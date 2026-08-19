"""
Queue a list of prompts into Google Flow and save each resulting image.

How a run goes:

    1. Chrome opens on Flow. The script does nothing yet.
    2. YOU log in and attach the character reference image by hand.
    3. You press Enter in the terminal. Now the script drives.
    4. For each scene: type the prompt, click generate, wait, save the image.

Steps 2 and 3 are not a limitation to be engineered away, they are the design.
Flow's @mention reference system only works in Agent mode, and Agent mode
paraphrases prompts, which wrecks style consistency. With Agent OFF and a
reference attached by hand, the reference sticks for the whole session, so the
script only ever has to type text and click a button.

Usage:
    python runner.py --inspect        # dump the DOM so you can fix config.py
    python runner.py                  # run every scene in scenes.txt
    python runner.py --only 3,7,12    # re-run just those scenes
"""

import argparse
import base64
import random
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

import config

# Pacing floors. config.py documents these as "do not lower"; this is where
# that is actually enforced, so a careless edit there cannot speed the run up.
DELAY_BETWEEN = max(config.DELAY_BETWEEN, 6.0)
DELAY_JITTER = max(config.DELAY_JITTER, 4.0)
TYPE_DELAY_MS = max(config.TYPE_DELAY_MS, 25)


# --- Scene list ------------------------------------------------------------

def load_scenes(path: Path) -> list[str]:
    """One prompt per line. Blank lines and # comments ignored."""
    if not path.exists():
        raise FileNotFoundError(f"No scenes file at {path}")
    scenes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            scenes.append(line)
    return scenes


def output_path(index: int, ext: str = ".png") -> Path:
    return config.OUTPUT_DIR / f"scene_{index:03}{ext}"


def existing_output(index: int) -> Path | None:
    """
    What resume checks. Globs the extension because we only learn the real
    format from the downloaded bytes, so scene 7 may be .jpg while scene 8
    is .png.
    """
    return next(config.OUTPUT_DIR.glob(f"scene_{index:03}.*"), None)


# --- Element lookup --------------------------------------------------------

def buttons_with_text(page, needle: str, exact: bool = False):
    """
    Find buttons by walking the DOM ourselves instead of using `:text-is()`.

    Playwright's text engine kept failing to match controls that --inspect had
    clearly listed (the Agent toggle among them), most likely over whitespace
    normalisation and its stricter visibility rules. Reading innerText directly
    is predictable, and lets a failure print what it DID see.
    """
    found = []
    for element in page.query_selector_all('button, [role="button"], a'):
        try:
            text = (element.evaluate("(e) => e.innerText") or "").strip()
        except Exception:
            continue
        if not text:
            continue
        hit = (text == needle) if exact else (needle.lower() in text.lower())
        if hit:
            found.append((element, text))
    return found


def first_button_with_text(page, needle: str, exact: bool = False):
    for element, _ in buttons_with_text(page, needle, exact):
        try:
            if element.is_visible():
                return element
        except Exception:
            continue
    # Fall back to an invisible-but-present match rather than giving up: some
    # Flow controls report as hidden yet still take a click.
    hits = buttons_with_text(page, needle, exact)
    return hits[0][0] if hits else None


def diagnose(page, label: str) -> None:
    """
    Dump what is actually on screen when something cannot be found.

    Exists because the alternative is another guess-and-rerun cycle. This puts
    the real state in the terminal at the moment of failure.
    """
    print(f"\n{'-' * 68}")
    print(f"DIAGNOSTIC: {label}")
    print(f"{'-' * 68}")

    debug_dir = config.ROOT_DIR / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    shot = debug_dir / f"{label.replace(' ', '_')[:40]}.png"
    try:
        page.screenshot(path=str(shot))
        print(f"screenshot -> debug/{shot.name}")
    except Exception:
        pass

    try:
        entries = page.evaluate("""() => {
          const out = [];
          for (const el of document.querySelectorAll(
                   'button, [role="button"], a, input')) {
            const t = (el.innerText || el.value || '').replace(/\\s+/g,' ').trim();
            const vis = !!(el.offsetWidth || el.offsetHeight
                           || el.getClientRects().length);
            if (!t && el.tagName !== 'INPUT') continue;
            out.push({
              tag: el.tagName.toLowerCase(),
              text: t.slice(0, 46),
              label: el.getAttribute('aria-label') || '',
              placeholder: el.getAttribute('placeholder') || '',
              vis: vis,
            });
          }
          return out.slice(0, 60);
        }""")
    except Exception:
        entries = []

    print(f"\n{len(entries)} clickable/among them:")
    for e in entries:
        mark = " " if e["vis"] else "H"
        extra = e["label"] or e["placeholder"]
        print(f"  [{mark}] {e['tag']:<7} {e['text']:<48}"
              f"{(' | ' + extra) if extra else ''}")

    try:
        dialogs = page.evaluate("""() => {
          const out = [];
          for (const d of document.querySelectorAll(
                   '[role="dialog"],[aria-modal="true"]')) {
            out.push((d.innerText || '').replace(/\\s+/g,' ').slice(0, 300));
          }
          return out;
        }""")
        if dialogs:
            print("\nopen dialog text:")
            for d in dialogs:
                print(f"  {d!r}")
        else:
            print("\nno [role=dialog] on the page (picker may use a plain div)")
    except Exception:
        pass
    print("-" * 68 + "\n")


def find_first(page, selectors: list[str], what: str, require_enabled: bool = False):
    """
    Return the first visible element matching any candidate selector.

    require_enabled matters for the submit button: Flow greys it out until the
    prompt box has content, and clicking a disabled button does nothing at all
    - the run would then just sit there until the generation timeout.
    """
    for selector in selectors:
        try:
            element = page.query_selector(selector)
        except Exception:
            continue                      # malformed selector, try the next
        if element:
            try:
                if element.is_visible() and (not require_enabled or element.is_enabled()):
                    return element
            except Exception:
                continue
    raise RuntimeError(
        f"Could not find the {what}. Tried: {selectors}\n"
        f"Run `python runner.py --inspect` and fix config.py."
    )


# --- Startup: wait for the app, settle Agent mode ---------------------------

def wait_until_ready(page) -> None:
    """
    Wait for the prompt box to exist.

    Doubles as the login wait. If the saved profile is still signed in this
    returns almost immediately; if not, you sign in during this window and the
    run continues on its own - no keypress, which is the whole point.
    """
    deadline = time.monotonic() + config.READY_TIMEOUT
    nudged = False

    while time.monotonic() < deadline:
        for selector in config.PROMPT_SELECTORS:
            try:
                if page.query_selector(selector):
                    return
            except Exception:
                pass
        if not nudged:
            print("[wait] prompt box not up yet. If you are signed out, sign in")
            print(f"[wait] now - the run resumes by itself (up to "
                  f"{config.READY_TIMEOUT:.0f}s).")
            nudged = True
        time.sleep(2.0)

    raise RuntimeError(
        f"Prompt box never appeared within {config.READY_TIMEOUT:.0f}s. Either "
        f"the login did not complete, or PROMPT_SELECTORS "
        f"({config.PROMPT_SELECTORS}) no longer match - run --inspect."
    )


_AGENT_STATE_JS = """
(el) => ({
  pressed: el.getAttribute('aria-pressed'),
  checked: el.getAttribute('aria-checked'),
  state: el.getAttribute('data-state'),
  cls: (el.className && typeof el.className === 'string') ? el.className : '',
})
"""


def _agent_is_on(info) -> bool | None:
    """True/False if the toggle state is readable, None if it is not."""
    for key in ("pressed", "checked"):
        if info[key] in ("true", "false"):
            return info[key] == "true"
    if info["state"] in ("on", "active", "checked", "open"):
        return True
    if info["state"] in ("off", "inactive", "unchecked", "closed"):
        return False
    return None


def ensure_agent_off(page) -> None:
    """
    Turn Agent mode off if it is on.

    Never clicks blind: an unreadable state gets a warning rather than a guess,
    because a wrong guess would switch Agent ON and quietly paraphrase every
    prompt in the run.
    """
    # The prompt bar renders after the prompt box, so poll instead of checking
    # once. A single early check reports "not found" on a page that has one.
    button = None
    deadline = time.monotonic() + config.AGENT_WAIT
    while button is None and time.monotonic() < deadline:
        button = first_button_with_text(page, "Agent", exact=True)
        if button is None:
            time.sleep(1.0)

    if button is None:
        print(f"[agent] toggle not found after {config.AGENT_WAIT:.0f}s")
        diagnose(page, "agent toggle not found")
        return

    state = _agent_is_on(button.evaluate(_AGENT_STATE_JS))
    if state is False:
        print("[agent] already off")
        return
    if state is None:
        print("[agent] cannot read the toggle state, leaving it alone.")
        print("[agent] Confirm it is OFF in the browser - if it is on, prompts")
        print("[agent] get paraphrased and the style will drift.")
        return

    print("[agent] on - turning it off")
    button.click()
    page.wait_for_timeout(1000)
    if _agent_is_on(button.evaluate(_AGENT_STATE_JS)) is not False:
        print("[agent] WARNING: it may still be on. Check the browser.")


def _model_chip(page):
    """
    The prompt-bar chip showing the current model.

    Filtered rather than "first visible match", because Flow's failure card
    quotes the model name back at you - "You've reached the daily limit for Nano
    Banana Pro generations" - and matches MODEL_CHIP_MARKER exactly as well as
    the chip does. Clicking the card opens no menu, so ensure_model reported
    switching, changed nothing, and the run kept generating on the spent model.

    The real chip is the one that also carries the aspect ratio and batch size.
    """
    import re as _re
    exclude = _re.compile(getattr(config, "CHIP_EXCLUDE_PATTERN", r"$^"), _re.I)
    markers = getattr(config, "MODEL_CHIP_SETTINGS_MARKERS", [])

    fallback = None
    for element, text in buttons_with_text(page, config.MODEL_CHIP_MARKER):
        try:
            if not element.is_visible():
                continue
        except Exception:
            continue
        flat = " ".join(text.split())
        if exclude.search(flat):
            continue
        if any(m in flat for m in markers):
            return element, text
        # Keep the first clean candidate in case Flow drops the settings from
        # the chip label one day. Better a guess than nothing.
        if fallback is None:
            fallback = (element, text)
    return fallback if fallback is not None else (None, "")


# Which rung of config.MODEL_LADDER the run is currently on. Module state
# rather than a parameter because every scene in a run shares it: once the top
# model is out of credits it stays out for the rest of the day, so re-trying it
# on the next scene would just burn another failed generation.
_LADDER_RUNG = 0


def current_model() -> tuple[str, list[str]]:
    """The (name, exclude) pair the run should be generating with right now."""
    if not config.MODEL_LADDER:
        return config.MODEL_NAME, config.MODEL_EXCLUDE
    rung = min(_LADDER_RUNG, len(config.MODEL_LADDER) - 1)
    name, exclude = config.MODEL_LADDER[rung]
    return name, list(exclude)


def demote_model(page) -> bool:
    """
    Drop to the next model down after the current one hits its daily limit.

    Returns False when there is nothing lower left, which is the only case that
    should end the run.
    """
    global _LADDER_RUNG
    if not config.MODEL_LADDER:
        return False
    if _LADDER_RUNG >= len(config.MODEL_LADDER) - 1:
        return False

    was, _ = current_model()
    _LADDER_RUNG += 1
    now, _ = current_model()
    print(f"[model] {was} is out for today, dropping to {now} "
          f"for the rest of this run")
    if not ensure_model(page):
        # Worth shouting about: the retry will run on whatever is still
        # selected, which is the model that just refused. Left silent, the run
        # walks down the entire ladder without ever changing model.
        print(f"[model] WARNING: could not select {now}. The next attempt runs "
              f"on whatever is selected, which may still be {was}.")
        print(f"[model] check the labels in config.MODEL_LADDER against the "
              f"chip text printed above.")
    return True


def _wanted(text: str) -> bool:
    """Does this label name the model we want, and not an excluded variant?"""
    name, exclude = current_model()
    if name.lower() not in text.lower():
        return False
    return not any(x.lower() in text.lower() for x in exclude)


def ensure_model(page) -> bool:
    """
    Switch Flow to the run's current model if it is not already selected.

    "Current" means the active rung of config.MODEL_LADDER, which starts at the
    best model and steps down as each one hits its daily limit.

    Substring matching alone cannot tell "Nano Banana 2" from "Nano Banana 2
    Lite", so an option has to contain MODEL_NAME and none of MODEL_EXCLUDE.
    Never fatal: a failure here prints what it saw and leaves the current model
    selected, because the wrong model still produces a usable image.
    """
    wanted_name, wanted_exclude = current_model()
    if not wanted_name:
        return True

    chip, text = _model_chip(page)
    if chip is None:
        print("[model] selector not found, leaving whatever is selected")
        return False

    current = " ".join(text.split())
    if _wanted(current):
        print(f"[model] already on {wanted_name}")
        return True

    print(f"[model] currently {current[:48]!r}, switching to {wanted_name}")
    try:
        chip.click()
    except Exception as exc:
        print(f"[model] could not open the menu ({type(exc).__name__})")
        return False

    def find_option():
        """A visible option naming the wanted model, excluding the chips."""
        for element, label in buttons_with_text(page, wanted_name):
            flat = " ".join(label.split())
            # Skip the chip and the submenu button - both carry the model name.
            if element == chip or not _wanted(flat):
                continue
            if config.MODEL_SUBMENU_MARKER in flat:
                continue
            try:
                if element.is_visible():
                    return element
            except Exception:
                continue
        return None

    def find_submenu():
        """The nested dropdown inside the settings panel, if it is there."""
        for element, label in buttons_with_text(page, config.MODEL_CHIP_MARKER):
            flat = " ".join(label.split())
            if element == chip or config.MODEL_SUBMENU_MARKER not in flat:
                continue
            try:
                if element.is_visible():
                    return element
            except Exception:
                continue
        return None

    deadline = time.monotonic() + config.MODEL_MENU_WAIT
    option = None
    opened_submenu = False
    while option is None and time.monotonic() < deadline:
        option = find_option()
        if option is not None:
            break
        # The list is one level deeper: the panel holds a dropdown showing the
        # current model, and the options only exist after clicking that.
        if not opened_submenu:
            submenu = find_submenu()
            if submenu is not None:
                print("[model] opening the nested model dropdown")
                try:
                    submenu.click()
                    opened_submenu = True
                    page.wait_for_timeout(900)
                    continue
                except Exception:
                    pass
        time.sleep(0.4)

    if option is None:
        print(f"[model] no option matching {wanted_name!r} without "
              f"{wanted_exclude}")
        diagnose(page, "model option not found")
        page.keyboard.press("Escape")
        return False

    option.click()
    page.wait_for_timeout(1200)
    _, after = _model_chip(page)
    if _wanted(" ".join(after.split())):
        print(f"[model] switched to {wanted_name}")
        return True
    print(f"[model] WARNING: chip still reads {' '.join(after.split())[:48]!r}")
    return False


# --- Reference image -------------------------------------------------------

def attach_reference(page) -> bool:
    """
    Get the character reference onto the prompt.

    Three distinct steps, and missing the last one is easy: uploading a file
    only files it in the media library. It is inert there. The asset must then
    be SELECTED and handed over with "Add to Prompt" before any generation is
    locked to it.

    Reuses an already-uploaded copy when one exists, so repeat runs do not fill
    the library with duplicates of the same character.
    """
    reference = config.REFERENCE_IMAGE
    if reference is None:
        print(f"[ref] no image found in {config.REFERENCE_DIR}")
        return False
    if not reference.exists():
        print(f"[ref] configured reference is missing: {reference}")
        return False

    if not _open_asset_picker(page):
        print("[ref] could not open the asset picker.")
        return False

    if _select_existing_asset(page):
        print(f"[ref] reusing existing {config.REFERENCE_ASSET_NAME!r} asset")
        if reference_attached(page):
            # Selecting attached it and closed the picker; there is no second
            # step to perform.
            print("[ref] attached to the prompt on selection")
            return True
    else:
        print(f"[ref] {config.REFERENCE_ASSET_NAME!r} not in the library, uploading")
        if not _upload_reference(page, reference):
            return False
        if not _select_existing_asset(page):
            print("[ref] uploaded, but the asset never appeared in the picker")
            return False

    return _click_add_to_prompt(page)


# Scans EVERY element, not just <button>, because Flow's picker footer may well
# be a styled div. Requires few children so it matches the control itself
# rather than a wrapper, then walks up to whatever is actually clickable.
_FIND_CLICKABLE_TEXT_JS = """
([needle, maxChildren]) => {
  const want = needle.toLowerCase();
  for (const el of document.querySelectorAll(
           'button, [role="button"], a, div, span, p')) {
    if (el.children.length > maxChildren) continue;
    const t = (el.innerText || '').replace(/\\s+/g, ' ').trim().toLowerCase();
    if (t !== want) continue;
    if (!(el.offsetWidth || el.offsetHeight || el.getClientRects().length))
      continue;
    let node = el;
    for (let i = 0; i < 5 && node; i++) {
      if (node.tagName === 'BUTTON' || node.getAttribute('role') === 'button'
          || node.tagName === 'A') return node;
      node = node.parentElement;
    }
    return el;
  }
  return null;
}
"""


def find_clickable_with_text(page, needle: str, max_children: int = 3):
    try:
        handle = page.evaluate_handle(_FIND_CLICKABLE_TEXT_JS,
                                      [needle, max_children])
        return handle.as_element()
    except Exception:
        return None


def _find_add_to_prompt(page):
    return (first_button_with_text(page, "Add to Prompt")
            or find_clickable_with_text(page, "Add to Prompt"))


def reference_attached(page) -> bool:
    """
    Is a reference chip sitting on the prompt right now?

    Clicking an asset can attach it outright and close the picker, which means
    "Add to Prompt" is gone precisely BECAUSE the job is done. Treating that
    absence as failure is what stopped a run that had actually succeeded.

    The chip carries a "cancel" ligature button (its remove X), and Flow only
    renders "Clear prompt" once the prompt holds something. Neither is present
    on an empty prompt bar, so together they are a reliable positive signal.
    """
    for text in config.ATTACHED_CHIP_TEXTS:
        if first_button_with_text(page, text, exact=True) is not None:
            return True
    return False


# There are TWO add buttons and they are not interchangeable:
#
#   - top right "Add Media": adds to the MEDIA LIBRARY. Uploading here files
#     the image away where the prompt cannot see it. This is what produced the
#     duplicate uploads and the "asset never appeared" failures.
#   - a small "+" in the prompt bar beside Agent: attaches a reference to THE
#     PROMPT. This is the one we want.
#
# Text cannot tell them apart, so anchor on the Agent toggle (unique, and its
# position is confirmed) and take the add-style button nearest to it.
_FIND_PROMPT_ADD_JS = """
([agentText, ligatures]) => {
  const clickable = [...document.querySelectorAll('button, [role="button"]')];
  const agent = clickable.find(
    b => (b.innerText || '').trim() === agentText);
  if (!agent) return null;

  const a = agent.getBoundingClientRect();
  const centre = (r) => [r.left + r.width / 2, r.top + r.height / 2];
  const [ax, ay] = centre(a);

  let best = null, bestDist = Infinity;
  for (const b of clickable) {
    if (b === agent) continue;
    const text = (b.innerText || '').trim().toLowerCase();
    const label = (b.getAttribute('aria-label') || '').toLowerCase();
    // Match the FIRST TOKEN, not the whole string. These controls render as a
    // Material Symbols ligature followed by a word, so the prompt bar's plus
    // reads "add_2 Create" - testing the full text rejected the exact button
    // we were looking for.
    const firstToken = text.split(/\\s+/)[0];
    const isAdd = ligatures.includes(firstToken) || text === ''
                  || /add|attach|reference/.test(label);
    if (!isAdd) continue;

    const r = b.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    // Same row as the prompt bar: a control far above it is the library one.
    if (Math.abs(centre(r)[1] - ay) > 80) continue;

    const [bx, by] = centre(r);
    const dist = Math.hypot(bx - ax, by - ay);
    if (dist < bestDist) { bestDist = dist; best = b; }
  }
  return best;
}
"""


def find_prompt_add_button(page):
    """The + in the prompt bar, identified by sitting next to Agent."""
    try:
        handle = page.evaluate_handle(
            _FIND_PROMPT_ADD_JS,
            ["Agent", ["add", "add_2", "+", "attach_file",
                       "add_photo_alternate", "add_circle"]],
        )
        return handle.as_element()
    except Exception:
        return None


def _open_asset_picker(page) -> bool:
    """The picker may already be open; only click a trigger if it is not."""
    if _find_add_to_prompt(page):
        print("[ref] asset picker already open")
        return True

    # Deliberately NOT "Add Media": that is the library button in the top right
    # and using it is what filed the reference somewhere the prompt could not
    # see it. We want the + in the prompt bar, found by proximity to Agent.
    trigger = find_prompt_add_button(page)
    if trigger is None:
        print("[ref] could not find the + button in the prompt bar")
        print("[ref] (looked for an add-style control next to the Agent toggle)")
        diagnose(page, "prompt bar add button not found")
        return False

    print("[ref] opening reference picker via the prompt bar +")
    trigger.click()

    # The picker's contents load asynchronously, so poll rather than assume a
    # fixed wait is long enough.
    deadline = time.monotonic() + config.PICKER_WAIT
    while time.monotonic() < deadline:
        if _find_add_to_prompt(page) or _find_file_input(page):
            return True
        time.sleep(0.5)

    print(f"[ref] picker did not open within {config.PICKER_WAIT:.0f}s")
    diagnose(page, "asset picker did not open")
    return False


def _select_existing_asset(page) -> bool:
    """Find the reference in the library by display name and click it."""
    name = config.REFERENCE_ASSET_NAME

    # Narrow the list first so the name match cannot land on some other asset.
    for selector in config.ASSET_SEARCH_SELECTORS:
        try:
            box = page.query_selector(selector)
            if box and box.is_visible():
                box.click()
                page.keyboard.press("ControlOrMeta+a")
                box.type(name, delay=TYPE_DELAY_MS)
                page.wait_for_timeout(1500)
                break
        except Exception:
            continue

    # Asset rows are not buttons, so scan any element whose own text is the
    # asset name, then click the nearest clickable ancestor.
    deadline = time.monotonic() + config.ASSET_WAIT
    while time.monotonic() < deadline:
        handle = page.evaluate_handle(
            """(name) => {
              for (const el of document.querySelectorAll('div,span,p,li')) {
                if (el.children.length > 2) continue;
                const t = (el.innerText || '').trim();
                if (t.toLowerCase() !== name.toLowerCase()) continue;
                let node = el;
                for (let i = 0; i < 6 && node; i++) {
                  if (node.getAttribute('role') === 'button'
                      || node.tagName === 'BUTTON'
                      || node.onclick) return node;
                  node = node.parentElement;
                }
                return el;
              }
              return null;
            }""",
            name,
        )
        element = handle.as_element()
        if element is not None:
            try:
                element.click(timeout=5000)
                page.wait_for_timeout(1000)
                return True
            except Exception:
                pass
        time.sleep(0.5)

    return False


def _upload_reference(page, reference: Path) -> bool:
    file_input = _find_file_input(page)
    if file_input is None:
        print('[ref] no <input type="file"> found to upload into')
        return False

    print(f"[ref] uploading {reference.name} "
          f"({reference.stat().st_size // 1024} KB)")
    file_input.set_input_files(str(reference))
    print(f"[ref] waiting {config.REFERENCE_SETTLE:.0f}s for Flow to ingest it")
    page.wait_for_timeout(int(config.REFERENCE_SETTLE * 1000))
    return True


def _click_add_to_prompt(page) -> bool:
    # Poll: the control commonly mounts or enables only once an asset is
    # actually selected, so a single immediate check is too early.
    button = None
    deadline = time.monotonic() + config.PICKER_WAIT
    while button is None and time.monotonic() < deadline:
        if reference_attached(page):
            print("[ref] already attached to the prompt")
            return True
        button = _find_add_to_prompt(page)
        if button is None:
            time.sleep(0.5)

    if button is None:
        print('[ref] no "Add to Prompt" control found after '
              f"{config.PICKER_WAIT:.0f}s - the reference would sit in the")
        print("[ref] library unattached, so stopping here.")
        diagnose(page, "add to prompt not found")
        return False

    button.click()
    page.wait_for_timeout(2000)
    print("[ref] added to prompt")

    if not reference_attached(page):
        print("[ref] WARNING: no reference chip on the prompt afterwards.")
        print("[ref] Generations may come out off-model - check the browser.")
    return True


def _find_file_input(page):
    """First file input on the page, hidden or not."""
    for selector in config.FILE_INPUT_SELECTORS:
        try:
            element = page.query_selector(selector)
        except Exception:
            continue
        if element:
            return element
    return None


# --- Inspect mode (task 1) -------------------------------------------------

# Builds a reasonably stable CSS selector for one element, preferring the
# attributes that survive a redeploy (testid, aria-label, id) over class names,
# which in Flow are almost certainly hashed build output.
_SELECTOR_JS = """
(el) => {
  const esc = (s) => (window.CSS && CSS.escape ? CSS.escape(s) : s);
  for (const attr of ['data-testid', 'data-test-id', 'aria-label', 'name']) {
    const v = el.getAttribute(attr);
    if (v) return `${el.tagName.toLowerCase()}[${attr}="${v}"]`;
  }
  if (el.id) return `#${esc(el.id)}`;
  const cls = (el.className && typeof el.className === 'string')
    ? el.className.trim().split(/\\s+/).filter(c => c.length < 25).slice(0, 2)
    : [];
  if (cls.length) return el.tagName.toLowerCase() + '.' + cls.map(esc).join('.');
  return el.tagName.toLowerCase();
}
"""

_DESCRIBE_JS = """
(el) => ({
  tag: el.tagName.toLowerCase(),
  type: el.getAttribute('type') || '',
  role: el.getAttribute('role') || '',
  label: el.getAttribute('aria-label') || '',
  placeholder: el.getAttribute('placeholder') || '',
  testid: el.getAttribute('data-testid') || '',
  text: (el.innerText || el.value || '').trim().slice(0, 60),
  visible: !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length),
})
"""

# For each image, walk up the tree and report the nearest ancestor that has a
# stable-looking hook. That ancestor is your RESULT_IMAGE_SELECTOR scope.
_IMAGE_JS = """
(el) => {
  let container = '';
  let node = el.parentElement;
  let depth = 0;
  while (node && depth < 8) {
    for (const attr of ['data-testid', 'data-test-id', 'id', 'role']) {
      const v = node.getAttribute(attr);
      if (v && !container) {
        container = attr === 'id' ? `#${v}` : `${node.tagName.toLowerCase()}[${attr}="${v}"]`;
      }
    }
    if (container) break;
    node = node.parentElement;
    depth++;
  }
  return {
    src: (el.currentSrc || el.src || '').slice(0, 110),
    w: el.naturalWidth,
    h: el.naturalHeight,
    alt: (el.getAttribute('alt') || '').slice(0, 40),
    container: container || '(no stable ancestor found)',
  };
}
"""


def inspect_page(page):
    """Dump every input and button so you can write real selectors."""
    print("\n" + "=" * 72)
    print("EDITABLE ELEMENTS  ->  candidates for PROMPT_SELECTORS")
    print("=" * 72)
    editable = page.query_selector_all(
        'textarea, input, [contenteditable="true"], [role="textbox"]'
    )
    if not editable:
        print("  (none found - is the page fully loaded?)")
    for element in editable:
        info = element.evaluate(_DESCRIBE_JS)
        if not info["visible"]:
            continue
        print(f"\n  selector : {element.evaluate(_SELECTOR_JS)}")
        print(f"  tag      : {info['tag']}  type={info['type']}  role={info['role']}")
        if info["placeholder"]:
            print(f"  placeholder: {info['placeholder']}")
        if info["label"]:
            print(f"  aria-label : {info['label']}")
        if info["testid"]:
            print(f"  testid     : {info['testid']}")

    print("\n" + "=" * 72)
    print("FILE INPUTS  ->  where the reference gets uploaded")
    print("=" * 72)
    print("Hidden ones are listed too - set_input_files() works on those, so a")
    print("hidden input is normal and fine.\n")
    file_inputs = page.query_selector_all('input[type="file"]')
    if not file_inputs:
        print("  (none on the page - the widget probably mounts its input only")
        print("   after you click an upload button. Check UPLOAD_TRIGGER_SELECTORS.)")
    for element in file_inputs:
        info = element.evaluate(_DESCRIBE_JS)
        accept = element.get_attribute("accept") or "(any)"
        state = "visible" if info["visible"] else "hidden "
        print(f"  [{state}] accept={accept:<28} {element.evaluate(_SELECTOR_JS)}")

    print("\n" + "=" * 72)
    print("DIALOGS / OVERLAYS  ->  the asset picker, when it is open")
    print("=" * 72)
    dialogs = page.query_selector_all('[role="dialog"], [aria-modal="true"]')
    if not dialogs:
        print("  (no dialog open - reopen the asset picker and dump again)")
    for i, dialog in enumerate(dialogs, 1):
        print(f"\n  --- dialog {i}: {dialog.evaluate(_SELECTOR_JS)}")
        for element in dialog.query_selector_all('button, [role="button"], input'):
            info = element.evaluate(_DESCRIBE_JS)
            if not info["visible"] and info["tag"] != "input":
                continue
            label = (info["label"] or info["text"] or info["placeholder"]
                     or "(no label)").replace("\n", " ")
            print(f"      {label[:40]:<42} {element.evaluate(_SELECTOR_JS)}")

    print("\n" + "=" * 72)
    print("BUTTONS  ->  SUBMIT_SELECTORS, the Agent toggle, the picker trigger")
    print("=" * 72)
    for element in page.query_selector_all('button, [role="button"]'):
        info = element.evaluate(_DESCRIBE_JS)
        if not info["visible"]:
            continue
        label = (info["label"] or info["text"] or "").replace("\n", " ")
        line = f"  {label[:40]:<42} {element.evaluate(_SELECTOR_JS)}"
        if not label:
            # Icon-only button: the markup is the only way to tell them apart,
            # and one of these is almost certainly the asset-picker trigger.
            markup = element.evaluate(
                "(el) => el.innerHTML.replace(/\\s+/g,' ').slice(0, 70)")
            line += f"\n      markup: {markup}"
        print(line)
        for attr in ("aria-pressed", "data-state", "aria-checked"):
            value = element.get_attribute(attr)
            if value is not None:
                print(f"      {attr}={value!r}   <- toggle state, useful for Agent")

    print("\n" + "=" * 72)
    print("IMAGES  ->  pick a container for RESULT_IMAGE_SELECTOR")
    print("=" * 72)
    print("Generate one image by hand first, then compare: the big one is a")
    print("result, the small ones are avatars and icons you must exclude.\n")
    for element in page.query_selector_all("img"):
        info = element.evaluate(_IMAGE_JS)
        flag = "RESULT?" if info["w"] >= config.MIN_RESULT_WIDTH else "icon   "
        print(f"  [{flag}] {info['w']}x{info['h']}  {info['container']}")
        print(f"            src: {info['src']}")

    print("\n" + "=" * 72)
    print("Copy the right selectors into config.py, then run without --inspect.")
    print("=" * 72 + "\n")


# --- Typing (task 2) -------------------------------------------------------

_READ_BACK_JS = "(el) => el.value !== undefined ? el.value : el.innerText"


def _clear_prompt(page, element) -> None:
    """
    Empty the prompt TEXT, leaving the attached reference alone.

    Do NOT use Flow's "Clear prompt" button here. It clears the whole prompt
    INCLUDING the reference chip, so every scene after the first would generate
    with no reference at all and quietly come out off-model. Select-all +
    Delete inside the text box only touches the text.
    """
    try:
        if not (element.evaluate(_READ_BACK_JS) or "").strip():
            return                        # already empty, nothing to undo
        element.click()
        page.keyboard.press("ControlOrMeta+a")
        page.keyboard.press("Delete")
        page.wait_for_timeout(200)
    except Exception:
        pass


def fill_prompt(page, element, text: str) -> None:
    """
    Get the prompt into the box and confirm it actually landed.

    React ignores a directly assigned .value, so every path here has to go
    through a real input event. Order depends on config.PASTE_PROMPT; whichever
    runs first, the read-back below decides whether it worked, and the other
    method is tried rather than silently submitting an empty prompt.

    insert_text goes through CDP Input.insertText, which is how a paste or an
    IME commits text: one proper input event, no per-character keystrokes.
    fill() is last because it is the most likely of the three to be ignored by
    a controlled component.
    """
    # Playwright's default action timeout is far shorter than a long prompt
    # takes to type: 1529 chars x 55ms is ~84s, which blew past it every time
    # and silently dropped us onto the next method. So the budget has to scale
    # with the text whenever typing is the path being used.
    type_timeout = len(text) * TYPE_DELAY_MS + 30_000

    paste = ("insert_text", lambda: page.keyboard.insert_text(text))
    typing = ("type", lambda: element.type(text, delay=TYPE_DELAY_MS,
                                           timeout=type_timeout))

    attempts = [paste, typing] if config.PASTE_PROMPT else [typing, paste]
    attempts.append(("fill", lambda: element.fill(text)))

    for name, action in attempts:
        try:
            _clear_prompt(page, element)
            element.click()
            action()
        except Exception as exc:
            print(f"    [type] {name} raised {type(exc).__name__}, trying next")
            continue

        landed = (element.evaluate(_READ_BACK_JS) or "").strip()
        if landed.startswith(text[:40].strip()):
            # Only worth a line when the intended method failed and something
            # else picked it up - that is a selector problem starting to show.
            if name != attempts[0][0]:
                print(f"    [type] fell back to {name}()")
            return
        print(f"    [type] {name}() did not stick (read back {landed[:30]!r})")

    raise RuntimeError(
        "Could not get text into the prompt box with type(), fill(), or "
        "insert_text(). The PROMPT_SELECTORS match is probably the wrong "
        "element - re-run --inspect."
    )


# --- Completion detection (task 3) -----------------------------------------

# Flow's own media UUID, from the `name` query param on the result URL.
#
# An earlier version stamped a data-attribute on each seen <img> instead. That
# was wrong: React owns those nodes and destroys them on re-render (which a
# rejected prompt triggers), so every old image came back looking brand new and
# the runner happily saved one. The UUID lives in the src Flow itself wrote, so
# no amount of re-rendering, reordering, or lazy-loading can disguise an old
# image as a fresh one.
_IDENTIFY_JS = """
(el) => {
  const src = el.currentSrc || el.src || '';
  const m = src.match(/[?&]name=([^&]+)/);
  return {
    id: m ? m[1] : src,
    src: src,
    ready: el.complete && el.naturalWidth > 0,
    width: el.naturalWidth,
  };
}
"""


def _all_images(page):
    """Every image matching the result selector, loaded or not."""
    out = []
    for element in page.query_selector_all(config.RESULT_IMAGE_SELECTOR):
        try:
            out.append((element, element.evaluate(_IDENTIFY_JS)))
        except Exception:
            continue                      # node detached mid-poll
    return out


# Every media UUID this run has ever laid eyes on, plus every one it has saved.
#
# A per-scene DOM snapshot is not enough on its own. Flow's result grid drops
# off-screen nodes and re-renders them later, so an image from an EARLIER VIDEO
# can appear mid-wait, be absent from this scene's baseline, and look brand new.
# That is how a run once saved the previous video's scene 45 as this video's
# scene 7, and saved one generation twice under two different scene numbers.
# Neither failure shows up anywhere except in the finished video.
_SEEN_IDS: set[str] = set()


def snapshot_ids(page) -> set[str]:
    """
    Every media UUID this run knows about: on the page now, or seen earlier.

    Deliberately does NOT filter on `ready`: an image still lazy-loading
    already carries its final src, and skipping it here would let it show up
    later looking like our generation.
    """
    _SEEN_IDS.update(info["id"] for _, info in _all_images(page))
    return set(_SEEN_IDS)


def wait_for_new_image(page, baseline_ids: set[str], baseline_rejections: int = 0,
                       baseline_quota: tuple[int, int] = (0, 0)):
    """
    Block until an image Flow did not have before appears, then return it.

    The invariant that makes this safe: an image whose UUID was in the baseline
    can never be returned, so a failed or rejected generation times out rather
    than silently saving something old.
    """
    deadline = time.monotonic() + config.GENERATION_TIMEOUT
    last_count = -1
    stable = 0

    while time.monotonic() < deadline:
        time.sleep(config.POLL_INTERVAL)
        check_for_challenge(page)
        check_for_quota(page, baseline_quota)
        check_for_rejection(page, baseline_rejections)

        # Flow renders each result twice (grid tile + preview pane), both with
        # the same media UUID, so dedupe by id. Without this a single normal
        # generation looks like two and trips the batch warning below.
        seen_ids = set()
        fresh = []
        for element, info in _all_images(page):
            if (info["id"] in baseline_ids or info["id"] in seen_ids
                    or not info["ready"]
                    or info["width"] < config.MIN_RESULT_WIDTH):
                continue
            seen_ids.add(info["id"])
            fresh.append((element, info))

        # Settling guard: wait for the count to stop moving so we do not grab a
        # half-rendered result the instant it appears.
        if len(fresh) == last_count:
            stable += 1
        else:
            stable = 0
            last_count = len(fresh)

        if fresh and stable >= config.STABLE_POLLS:
            if len(fresh) > 1:
                # Flow is set to x1, so this should not happen. If it does, the
                # model bar was bumped to x2/x4 and "which one is the newest"
                # stops being answerable from DOM order alone.
                print(f"    [warn] {len(fresh)} new images at once, taking the last")
            element, info = fresh[-1]
            return element, info["src"], info["id"]

    raise TimeoutError(
        f"No new image after {config.GENERATION_TIMEOUT:.0f}s. The generation "
        f"probably failed silently, or RESULT_IMAGE_SELECTOR "
        f"({config.RESULT_IMAGE_SELECTOR!r}) has stopped matching."
    )


def dump_diagnostics(page, index: int) -> None:
    """
    On a timeout, capture what was on screen.

    The point is REJECTION_PATTERN: if Flow refused the prompt in wording the
    pattern does not cover, the run times out silently and we learn nothing.
    This puts the actual short-text elements in front of you so the pattern can
    be corrected instead of guessed at again.
    """
    debug_dir = config.ROOT_DIR / "debug"
    debug_dir.mkdir(parents=True, exist_ok=True)
    shot = debug_dir / f"scene_{index:03}_timeout.png"
    try:
        page.screenshot(path=str(shot))
        print(f"    [debug] screenshot -> {shot.relative_to(config.ROOT_DIR)}")
    except Exception:
        pass

    try:
        texts = page.evaluate(
            """(maxChars) => {
              const seen = [];
              for (const el of document.querySelectorAll(
                       '[role="alert"],[role="status"],[aria-live]')) {
                const t = (el.innerText || '').trim().replace(/\\s+/g, ' ');
                if (t && t.length <= maxChars && !seen.includes(t)) seen.push(t);
              }
              return seen;
            }""",
            config.REJECTION_MAX_CHARS,
        )
    except Exception:
        texts = []

    if texts:
        print("    [debug] live-region text on screen (candidate error wording):")
        for t in texts:
            print(f"            {t[:160]!r}")
    else:
        print("    [debug] no alert/status/aria-live text found on the page")


class PromptRejected(RuntimeError):
    """Flow refused the prompt. Retrying verbatim will not help."""


class ChallengeUnsolved(RuntimeError):
    """A CAPTCHA appeared and nobody cleared it in time."""


class SceneUnrecoverable(RuntimeError):
    """Both the primary and the fallback description were refused."""


class QuotaExhausted(RuntimeError):
    """Out of daily credits. Every remaining scene would fail the same way."""


class ModelQuotaExhausted(RuntimeError):
    """
    THIS model is out for the day, but the others are not.

    Recoverable, unlike QuotaExhausted: drop a rung on config.MODEL_LADDER and
    the same scene generates fine on a lesser model.
    """


# Runs the match in-page against individual small elements, rather than letting
# Playwright's text= engine walk up to a container. `children.length <= 3` and
# the length cap are what keep a footer link from turning the whole page into a
# match.
_FIND_REJECTION_JS = """
([scopes, pattern, maxChars, maxChildren]) => {
  const re = new RegExp(pattern, 'i');
  const hits = [];
  for (const el of document.querySelectorAll(scopes)) {
    // Near-leaf nodes, so one banner counts once instead of once per ancestor
    // that happens to contain the same text. Not strictly leaves: Flow's policy
    // refusal wraps "policies" in a link, which put the sentence one level up.
    if (el.children.length > maxChildren) continue;
    if (!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)) continue;
    const t = (el.innerText || '').trim();
    if (!t || t.length > maxChars) continue;
    if (re.test(t)) hits.push(t.replace(/\\s+/g, ' '));
  }
  return hits;
}
"""


def find_rejections(page) -> list[str]:
    """
    Every rejection banner currently on screen.

    A LIST, not the first hit, because Flow leaves the failed-generation card
    on the page. Without counting, the next scene submits, immediately sees the
    previous scene's leftover warning, and is falsely reported as rejected -
    which cascades through the whole rest of the batch.
    """
    try:
        return page.evaluate(
            _FIND_REJECTION_JS,
            [config.REJECTION_SCOPES, config.REJECTION_PATTERN,
             config.REJECTION_MAX_CHARS,
             getattr(config, "REJECTION_MAX_CHILDREN", 0)],
        ) or []
    except Exception:
        return []                         # navigation mid-poll, try again later


def _quota_hits(page) -> tuple[list, list]:
    """(model-specific, account-wide) quota notices currently on the page."""
    def hits_for(pattern: str) -> list:
        if not pattern:
            return []
        try:
            return page.evaluate(
                _FIND_REJECTION_JS,
                [config.REJECTION_SCOPES, pattern, config.REJECTION_MAX_CHARS,
                 getattr(config, "REJECTION_MAX_CHILDREN", 0)],
            ) or []
        except Exception:
            return []

    return (hits_for(getattr(config, "MODEL_QUOTA_PATTERN", "")),
            hits_for(config.QUOTA_PATTERN))


def quota_baseline(page) -> tuple[int, int]:
    """
    How many quota notices are already on screen before submitting.

    Flow leaves failed cards up, so without this the SAME spent-model card is
    re-read on every subsequent attempt. That is what burned the whole model
    ladder inside one scene: each retry saw the original Pro error, demoted
    again, and never actually left Pro.
    """
    model_hits, hits = _quota_hits(page)
    return len(model_hits), len(hits)


def check_for_quota(page, baseline: tuple[int, int] = (0, 0)) -> None:
    """
    Raise when a quota notice appeared that was not there before submitting.

    Two outcomes, deliberately different: one model being spent is recoverable
    by dropping down the ladder, whereas the account being out of credits means
    every remaining scene fails identically and the run should stop rather than
    burn the full generation timeout on each one.
    """
    model_hits, hits = _quota_hits(page)

    # Checked first, and deliberately: Flow's per-model message contains the
    # words "daily limit", so QUOTA_PATTERN matches it too. Testing the broad
    # pattern first would abort a run that only needed to change model.
    #
    # Matched by MODEL NAME rather than by counting. Counting looked sufficient
    # and is not: Flow's result grid reflows as images are added, so a card that
    # scrolled out of view comes back and pushes the count above its baseline
    # with no new failure at all. That is how a run already down on Lite read a
    # leftover "daily limit for Nano Banana Pro" and demoted off the end of the
    # ladder. A notice only counts if it names the model we are generating with.
    fresh = [h for h in model_hits if _wanted(h)]
    if fresh and len(model_hits) > baseline[0]:
        raise ModelQuotaExhausted(fresh[-1][:160])
    if model_hits and not fresh:
        name, _ = current_model()
        print(f"    [limit] ignoring a stale notice that does not name "
              f"{name}")

    if len(hits) > baseline[1]:
        raise QuotaExhausted(hits[-1][:160])


def check_for_rejection(page, baseline: int = 0) -> None:
    """
    Fail fast when Flow rejects a prompt on policy grounds.

    Without this the scene still fails safely (no new UUID ever appears, so
    nothing gets saved) but only after burning the full generation timeout.
    Since these come up regularly, that is a lot of dead time over 30 scenes.

    Only ever call this AFTER submitting, and pass the count that was on screen
    BEFORE submitting: Flow leaves failed cards up, so only an INCREASE means
    this scene was rejected rather than a previous one.
    """
    current = find_rejections(page)
    if len(current) > baseline:
        raise PromptRejected(current[-1][:160])


# --- Saving (task 4) -------------------------------------------------------

_BLOB_TO_B64_JS = """
async (url) => {
  const res = await fetch(url);
  const buf = await res.arrayBuffer();
  let bin = '';
  const bytes = new Uint8Array(buf);
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}
"""


# Flow serves JPEG, not PNG, whatever the brief assumed. Name files after what
# is actually in them - a .png holding JFIF bytes trips up anything that trusts
# the extension instead of sniffing. Re-encoding to real PNG was the other
# option and is worse: several times the size, and the JPEG artifacts are
# already baked in so no quality comes back.
_MAGIC = [
    (b"\x89PNG\r\n\x1a\n", ".png"),
    (b"\xff\xd8\xff", ".jpg"),
    (b"GIF8", ".gif"),
]


def sniff_extension(data: bytes) -> str:
    for magic, ext in _MAGIC:
        if data.startswith(magic):
            return ext
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    print("    [save] unrecognised image format, defaulting to .png")
    return ".png"


def save_image(page, element, src: str, index: int) -> Path:
    """
    Get the bytes to disk and return the path actually written.

    Flow may hand back a data: URI, a blob: URL, or a signed https URL, and
    each needs a different route. The last resort is a screenshot of the
    element itself, which always works but re-encodes the image.
    """
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scheme = urlparse(src).scheme
    data = None

    if scheme == "data" and "," in src:
        data = base64.b64decode(src.split(",", 1)[1])

    # blob: is same-origin to the page, so only in-page fetch can read it.
    elif scheme == "blob":
        data = base64.b64decode(page.evaluate(_BLOB_TO_B64_JS, src))

    elif scheme in ("http", "https"):
        try:
            # Goes through the browser context, so session cookies and any
            # signed-URL auth come along for free. Also follows the
            # getMediaUrlRedirect hop to wherever the bytes actually live.
            response = page.request.get(src)
            if response.ok:
                data = response.body()
            else:
                print(f"    [save] direct fetch returned HTTP {response.status}")
        except Exception as exc:
            print(f"    [save] direct fetch failed ({type(exc).__name__})")

    if data is not None:
        dest = config.OUTPUT_DIR / f"scene_{index:03}{sniff_extension(data)}"
        dest.write_bytes(data)
        return dest

    dest = config.OUTPUT_DIR / f"scene_{index:03}.png"
    if _save_via_download_button(page, element, dest):
        return dest

    print("    [save] falling back to element screenshot")
    element.screenshot(path=str(dest))
    return dest


def _save_via_download_button(page, element, dest: Path) -> bool:
    """Click Flow's own download control for this image. Fallback path."""
    try:
        element.hover()
    except Exception:
        return False

    for selector in config.DOWNLOAD_BUTTON_SELECTORS:
        try:
            button = page.query_selector(selector)
            if not button or not button.is_visible():
                continue
            with page.expect_download(timeout=30_000) as info:
                button.click()
            info.value.save_as(str(dest))
            print("    [save] used Flow's download button")
            return True
        except Exception:
            continue
    return False


# --- Challenge handling ----------------------------------------------------

def _challenge_visible(page) -> bool:
    for selector in config.CHALLENGE_SELECTORS:
        try:
            element = page.query_selector(selector)
        except Exception:
            continue
        if element and element.is_visible():
            return True
    return False


def check_for_challenge(page) -> None:
    """
    Wait for a human to clear a CAPTCHA. We never solve these ourselves.

    Polls rather than asking for a keypress: if you are at the keyboard,
    solving it in the browser just resumes the run with nothing to press. If
    nobody is there, it gives up after CHALLENGE_WAIT and the run exits
    cleanly, so an overnight batch cannot sit frozen holding the Mac awake.
    """
    if not _challenge_visible(page):
        return

    print("\n" + "!" * 72)
    print("A CAPTCHA or challenge appeared. Solve it in the browser window.")
    print(f"The run resumes by itself once it clears "
          f"(waiting up to {config.CHALLENGE_WAIT / 60:.0f} min).")
    print("!" * 72)

    deadline = time.monotonic() + config.CHALLENGE_WAIT
    while time.monotonic() < deadline:
        time.sleep(3.0)
        if not _challenge_visible(page):
            print("[challenge] cleared, carrying on\n")
            return

    raise ChallengeUnsolved(
        f"CAPTCHA not cleared within {config.CHALLENGE_WAIT / 60:.0f} minutes"
    )


# --- Per-scene driver ------------------------------------------------------

def _attempt(page, index: int, prompt: str) -> None:
    check_for_challenge(page)

    # Self-healing: whatever knocks the reference off - clearing, a stray
    # click, Flow resetting the bar - put it back before typing. Generating
    # without it produces off-model images that look fine until you compare
    # them, which is the worst kind of failure to find later.
    if not reference_attached(page):
        print("    [ref] reference not on the prompt, re-attaching")
        if not attach_reference(page):
            raise RuntimeError(
                "Reference is detached and could not be re-attached. Refusing "
                "to generate off-model."
            )

    # No rejection check here on purpose: before submitting, anything on screen
    # belongs to the previous scene, and treating it as this scene's failure
    # kills a scene that was never even attempted.
    baseline_ids = snapshot_ids(page)
    print(f"    [base] {len(baseline_ids)} existing image(s) on page")

    box = find_first(page, config.PROMPT_SELECTORS, "prompt box")
    fill_prompt(page, box, prompt)

    # Count the failed cards already on screen, so a leftover from the previous
    # scene cannot be mistaken for this one being rejected. Quota notices need
    # the same treatment for the same reason - and more urgently, because a
    # re-read spent-model card demotes down the whole ladder without ever
    # leaving the model that is already out.
    baseline_rejections = len(find_rejections(page))
    baseline_quota = quota_baseline(page)

    submit = find_first(page, config.SUBMIT_SELECTORS, "submit button",
                        require_enabled=True)
    submit.click()
    print("    [wait] generating...")
    started = time.monotonic()

    try:
        element, src, media_id = wait_for_new_image(
            page, baseline_ids, baseline_rejections, baseline_quota)
    except TimeoutError:
        dump_diagnostics(page, index)
        raise

    # Belt and braces. wait_for_new_image already guarantees this, but saving
    # the wrong image is the one failure that is invisible in the output, so it
    # is worth a second assertion right before the bytes hit disk.
    if media_id in baseline_ids:
        raise RuntimeError(f"Refusing to save pre-existing image {media_id}")

    dest = save_image(page, element, src, index)
    # Timed so a model change (Lite vs full) can be compared with real numbers
    # rather than guessed at. Typing dominates wall clock; this is the part a
    # model swap actually changes.
    print(f"    [done] -> {dest.name}  ({dest.stat().st_size // 1024} KB, "
          f"{time.monotonic() - started:.0f}s to generate)")


def run_scene(page, index: int, prompt: str, alt: str | None = None) -> None:
    """
    Generate one scene, falling back to an alternate description if Flow
    refuses the first.

    Retrying the SAME text is pointless - the policy filter gives identical
    wording identical treatment. The alternate is a milder description of the
    same moment, written by the script author for exactly this. If both are
    refused the run stops: a missing scene means an incomplete video, and
    pushing on just spends credits on a batch you cannot use anyway.
    """
    print(f"\n[scene {index:03}] {prompt[:64]}{'...' if len(prompt) > 64 else ''}")
    try:
        _attempt_on_best_model(page, index, prompt)
        return
    except PromptRejected as exc:
        print(f"    [REJECTED] {exc}")
        if not alt:
            raise SceneUnrecoverable(
                f"scene {index} was refused and has no fallback description"
            ) from exc

    print("    [retry] trying the fallback description")
    print(f"    [scene {index:03}] {alt[:64]}{'...' if len(alt) > 64 else ''}")
    try:
        _attempt_on_best_model(page, index, alt)
    except PromptRejected as exc:
        raise SceneUnrecoverable(
            f"scene {index}: both descriptions were refused - {exc}"
        ) from exc


def _attempt_on_best_model(page, index: int, text: str) -> None:
    """
    Generate one scene, stepping down config.MODEL_LADDER as models run dry.

    Separate from the rejection fallback in run_scene because the two failures
    need opposite responses: a policy rejection means change the WORDS and keep
    the model, a spent daily limit means keep the words and change the MODEL.
    Mixing them would spend the alternate description on a problem it cannot
    fix, leaving the scene with no fallback left when it hits a real refusal.
    """
    while True:
        try:
            _attempt(page, index, text)
            return
        except ModelQuotaExhausted as exc:
            print(f"    [limit] {exc}")
            if not demote_model(page):
                raise QuotaExhausted(
                    "every model on the ladder has hit its daily limit"
                ) from exc
            print("    [retry] same prompt, one model down")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--inspect", action="store_true",
                        help="dump the DOM to help you fix config.py, then exit")
    parser.add_argument("--only",
                        help="comma-separated scene numbers to run, e.g. 3,7,12")
    parser.add_argument("--scenes", type=Path, default=config.SCENES_FILE)
    parser.add_argument("--alt-scenes", type=Path,
                        help="fallback descriptions, one per line, matching "
                             "scenes.txt line for line. Used only when Flow "
                             "refuses the primary description.")
    parser.add_argument("--output", type=Path,
                        help="where to write scene_NNN.* (default: "
                             "flow_runner/output). pipeline.py points this at "
                             "the run folder so images land with the script.")
    args = parser.parse_args()

    # Rebinding the config value is enough: every writer and the resume check
    # read config.OUTPUT_DIR at call time, not at import.
    if args.output:
        config.OUTPUT_DIR = args.output

    scenes = [] if args.inspect else load_scenes(args.scenes)

    # Fallback descriptions, line-for-line with scenes.txt. Used only when Flow
    # refuses a primary prompt. A length mismatch is treated as fatal to the
    # fallback feature rather than tolerated: pairing scene 7 with scene 8's
    # alternate would silently generate the wrong picture.
    alts = []
    if not args.inspect and args.alt_scenes and args.alt_scenes.exists():
        alts = load_scenes(args.alt_scenes)
        if len(alts) != len(scenes):
            print(f"[alt] {args.alt_scenes.name} has {len(alts)} lines but "
                  f"scenes.txt has {len(scenes)} - ignoring it, a mismatch "
                  f"would pair scenes with the wrong fallback")
            alts = []
        else:
            print(f"[alt] {len(alts)} fallback description(s) loaded")

    wanted = None
    if args.only:
        wanted = {int(n) for n in args.only.split(",") if n.strip()}

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        # A persistent profile keeps you logged in across runs, so a restart
        # does not mean logging in again. headless is hardcoded False and must
        # stay that way: headless Chrome is trivially fingerprinted.
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(config.USER_DATA_DIR),
            headless=False,
            channel="chrome",
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(config.PAGE_LOAD_TIMEOUT)
        page.goto(config.FLOW_URL, wait_until="domcontentloaded")

        wait_until_ready(page)

        if args.inspect:
            # The pause matters: the interesting controls (asset picker, error
            # toasts) only exist once you have opened them, so the dump has to
            # happen against the page in the state you want captured, not the
            # state it loads in.
            print("\n" + "=" * 72)
            print("Set the page up the way you want it captured, e.g. open the")
            print("asset picker so its buttons are on screen.")
            print("=" * 72)
            input("Press Enter to dump the DOM... ")
            inspect_page(page)
            input("Press Enter to close the browser... ")
            context.close()
            return 0

        ensure_agent_off(page)
        ensure_model(page)

        # The reference is attached once per session. With Agent off it then
        # persists across every generation, so scenes only need text + a click.
        if not attach_reference(page):
            print("\nStopping: without the reference every image would come out")
            print("off-model, which is worse than generating nothing. Run")
            print("`python runner.py --inspect` and send me the FILE INPUTS")
            print("section so the selector can be fixed.")
            context.close()
            return 2

        failures = []
        rejected = []
        skipped = 0
        for number, prompt in enumerate(scenes, start=1):
            if wanted and number not in wanted:
                continue
            # Naming scenes explicitly overrides the resume skip, so --only can
            # redo a scene whose output exists but came out wrong.
            if not wanted and existing_output(number):
                skipped += 1
                continue                  # resume: already have this one

            try:
                run_scene(page, number, prompt,
                          alts[number - 1] if alts else None)
            except KeyboardInterrupt:
                print("\nStopped. Re-run to resume where you left off.")
                context.close()
                return 130
            except QuotaExhausted as exc:
                done = number - 1
                print(f"\n[QUOTA] {exc}")
                print(f"\nOut of daily credits after {done} scene(s). Stopping "
                      f"rather than timing out on each remaining one.")
                print(f"Finished images are kept - re-run tomorrow and it "
                      f"resumes at scene {number}.")
                context.close()
                return 3
            except ChallengeUnsolved as exc:
                print(f"\n[STOPPED] {exc}")
                print(f"Scenes 1-{number - 1} are saved. Re-run to resume "
                      f"at scene {number}.")
                context.close()
                return 5
            except SceneUnrecoverable as exc:
                print(f"\n[FATAL] {exc}")
                print(f"\nStopping. Scenes 1-{number - 1} are saved and will be "
                      f"skipped on the next run.")
                print(f"Reword beat {number} in script.json, then re-run.")
                context.close()
                return 4
            except PromptRejected as exc:
                # Worth separating from a crash: the code worked fine, Flow
                # just would not take this wording. Retrying it verbatim is
                # pointless, the prompt itself needs editing.
                print(f"    [REJECTED] {exc}")
                rejected.append(number)
            except Exception as exc:
                print(f"    [FAIL] {type(exc).__name__}: {exc}")
                failures.append(number)

            pause = DELAY_BETWEEN + random.uniform(0, DELAY_JITTER)
            print(f"    [pace] sleeping {pause:.1f}s")
            time.sleep(pause)

        print("\n" + "=" * 72)
        print(f"Saved to {config.OUTPUT_DIR}")
        if skipped:
            print(f"Skipped {skipped} scene(s) that already had an output file.")
        if rejected:
            ids = ",".join(str(n) for n in rejected)
            print(f"\n{len(rejected)} scene(s) REJECTED by Flow's policy filter: {ids}")
            print("Reword these in scenes.txt first - re-running them as-is will")
            print(f"just be rejected again:\n    python runner.py --only {ids}")
        if failures:
            retry = ",".join(str(n) for n in failures)
            print(f"\n{len(failures)} scene(s) failed: {retry}")
            print(f"Retry them with:\n    python runner.py --only {retry}")
        if not failures and not rejected:
            print("No failures.")
        print("=" * 72)

        context.close()
        return 1 if (failures or rejected) else 0


if __name__ == "__main__":
    sys.exit(main())
