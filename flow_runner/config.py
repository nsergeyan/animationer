"""
Everything fragile about Flow's UI lives in this file.

runner.py is deliberately generic: it knows "find the prompt box, type, click
submit, wait for a new image, save it" but nothing about Flow's actual markup.
So when Google reshuffles the DOM (and they will), this is the only file you
touch.

SELECTOR STATUS: every selector below is a GUESS. Nobody has seen Flow's real
DOM yet. Run `python runner.py --inspect`, log in by hand, then replace the
lists here with the exact selectors it prints. Each setting is a LIST and is
tried in order, so you can leave a fallback guess after the real one.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# --- Directories -----------------------------------------------------------
ROOT_DIR = Path(__file__).parent
OUTPUT_DIR = ROOT_DIR / "output"                  # scene_001.png, scene_002.png, ...
SCENES_FILE = ROOT_DIR / "scenes.txt"
USER_DATA_DIR = ROOT_DIR / ".chrome-profile"      # keeps you logged in between runs

load_dotenv(ROOT_DIR.parent / ".env")

# --- Target ----------------------------------------------------------------
# Point this at the PROJECT, not the tool landing page. The landing page has no
# prompt box and none of your existing media, so the run would stall waiting for
# an element that is not there.
#
# Loaded from .env rather than hardcoded, since a project id is specific to
# one Google account: labs.google/fx/tools/flow/project/<your-project-id>
FLOW_URL = os.getenv("GOOGLE_FLOW_PROJECT_URL", "")
if not FLOW_URL:
    raise RuntimeError(
        "GOOGLE_FLOW_PROJECT_URL is not set in .env. Open your project on "
        "labs.google/fx/tools/flow, copy its URL, and set it there."
    )

# --- Reference image -------------------------------------------------------
# The character art every generation is locked to. Picked up automatically:
# the first image file in assets/reference/. Set REFERENCE_IMAGE to an explicit
# Path if you ever keep more than one there.
REFERENCE_DIR = ROOT_DIR.parent / "assets" / "reference"


def _find_reference():
    if not REFERENCE_DIR.exists():
        return None
    for path in sorted(REFERENCE_DIR.iterdir()):
        if path.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            return path
    return None


REFERENCE_IMAGE = _find_reference()

# Playwright can push a file straight into an <input type="file"> even when the
# element is hidden, which is how React upload widgets are normally built. That
# sidesteps the OS file picker entirely - no clicking through Finder.
FILE_INPUT_SELECTORS = [
    'input[type="file"][accept*="image" i]',
    'input[type="file"]',
]

# Some upload widgets only mount the file input after you open their menu. If no
# input is found straight away, these get clicked first and then we look again.
# Confirmed via --inspect: the control is labelled "Add Media".
#
# Its id is #radix-:r7: - do NOT use that. Radix generates those ids per render,
# so they change between page loads and even between renders.
#
# Do NOT use 'drive_folder_upload' either. That is the SIDEBAR's "View uploaded
# media" nav button: clicking it opens the media library panel rather than the
# prompt's asset picker, so the reference uploads somewhere the prompt cannot
# see it. That mistake cost two duplicate uploads.
UPLOAD_TRIGGER_SELECTORS = [
    'button:has-text("Add Media")',
]

# DELIBERATELY UNUSED - kept as a warning.
#
# Flow's "Clear prompt" button clears the ENTIRE prompt, which includes the
# attached reference chip, not just the text. Wiring it in between scenes
# silently detached the reference and every following scene generated
# off-model. Clear the text with select-all + Delete inside the box instead.
CLEAR_PROMPT_SELECTORS_DO_NOT_USE = [
    'button:has-text("Clear prompt")',
]

# The asset picker dialog. Uploading a file only puts it in the media library -
# it does NOT attach it to the prompt. The asset has to be selected and then
# handed to the prompt with this button, which is the step that actually locks
# generations to the reference.
ADD_TO_PROMPT_SELECTORS = [
    'button:text-is("Add to Prompt")',
    'button:has-text("Add to Prompt")',
]

# How the runner confirms a reference is actually ON the prompt.
#
# These are Material Symbols ligatures rendered as button text. "cancel" is the
# remove-X on the attached reference chip; "close" belongs to "Clear prompt",
# which Flow only renders once the prompt holds something. Neither exists on an
# empty prompt bar, so either one appearing means the attach worked.
#
# This matters because selecting an asset can attach it outright and close the
# picker - in which case "Add to Prompt" is gone BECAUSE it succeeded.
ATTACHED_CHIP_TEXTS = [
    "cancel",
]

# How the reference shows up in Flow's library. Note this is the DISPLAY name,
# which is not the filename: TiredGuy_2K_202608151256.jpeg lists as "TiredGuy".
REFERENCE_ASSET_NAME = "TiredGuy"

# Used to find an already-uploaded copy so each run does not add a duplicate.
ASSET_SEARCH_SELECTORS = [
    'input[placeholder*="Search assets" i]',
    'input[placeholder*="search" i]',
]

# Seconds to let Flow finish ingesting a freshly uploaded reference.
REFERENCE_SETTLE = 10.0

# The picker and its asset list load asynchronously, so these are polled
# rather than slept through.
PICKER_WAIT = 15.0
ASSET_WAIT = 15.0

# --- Agent mode ------------------------------------------------------------
# Agent mode must stay OFF: it paraphrases the prompt in its own words, which
# destroys the style consistency the whole reference-locking approach exists to
# preserve. The runner reads this toggle's state and turns it off if needed.
#
# :text-is() is exact-match, unlike :has-text() which would also match any
# ancestor containing the word "Agent".
#
# Confirmed via --inspect: this button carries aria-pressed, so its state reads
# cleanly and the runner never has to guess. It lives in the bottom prompt bar,
# which renders LATER than the prompt box - hence AGENT_WAIT below.
AGENT_TOGGLE_SELECTORS = [
    'button:text-is("Agent")',
    'button[aria-label*="agent" i]',
]

# Seconds to wait for the prompt bar to finish rendering. Without this the
# check runs too early and reports "toggle not found" on a page that has one.
AGENT_WAIT = 20.0

# --- Model selection --------------------------------------------------------
# Flow's prompt bar carries a model chip that reads something like
# "🍌 Nano Banana 2 Lite / crop_16_9 / x1". The runner reads that chip and
# switches models if it is not already on the one you want.
#
# MODEL_NAME is matched as a SUBSTRING, so "Nano Banana 2" also matches
# "Nano Banana 2 Lite". MODEL_EXCLUDE is what disambiguates them: an option must
# contain MODEL_NAME and none of MODEL_EXCLUDE. Set MODEL_NAME to "" to leave
# whatever is selected alone.
MODEL_NAME = "Nano Banana 2"
MODEL_EXCLUDE = ["Lite"]

# Each model has its OWN daily limit, so running out on the best one does not
# mean the run is over - it means the run should carry on a tier lower. The
# ladder is tried top down: the run starts on rung 0, and each time Flow says
# the daily limit for the current model is gone, the runner drops to the next
# rung and retries the SAME scene. Only when the last rung is exhausted does the
# run stop.
#
# The pictures get worse as it descends, which is the point: a finished video
# made of mixed-tier images beats half a video made of the best ones.
#
# Each entry is (substring to match, substrings that disqualify), the same
# matching ensure_model already uses. THESE MUST MATCH THE LABELS IN FLOW'S
# MODEL MENU. The runner prints what it sees at startup as
# "[model] currently '...'" - copy the exact wording from there if a rung never
# matches. Set to [] to disable the ladder and use MODEL_NAME alone.
MODEL_LADDER = [
    ("Nano Banana Pro", []),
    ("Nano Banana 2", ["Lite", "Pro"]),
    ("Nano Banana 2 Lite", []),
]

# The chip is identified by this appearing in its text.
MODEL_CHIP_MARKER = "Nano Banana"

# ...but so is Flow's own failure card, because it quotes the model name back:
# "You've reached the daily limit for Nano Banana Pro generations." Clicking
# that opens no menu, so the model silently never changes and the run carries on
# generating with the model that is already spent.
#
# The real chip is the only candidate that also carries the aspect-ratio and
# batch-size settings, e.g. "Nano Banana Pro crop_16_9 x1". Any candidate whose
# text matches CHIP_EXCLUDE_PATTERN is thrown out first.
MODEL_CHIP_SETTINGS_MARKERS = ["crop_", "x1", "x2", "x4"]
CHIP_EXCLUDE_PATTERN = r"(failed|daily limit|reached the|retry|reuse prompt)"

# The model menu is TWO levels deep. Clicking the prompt-bar chip opens a
# settings panel (Image/Video, aspect ratio, x1-x4) that contains a SECOND
# dropdown showing the current model, e.g. "Nano Banana 2 Lite arrow_drop_down".
# The real model list only appears after clicking that one too.
MODEL_SUBMENU_MARKER = "arrow_drop_down"

# Seconds to wait for the model menu to open.
MODEL_MENU_WAIT = 8.0

# --- Startup ---------------------------------------------------------------
# How long to wait for the prompt box to show up. This doubles as the login
# wait: if you are signed out, sign in during this window and the run carries
# on by itself. No keypress needed.
READY_TIMEOUT = 240.0

# --- Selectors (ALL UNVERIFIED - replace using --inspect) -------------------
# The prompt textarea. Flow is React, so this is probably a contenteditable div
# or a textarea inside a wrapper, not a bare <input>.
# Confirmed via --inspect: a contenteditable div, which is why it carries
# role=textbox rather than being a real <textarea>.
#
# Do NOT add a bare `input` or `textarea` fallback here. The page also has
# input[data-testid="search-input"] (media library search) and
# input[aria-label="Editable text"] (the project title). Text typed into those
# lands successfully, so fill_prompt's read-back check would NOT catch the
# mistake - it would just quietly rename your project once per scene. Failing
# loudly is the right behaviour if this selector ever stops matching.
PROMPT_SELECTORS = [
    '[role="textbox"]',
    'div[contenteditable="true"]',
]

# Matched on the Material Symbols ligature text, not the class. Two buttons on
# the page say "Create": the sidebar one (icon `add_2`) starts a NEW PROJECT,
# and this one (icon `arrow_forward`) submits the prompt. They share the class
# button.sc-e8425ea6-0.hOBPaw, so class alone is a coin flip. Never loosen this
# to just "Create".
SUBMIT_SELECTORS = [
    'button:has-text("arrow_forward")',
]

# Flow serves every generation through this one API route, so matching on src
# is tighter than any container scope: it cannot match the profile avatar
# (lh3.googleusercontent.com) or the Material Symbols icon font.
# The reported per-image wrapper, div[role="button"], is far too generic to use.
RESULT_IMAGE_SELECTOR = 'img[src*="media.getMediaUrlRedirect"]'

# Only used by the click-to-download fallback, if direct fetching fails.
DOWNLOAD_BUTTON_SELECTORS = [
    'button[aria-label*="download" i]',
    'a[download]',
]

# Signs that Flow is busy. Optional: if these match nothing the runner just
# relies on new-image detection, which works on its own.
BUSY_SELECTORS = [
    '[role="progressbar"]',
    '[aria-busy="true"]',
]

# If any of these appear, the runner STOPS and waits for you. It never tries to
# solve a challenge itself.
CHALLENGE_SELECTORS = [
    'iframe[src*="recaptcha"]',
    'iframe[title*="challenge" i]',
    'text=/unusual traffic/i',
]

# How long to wait for a human to clear a CAPTCHA before giving up, in seconds.
#
# The runner never solves challenges - it waits. But it must not wait FOREVER:
# an unattended overnight run that hits a CAPTCHA at 3am would otherwise sit
# blocked until morning while caffeinate holds the Mac awake. It polls instead
# of asking for a keypress, so if you ARE at the keyboard, solving it simply
# resumes the run with nothing to press.
CHALLENGE_WAIT = 600.0

# Flow refusing a prompt on policy grounds.
#
# Do NOT use Playwright `text=` selectors here. They match ANCESTORS containing
# the text, so `text=/policy/i` climbed to a page-wide container off the footer
# "Privacy Policy" link and reported the site tagline as a rejection - before a
# prompt had even been typed. Bare "policy" is unusable on a Google page.
#
# Instead this is a regex applied in-page to small, leaf-ish elements only (see
# _FIND_REJECTION_JS in runner.py), which cannot match a whole-page container.
# Keep the wording error-specific: anything that could appear in ordinary page
# furniture will cost you a whole run.
REJECTION_PATTERN = (
    r"(violat\w*\s+(our|the|content)|against\s+(our|the)\s+\w*\s*polic"
    r"|not\s+allowed|can'?t\s+generate|cannot\s+generate|unable\s+to\s+generate"
    r"|try\s+a\s+different\s+prompt|prompt\s+was\s+blocked|content\s+polic\w+)"
)

# Where an error is allowed to be found. Semantic roles first: if Flow uses
# them, detection is exact. The generic tags are a bounded fallback and are only
# consulted for elements with little text and few children.
REJECTION_SCOPES = '[role="alert"], [role="status"], [aria-live], div, span, p'

# An error toast is a sentence. Anything longer is page furniture, not an error.
REJECTION_MAX_CHARS = 300

# How many child elements a candidate may contain and still be treated as the
# error text itself rather than a container of it.
#
# This was 0 (leaf nodes only), which silently missed the most common refusal
# Flow produces: "This generation might violate our policies. Please try a
# different prompt or send feedback" puts a LINK on the word "policies", so the
# sentence lives in an element with one child and was skipped. The <a> alone
# reads "policies" and matches nothing, so a refused scene was never noticed and
# sat through the full generation timeout instead of retrying with its
# alternate description.
#
# Keep it small. The point of the limit is that a match should be the error
# sentence, not the whole page; REJECTION_MAX_CHARS is the real backstop.
REJECTION_MAX_CHILDREN = 2

# Running out of daily credits. Detected separately from a policy rejection
# because the response is different: a rejection fails ONE scene and the run
# carries on, but no credits means every remaining scene will fail too. Without
# this the run would sit through GENERATION_TIMEOUT for each one - 30 remaining
# scenes at 300s is two and a half hours of waiting for nothing.
QUOTA_PATTERN = (
    # "0 credits" is how Flow shows an exhausted balance in the header.
    r"(\b0\s+credits\b|out of credits|no credits|credits? remaining|daily limit|"
    r"quota (exceeded|reached)|limit reached|come back tomorrow|"
    r"used all your|run out of)"
)

# ONE model's daily limit, which is a different situation from the account
# being out of credits: the other models still work. Flow words it as
# "You've reached the daily limit for Nano Banana Pro generations. Try using a
# different model." That sentence also matches QUOTA_PATTERN above (it contains
# "daily limit"), so this is checked FIRST and wins, or a single model running
# dry would abort a run that could have finished a tier lower.
MODEL_QUOTA_PATTERN = (
    r"(daily limit for[^.]{0,80}generations"
    r"|try using a different model"
    r"|switch to a different model)"
)

# --- Result filtering ------------------------------------------------------
# An <img> narrower than this is an icon or a placeholder, not a generation.
# Raise it if icons still slip through.
MIN_RESULT_WIDTH = 256

# --- Pacing ----------------------------------------------------------------
# DO NOT LOWER THESE. Steady fast requests are the single clearest signal of
# automation. runner.py clamps them to these values as a floor anyway, so
# editing them downward here has no effect.
DELAY_BETWEEN = 6.0          # seconds of base pause between scenes
DELAY_JITTER = 4.0           # plus a random 0..this, so the rhythm is irregular
TYPE_DELAY_MS = 55           # per-character typing delay, when typing is used

# Paste the prompt in one go instead of typing it character by character.
#
# The pacing rule above does NOT apply here, because typing speed is not the
# signal it was assumed to be. A 1500-character prompt is ~84 seconds of
# typing, so a 45-scene run spent over an hour on keystrokes alone. And a flat
# 55ms per character with no variance, no backspaces and no pauses is a
# cleaner automation fingerprint than a paste is: pasting a long prompt is
# exactly what a real user does, because real users write prompts elsewhere.
#
# What still matters is DELAY_BETWEEN and DELAY_JITTER. Leave those alone.
#
# Set False to go back to per-character typing. Either way the read-back check
# in fill_prompt() verifies the text actually landed, and falls through to the
# other method if it did not.
PASTE_PROMPT = True

# --- Timeouts --------------------------------------------------------------
GENERATION_TIMEOUT = 300.0   # seconds to wait for one image before giving up
POLL_INTERVAL = 1.0          # how often to check for a finished image
STABLE_POLLS = 2             # consecutive unchanged polls before we call it done
PAGE_LOAD_TIMEOUT = 60_000   # ms, Playwright convention
