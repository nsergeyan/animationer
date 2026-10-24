"""
Animationer pipeline: one script.json in, one narrated 16:9 video out.

Every stage reads and writes files under output/<slug>/, so any stage can be
re-run on its own and finished work is skipped on the next run.

    prompts    script.json -> frames.json (every picture, and how it is made)
    images     frames.json -> images/ via flow_runner (Google Flow)
    voice      script.json -> audio/ via ElevenLabs
    manifest   pairs pictures with narration, measures durations, times
               picture changes to their words, adds the outro beat
    render     manifest.json -> final.mp4 via Remotion, then the music mix
               (one classical piece per run of locations with the same mood)

With no subcommand every stage runs in order (`all`). `check` reports what is
present and what is missing without doing anything.
"""

import argparse
import colorsys
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import config
from modules import transcriber

FLOW_RUNNER = config.ROOT_DIR / "flow_runner" / "runner.py"

# Paste a finished script here (the JSON text, or the same thing as a dict
# literal) and run `python pipeline.py` with no arguments: cmd_all turns it into
# a run folder under output/ (see adopt_pasted_script) and makes the whole
# video. Set it to {} to work on the most recent run instead.
NEW_SCRIPT = {
  "topic": "Crazy F1 Facts",
  "format": "facts_short",
  "plan": {
    "spine_question": "What are the craziest hidden facts about Formula One racing?",
    "hook": {
      "fact": "F1 drivers lose up to four kilos of body weight in a single race.",
      "why_strange_to_a_newcomer": "People assume driving a race car is like driving a normal car, not an intense physical workout that causes massive weight loss.",
      "source": "Insane F1 Demands! (YouTube 2026 / First Call Medical)"
    },
    "deflations": [
      {
        "assumed": "Drivers just sit and steer normally.",
        "actual": "They lose massive body weight while enduring extreme heat and G-forces.",
        "who_decided": "The intense physics and engineering of Formula One.",
        "build_beat": "They literally sweat it out.",
        "drop_beat": "Cockpits hit sixty degrees Celsius while they pull HEAVY Gs."
      }
    ],
    "cast": [
      {
        "name": "Max Verstappen",
        "why": "Current dominant driver, shows the physical exhaustion of winning."
      },
      {
        "name": "Lewis Hamilton",
        "why": "Famous veteran who perfectly navigates the hyper-complex steering wheel."
      },
      {
        "name": "Lando Norris",
        "why": "2025 World Champion, known for carrying extreme speed through corners."
      },
      {
        "name": "Charles Leclerc",
        "why": "Famous Ferrari driver who survived huge crashes thanks to the halo."
      }
    ],
    "specifics": [
      {
        "fact": "A steering wheel costs 100,000 dollars.",
        "source": "RTR Sports Marketing 2024 / 2026 Guide",
        "beat": "7"
      },
      {
        "fact": "Lifting off the throttle generates more braking force than a road car's brakes.",
        "source": "Formula 1 aerodynamic data",
        "beat": "12"
      },
      {
        "fact": "The halo can hold a double decker bus.",
        "source": "Mercedes FIA briefing 2018",
        "beat": "17"
      }
    ],
    "facts_to_check": [
      {
        "claim": "Drivers lose 4 kilos in a race.",
        "source": "First Call Medical / F1 Driver Weight Loss during race"
      },
      {
        "claim": "Steering wheel costs 100,000 dollars.",
        "source": "RTR Sports Marketing"
      },
      {
        "claim": "Halo holds 12 tons (a double decker bus).",
        "source": "Mercedes F1 technical briefing"
      },
      {
        "claim": "Lando Norris is the 2025 World Champion.",
        "source": "2025 F1 World Championship results"
      }
    ],
    "locations": [
      {"name": "the sweltering cockpit", "visual_anchor": "", "music": "none"},
      {"name": "the steering wheel workbench", "visual_anchor": "", "music": "playful"},
      {"name": "the high speed braking zone", "visual_anchor": "", "music": "calm"},
      {"name": "the halo crash test rig", "visual_anchor": "", "music": "building"}
    ],
    "setting_anchor": ""
  },
  "beats": [
    {
      "narration": "[thoughtful] Drivers can lose four kilos.",
      "location": "the sweltering cockpit",
      "image_prompt": "reference character stands at frame left, eyes wide, watching Max Verstappen, a dark navy racing suit, sweating in one dark navy Formula 1 car at frame right, a big sign reading \"-4 KG\" above, medium-wide shot",
      "image_prompt_alt": "reference character stands at frame centre, eyes wide, beside a stocky young man with short brown hair, helmet visor raised, a dark navy racing suit, sweating in one dark navy Formula 1 car at frame left, a big sign reading \"-4 KG\" above, wide shot at eye level"
    },
    {
      "narration": "In a single race.",
      "location": "the sweltering cockpit",
      "edits": [
        "the sign disappears and one big round white clock appears at the top of the frame"
      ]
    },
    {
      "narration": "Most of it is sweat.",
      "location": "the sweltering cockpit",
      "edits": [
        "the clock disappears and a big puddle of sweat spreads under the car in the bottom foreground"
      ]
    },
    {
      "narration": "In Singapore the cockpit gets close to sixty degrees Celsius.",
      "location": "the sweltering cockpit",
      "edits": [
        "the puddle disappears and one big red thermometer reading \"60°C\" appears at frame centre between the character and the car"
      ],
      "sfx": "shock"
    },
    {
      "narration": "[deadpan] No wonder Max Verstappen looks tired.",
      "location": "the sweltering cockpit",
      "edits": [
        "the thermometer disappears and the driver in the navy suit slumps forward, tongue out, exhausted"
      ]
    },
    {
      "narration": "Look at their tiny steering wheel.",
      "location": "the steering wheel workbench",
      "image_prompt": "reference character at frame centre leans in curiously over one small black Formula 1 steering wheel in the bottom foreground, Lewis Hamilton, long dark braids, standing at frame right, medium shot",
      "image_prompt_alt": "reference character at frame left leans in curiously over one small black Formula 1 steering wheel at frame centre, a lean medium-height man with long dark braids, a short beard and a scarlet red racing suit standing at frame right, high-angle shot"
    },
    {
      "narration": "It can cost up to... ONE hundred thousand dollars.",
      "location": "the steering wheel workbench",
      "edits": [
        "a big white price tag reading \"$100,000\" appears hanging from the wheel's edge"
      ],
      "sfx": "money"
    },
    {
      "narration": "It has about twenty five buttons and dials.",
      "location": "the steering wheel workbench",
      "edits": [
        "the tag disappears, the wheel becomes a real photo cutout of a Formula 1 steering wheel, roughly pasted onto the drawing"
      ]
    },
    {
      "narration": "Drivers change settings many times every lap.",
      "location": "the steering wheel workbench",
      "edits": [
        "one big curvy black race track line appears at the top of the frame, the character's eyes go wide"
      ]
    },
    {
      "narration": "[understated] Without looking down.",
      "location": "the steering wheel workbench",
      "edits": [
        "the driver with long dark braids lifts his head and stares straight ahead, the character's eyebrows rise"
      ]
    },
    {
      "narration": "Lifting off the gas works like a brake.",
      "location": "the high speed braking zone",
      "image_prompt": "reference character stands at frame right, head tilted, watching Lando Norris, a papaya orange racing suit, in one papaya orange Formula 1 car slowing hard at frame left, wide shot",
      "image_prompt_alt": "reference character stands small in the bottom foreground, head tilted, watching a young medium-build man with tousled brown hair and light stubble, a papaya orange racing suit, in one papaya orange Formula 1 car slowing hard at frame centre, low-angle shot"
    },
    {
      "narration": "At top speed, that matches YOUR car's emergency stop.",
      "location": "the high speed braking zone",
      "edits": [
        "one small grey family hatchback appears at the top of the frame, skidding with smoking brakes"
      ],
      "sfx": "shock"
    },
    {
      "narration": "[flatly] The drag is that big.",
      "location": "the high speed braking zone",
      "edits": [
        "the hatchback disappears and big curved wind lines pile up against the orange car's nose"
      ]
    },
    {
      "narration": "The air hits them like a wall.",
      "location": "the high speed braking zone",
      "edits": [
        "the wind lines become one big grey brick wall at frame centre, pressing on the orange car's nose"
      ]
    },
    {
      "narration": "That same air pushes Lando Norris's car down through the corners.",
      "location": "the high speed braking zone",
      "edits": [
        "the wall disappears, big downward arrows press the orange car onto a tight curved track in the bottom foreground"
      ]
    },
    {
      "narration": "Above the driver sits a titanium ring.",
      "location": "the halo crash test rig",
      "image_prompt": "reference character at frame left looks up, impressed, at Charles Leclerc, a slim dark-haired man in a scarlet red racing suit, sitting in one scarlet red Formula 1 car with a thin grey titanium halo ring over the cockpit, medium-wide shot",
      "image_prompt_alt": "reference character at frame right looks up, impressed, at a slim dark-haired man in a scarlet red racing suit, tall, with short wavy hair and a clean-shaven face, sitting in one scarlet red Formula 1 car with a thin grey titanium halo ring over the cockpit, low-angle three-quarter view"
    },
    {
      "narration": "This halo can hold a London double decker bus.",
      "location": "the halo crash test rig",
      "edits": [
        "a real photo cutout of a red London double decker bus, roughly pasted onto the drawing, appears resting on top of the halo"
      ],
      "sfx": "boom"
    },
    {
      "narration": "That is about twelve tonnes.",
      "location": "the halo crash test rig",
      "edits": [
        "a big white tag reading \"12 TONS\" hangs from the bus's front corner"
      ]
    },
    {
      "narration": "In twenty eighteen, a flying McLaren landed on Charles Leclerc's halo.",
      "location": "the halo crash test rig",
      "edits": [
        "the bus and tag disappear and one orange Formula 1 car flies low over the halo from frame right, its tyre touching the halo"
      ],
      "sfx": "hit"
    },
    {
      "narration": "[deadpan] He walked away unhurt.",
      "location": "the halo crash test rig",
      "edits": [
        "the tyre disappears, the man in the scarlet red suit stands beside the car smiling, the character's eyebrows rise"
      ]
    }
  ]
}

SCRIPT_TEMPLATE = {
    "topic": "",
    "beats": [
        {"narration": "", "location": "", "image_prompt": "", "edits": []},
    ],
}


# --- Sleep prevention -------------------------------------------------------

def prevent_sleep() -> subprocess.Popen | None:
    """
    Hold the Mac awake for as long as this process lives.

    -d display, -i idle, -s system sleep; -w ties caffeinate's lifetime to our
    PID so it exits when we do, even on a crash. macOS only, and it cannot stop
    a lid-close sleep.
    """
    if not config.PREVENT_SLEEP or sys.platform != "darwin":
        return None
    try:
        proc = subprocess.Popen(
            ["caffeinate", "-dis", "-w", str(os.getpid())],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        print("[awake] sleep prevented for this run (keep the lid open)")
        return proc
    except FileNotFoundError:
        return None


# --- Pasted script ---------------------------------------------------------

def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")
    return (slug or "video")[:40]


def adopt_pasted_script() -> str | None:
    """
    Turn the NEW_SCRIPT block into a run folder. Returns its slug, or None.

    Idempotent on purpose: if a run already holds exactly this script we return
    it rather than making another folder. Otherwise every Run click while the
    variable is filled would spawn video_1, video_2, video_3...
    """
    # Accept either form. Pasting the JSON with the quotes removed makes it a
    # Python dict literal, which is a perfectly natural thing to do and used to
    # crash here, so both are supported.
    if isinstance(NEW_SCRIPT, dict):
        data = NEW_SCRIPT
        if not data:
            return None
    else:
        raw = str(NEW_SCRIPT).strip()
        if not raw:
            return None

        # Claude wraps output in fences often enough to be worth handling here
        # rather than making you delete them by hand every time.
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            if raw.rstrip().endswith("```"):
                raw = raw.rstrip()[:-3]

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(
                f"NEW_SCRIPT is not valid JSON: {exc}\n"
                f"Paste only the JSON object - no commentary, no ``` fences."
            )
    if not isinstance(data.get("beats"), list) or not data["beats"]:
        raise SystemExit("NEW_SCRIPT has no 'beats' list.")

    text = json.dumps(data, indent=2)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for existing in sorted(config.OUTPUT_DIR.glob("*/script.json")):
        if existing.read_text(encoding="utf-8") == text:
            print(f"[paste] script already set up as '{existing.parent.name}'")
            return existing.parent.name

    base = _slugify(data.get("topic"))
    slug, n = base, 2
    while (config.OUTPUT_DIR / slug).exists():
        slug, n = f"{base}_{n}", n + 1

    run_dir = config.OUTPUT_DIR / slug
    (run_dir / "images").mkdir(parents=True, exist_ok=True)
    (run_dir / "audio").mkdir(parents=True, exist_ok=True)
    (run_dir / "script.json").write_text(text, encoding="utf-8")
    print(f"[paste] {len(data['beats'])} beats -> new run '{slug}'")
    return slug


# --- Run folders -----------------------------------------------------------

def resolve_run(slug: str | None) -> Path:
    """The run folder to work in: named, or the most recently modified."""
    if slug:
        run_dir = config.OUTPUT_DIR / slug
        if not run_dir.exists():
            raise SystemExit(
                f"No run at {run_dir}. Create it with:\n"
                f"    python pipeline.py init {slug}"
            )
        return run_dir

    if not config.OUTPUT_DIR.exists():
        raise SystemExit("No runs yet. Start one with: python pipeline.py init <slug>")
    runs = [p for p in config.OUTPUT_DIR.iterdir()
            if p.is_dir() and (p / "script.json").exists()]
    if not runs:
        raise SystemExit("No runs yet. Start one with: python pipeline.py init <slug>")

    latest = max(runs, key=lambda p: p.stat().st_mtime)
    print(f"[run] {latest.name}  (most recent; use --run to pick another)")
    return latest


def load_script(run_dir: Path) -> dict:
    """Read script.json and fail loudly on the shapes that break later stages."""
    path = run_dir / "script.json"
    if not path.exists():
        raise SystemExit(f"No script.json in {run_dir}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"script.json is not valid JSON: {exc}\n"
            f"Claude sometimes wraps output in ```json fences - remove them."
        )

    beats = data.get("beats")
    if not isinstance(beats, list) or not beats:
        raise SystemExit("script.json has no 'beats' list.")

    for i, beat in enumerate(beats, start=1):
        if not isinstance(beat.get("narration"), str) or not beat["narration"].strip():
            raise SystemExit(f"Beat {i} is missing a non-empty 'narration'.")
        edits = beat.get("edits", [])
        if not isinstance(edits, list) or not all(
                _edit_parts(e)[0].strip() for e in edits):
            raise SystemExit(f"Beat {i}: 'edits' must be a list of non-empty "
                             f"lines, or of {{\"at\": ..., \"edit\": ...}} "
                             f"objects with a non-empty edit.")
        if not (beat.get("image_prompt") or "").strip() and not edits:
            # A HOLD beat: no new picture, the one on screen stays up. Only
            # inside a location, since a new place needs its own picture.
            if i == 1 or _loc(beat) != _loc(beats[i - 2]):
                raise SystemExit(
                    f"Beat {i} has no picture of its own, and it opens "
                    f"{'the video' if i == 1 else 'a new location'}, so there "
                    f"is no picture to hold. Give it an image_prompt.")
    # Builds the frame list once purely to fail here, on the script, rather
    # than halfway through a Flow run.
    build_frames(data)
    return data


# --- Naming contract -------------------------------------------------------
#
# Everything is 1-BASED, because Flow already writes scene_001 and fighting that
# is how image N ends up paired with narration N+1. That mistake still renders a
# perfectly valid video, so it would only ever be caught by watching it.

def image_name(index: int) -> str:
    return f"scene_{index:03}"


def audio_name(index: int) -> str:
    return f"beat_{index:03}"


def frame_name(index: int, k: int) -> str:
    """
    Frame k (1-based) of beat `index`.

    Frame 1 keeps the plain scene_NNN name, so every run made before chaining
    existed still renders, and adding edits to a beat later never renames the
    picture it already has. Later frames sort straight after it in a listing:
    scene_012.jpg, scene_012_f2.jpg, scene_012_f3.jpg, scene_013.jpg.
    """
    return image_name(index) if k == 1 else f"{image_name(index)}_f{k}"


def find_image(run_dir: Path, index: int) -> Path | None:
    """Extension is unknown until Flow downloads it, so glob for it."""
    return find_frame(run_dir, image_name(index))


def find_frame(run_dir: Path, name: str) -> Path | None:
    return next((run_dir / "images").glob(f"{name}.*"), None)


def find_audio(run_dir: Path, index: int) -> Path | None:
    return next((run_dir / "audio").glob(f"{audio_name(index)}.*"), None)


# --- init ------------------------------------------------------------------

def cmd_init(args) -> int:
    """Create output/<slug>/ with an empty script.json to paste into."""
    run_dir = config.OUTPUT_DIR / args.slug
    script_path = run_dir / "script.json"
    if script_path.exists():
        raise SystemExit(f"{script_path} already exists, not overwriting.")

    (run_dir / "images").mkdir(parents=True, exist_ok=True)
    (run_dir / "audio").mkdir(parents=True, exist_ok=True)
    template = dict(SCRIPT_TEMPLATE, topic=args.slug.replace("_", " "))
    script_path.write_text(json.dumps(template, indent=2), encoding="utf-8")

    print(f"Created {run_dir}")
    print(f"\nNow paste Claude's JSON into:\n    {script_path}")
    print("\nThen:  python pipeline.py prompts")
    return 0


# --- prompts ---------------------------------------------------------------

def _fragment(text: str) -> str:
    """Flatten to one line and end it with a period, so fragments join cleanly."""
    t = " ".join((text or "").split())
    if not t:
        return ""
    return t if t.endswith((".", "!", "?")) else t + "."


def _anchor_map(data: dict) -> tuple[str, dict[str, str]]:
    """
    The location description, lifted out of the beats and stored once.

    Measured across five finished videos: 60-78% of every image_prompt's
    content words were the SAME location description, retyped in every beat of
    that location - and paraphrased slightly each time. "pale plaster rooms"
    became "pale plaster walls", "packed earth yard" became "packed earth
    courtyard". Every variant is a different instruction to the image model, so
    the script was injecting drift INSIDE a single location, on top of the
    drift that already comes from the generator.

    Same argument as config.STYLE_BLOCK, applied one level down:
    anything an LLM writes it will eventually paraphrase, so text that must not
    vary is written once and pasted in here rather than retyped per beat.

    The payoff is also budget. At ~55 unique words a beat instead of ~173, a
    90-beat script is SMALLER than the 45-beat scripts this replaces.
    """
    plan = data.get("plan") or {}
    setting = _fragment(plan.get("setting_anchor") or "")
    locations = {}
    for loc in plan.get("locations") or []:
        name = " ".join((loc.get("name") or "").split()).lower()
        anchor = _fragment(loc.get("visual_anchor") or "")
        if name and anchor:
            locations[name] = anchor
    return setting, locations


def _loc(beat: dict) -> str:
    return " ".join((beat.get("location") or "").split()).lower()


def _edit_parts(item) -> tuple[str, str]:
    """
    (change, at) for one edit.

    An edit is either a plain line, or {"at": "six meters", "edit": "..."},
    where `at` is the narration word(s) the picture should change on. A plain
    line has no word, so its beat falls back to an even split.
    """
    if isinstance(item, dict):
        edit, at = item.get("edit"), item.get("at")
        return (edit if isinstance(edit, str) else "",
                at.strip() if isinstance(at, str) else "")
    return (item if isinstance(item, str) else ""), ""


def _redraw_beats(beats: list[dict]) -> set[int]:
    """
    Beats (1-based) that draw a fresh picture in the middle of a location.

    That is a jump - everything on the page moves at once - so the render
    dissolves into it instead of hard cutting. Only counted when the beat
    before ended on an edit: in an old one-picture-per-beat script every beat
    is fresh, and those were always meant to hard cut within a location.
    """
    out = set()
    for i in range(1, len(beats)):
        beat, prev = beats[i], beats[i - 1]
        j = i - 1
        while j > 0 and _is_hold(beats[j]):
            j -= 1
        if ((beat.get("image_prompt") or "").strip()
                and _loc(beat) == _loc(prev) and beats[j].get("edits")):
            out.add(i + 1)
    return out


def _is_hold(beat: dict) -> bool:
    """A beat with no picture of its own: the one on screen stays up."""
    return not (beat.get("image_prompt") or "").strip() and not beat.get("edits")


def _scene_text(text: str) -> str:
    """
    One line, minus any style block the model wrote out of habit.

    Style is OURS, not the model's: a paraphrased copy would compete with
    config.STYLE_BLOCK, and the whole point is that this text never varies
    between scenes or videos. A newline would also split the frame's log
    line in two, so it is flattened here as well.
    """
    text = " ".join((text or "").split())
    cut = text.lower().find("style:")
    if cut != -1:
        text = text[:cut].rstrip(" .,;") + "."
    return text


def build_frames(data: dict) -> list[dict]:
    """
    Every picture the video needs, in order, and how each one gets made.

    A beat's frames are its image_prompt, if it has one, then its edits:

      establish  the image_prompt. Drawn fresh against the character
                 reference, exactly as every frame was before chaining.
      edit       one edit line, applied to the frame straight before it. That
                 frame is attached in Flow as the reference, so it is recorded
                 as `parent`, and the runner redoes an edit whenever its parent
                 changes.

    Old scripts carry an image_prompt on every beat and no edits, so they come
    out exactly as they always did: one establish frame per beat.

    Exits on a chain that cannot work: an edit with nothing before it, or one
    that would carry a picture across a location change. The render dissolves
    there, so the new place needs its own first picture.
    """
    setting_anchor, location_anchors = _anchor_map(data)
    frames: list[dict] = []
    for index, beat in enumerate(data["beats"], 1):
        loc = _loc(beat)
        parts = []
        if (beat.get("image_prompt") or "").strip():
            parts.append(("establish", beat["image_prompt"], ""))
        parts += [("edit", *_edit_parts(e)) for e in beat.get("edits") or []]

        for k, (mode, text, at) in enumerate(parts, 1):
            # `text` is the script's own words, kept for the runner's log line:
            # every edit prompt opens with the same EDIT_TEMPLATE wrapper.
            # `at` is the word it changes on, for the manifest's timing.
            frame = {"name": frame_name(index, k), "beat": index, "frame": k,
                     "mode": mode, "location": loc, "text": _scene_text(text),
                     "at": at}

            if mode == "establish":
                # Order: style, then subject and action, then the place. The
                # style leads so the model commits to the medium before it
                # reads a word of realistic scene description - see
                # config.STYLE_BLOCK's POSITION note for the photo-grounding
                # failure that rule exists to stop. The place trails because
                # leading with it buries the subject.
                anchor = " ".join(a for a in (location_anchors.get(loc, ""),
                                              setting_anchor) if a)

                def full(t: str) -> str:
                    return " ".join(part for part in (
                        config.STYLE_BLOCK, _fragment(_scene_text(t)), anchor
                    ) if part)

                frame["prompt"] = full(text)
                # Flow refuses a prompt now and then; retrying the same words
                # gets the same answer, so a milder description of the same
                # moment is what actually recovers it.
                alt = (beat.get("image_prompt_alt") or "").strip()
                frame["alt"] = full(alt) if alt else None
                frame["parent"] = None
            else:
                prev = frames[-1] if frames else None
                if prev is None:
                    raise SystemExit(
                        f"Beat {index} opens the video with an edit, so there "
                        f"is no picture to edit. Give it an image_prompt.")
                if prev["location"] != loc:
                    raise SystemExit(
                        f"Beat {index} starts location {beat.get('location')!r} "
                        f"with an edit, which would edit the last picture of "
                        f"{prev['location']!r}. Give beat {index} an image_prompt.")
                frame["prompt"] = config.EDIT_TEMPLATE.format(
                    edit=_fragment(_scene_text(text)))
                # edit_alt backs up the beat's one edit. A beat with several
                # edits has no single edit it stands for, so it gets none.
                alt = (beat.get("edit_alt") or "").strip()
                frame["alt"] = (config.EDIT_TEMPLATE.format(
                    edit=_fragment(_scene_text(alt)))
                    if alt and len(beat.get("edits") or []) == 1 else None)
                frame["parent"] = prev["name"]
            frames.append(frame)
    return frames


def _report_tempo(beats: list[dict], spoken_words) -> None:
    """
    How long each picture stays up, bucketed into the three tempos.

    Estimated from word counts at the measured speaking rate: a beat's time is
    shared by its pictures, and a hold beat adds its time to the picture
    already up. Close enough to judge the mix before a long image run.
    """
    per_second = WORDS_PER_MINUTE / 60 * config.NARRATION_SPEED
    holds: list[float] = []
    for b in beats:
        seconds = spoken_words(b["narration"]) / per_second
        n = (1 if (b.get("image_prompt") or "").strip() else 0) + len(b.get("edits") or [])
        if n == 0 and holds:
            holds[-1] += seconds
        else:
            holds += [seconds / max(n, 1)] * max(n, 1)
    if not holds:
        return
    fast = sum(1 for h in holds if h < config.TEMPO_FAST_MAX)
    slow = sum(1 for h in holds if h >= config.TEMPO_MEDIUM_MAX)
    medium = len(holds) - fast - slow
    pct = lambda k: f"{k / len(holds):.0%}"
    print(f"[prompts] tempo: {pct(fast)} fast / {pct(medium)} medium / "
          f"{pct(slow)} slow, a picture every {sum(holds) / len(holds):.1f}s "
          f"on average")
    flash = [h for h in holds if h < 1.0]
    stuck = [h for h in holds if h > 4.5]
    if len(flash) > len(holds) / 10:
        print(f"[warn] {len(flash)} pictures stay up under 1s; too fast to read")
    if stuck:
        print(f"[warn] {len(stuck)} pictures stay up over 4.5s; the frame "
              f"sits still too long")


def _long_chains(frames: list[dict]) -> list[tuple[int, int]]:
    """(beat where the chain starts, edits in a row) for over-long chains."""
    found, run, start = [], 0, 0
    for f in frames + [{"mode": "establish", "beat": 0}]:
        if f["mode"] == "edit":
            run += 1
            continue
        if run > config.CHAIN_MAX_EDITS:
            found.append((start, run))
        run, start = 0, f["beat"]
    return found


def music_moods(data: dict) -> dict[str, str]:
    """
    {location: mood} from plan.locations[].music, or {} when the script has
    no moods (it then renders over its own music.mp3, if it has one).

    Stops on a missing or unknown mood rather than guessing. This runs in the
    first stage on purpose: a typo here would otherwise only surface at render
    time, after an hour of image generation.
    """
    locations = (data.get("plan") or {}).get("locations") or []
    moods = {loc.get("name"): str(loc.get("music") or "").strip()
             for loc in locations if isinstance(loc, dict)}
    if not any(moods.values()):
        return {}

    from modules import video_editor
    library = video_editor.mood_library()
    used = sorted({b["location"] for b in data["beats"] if b.get("location")})
    problems = []
    for loc in used:
        mood = moods.get(loc)
        if not mood:
            problems.append(f"location '{loc}' has no music mood")
        elif mood == config.MUSIC_SILENT_MOOD:
            continue
        elif mood not in library:
            problems.append(f"location '{loc}': unknown mood '{mood}'")
        elif not library[mood]:
            problems.append(f"mood '{mood}' has no audio files in "
                            f"{config.MUSIC_MOODS_DIR / mood}")
    if problems:
        raise SystemExit("[music] " + "\n[music] ".join(problems) +
                         f"\n[music] moods available: {', '.join(library) or 'none'}"
                         f" (folders in {config.MUSIC_MOODS_DIR})")
    return {loc: moods[loc] for loc in used}


def sfx_plan(data: dict, warn: bool = False) -> dict[int, str]:
    """
    {beat index (1-based): tag} from beats[].sfx, or {} when sounds are off.

    Stops on an unknown tag, a tag with no files, or more reactions than the
    limits allow, for the same reason music_moods stops early: a typo should
    surface before an hour of images, not at render time. The softer limits
    (share of beats, spacing) only warn, and only when `warn` is set, so the
    warning prints once per command.
    """
    if not config.SFX_ENABLED:
        return {}
    tags = {i: str(b.get("sfx") or "").strip().lower()
            for i, b in enumerate(data["beats"], 1)}
    tags = {i: t for i, t in tags.items() if t}
    allowed = config.SFX_PICTURE_TAGS + config.SFX_AFTER_TAGS

    from modules import video_editor
    library = video_editor.sfx_library()
    problems = []
    for i, tag in tags.items():
        if tag in (config.SFX_TRANSITION_TAG, config.SFX_OUTRO_TAG):
            problems.append(f"beat {i}: '{tag}' is placed by the code, "
                            f"do not tag it")
        elif tag not in allowed:
            problems.append(f"beat {i}: unknown sound tag '{tag}'")
        elif not library.get(tag):
            problems.append(f"beat {i}: no audio files in {config.SFX_DIR / tag}")
    after = [i for i, t in tags.items() if t in config.SFX_AFTER_TAGS]
    rare = [i for i, t in tags.items() if t in config.SFX_RARE_TAGS]
    if len(after) > config.SFX_MAX_AFTER:
        problems.append(f"{len(after)} reaction sounds (beats "
                        f"{', '.join(map(str, after))}), the limit is "
                        f"{config.SFX_MAX_AFTER}: remove some")
    if len(rare) > config.SFX_MAX_RARE:
        problems.append(f"{len(rare)} {'/'.join(config.SFX_RARE_TAGS)} sounds "
                        f"(beats {', '.join(map(str, rare))}), the limit is "
                        f"{config.SFX_MAX_RARE}: remove some")
    if problems:
        raise SystemExit(
            "[sfx] " + "\n[sfx] ".join(problems) +
            f"\n[sfx] tags: {', '.join(allowed)} (folders in {config.SFX_DIR})")

    if warn:
        picture = len(tags) - len(after)
        if picture > len(data["beats"]) * config.SFX_PICTURE_SHARE:
            print(f"[warn] {picture} picture sounds on {len(data['beats'])} beats, "
                  f"more than 1 in {round(1 / config.SFX_PICTURE_SHARE)}: they "
                  f"stop meaning anything")
        close = [(a, b) for a, b in zip(after, after[1:])
                 if b - a < config.SFX_MIN_AFTER_GAP_BEATS]
        for a, b in close:
            print(f"[warn] reaction sounds on beats {a} and {b} are only "
                  f"{b - a} beats apart (aim for {config.SFX_MIN_AFTER_GAP_BEATS}+)")
    return tags


def _place_sfx(entries: list[dict], beats: list[dict], tags: dict[int, str],
               seed: str) -> int:
    """
    Add "sfx" to manifest entries and stretch durations for their pauses.

    Kinds and where each one lands, in seconds from the beat's start:
      picture     0, as the beat's picture appears
      after       after the last word, in a pause added to the beat
      transition  after everything else in the beat, in a short pause added
                  before a location change (the dissolve follows it)
      outro       after the outro line
    The pause is part of `duration`, so Remotion, the music timeline and the
    length report all see it without knowing anything about sound.
    Returns how many effects were placed.
    """
    from modules import video_editor
    library = video_editor.sfx_library()
    used: dict[str, int] = {}

    def take(tag: str) -> tuple[str, float] | None:
        files = library.get(tag)
        if not files:
            return None
        path = video_editor.pick_sfx(files, seed, tag, used.get(tag, 0))
        used[tag] = used.get(tag, 0) + 1
        return path.relative_to(config.SFX_DIR).as_posix(), _audio_duration(path)

    def after_line(entry: dict, tag: str, kind: str, got=None) -> None:
        got = got or take(tag)
        if got:
            name, length = got
            at = entry["duration"] + config.SFX_AFTER_GAP
            entry.setdefault("sfx", []).append(
                {"tag": tag, "kind": kind, "file": name, "at": round(at, 3)})
            entry["duration"] = round(at + min(length, config.SFX_MAX_SECONDS), 3)

    for k, entry in enumerate(entries):
        # The outro is appended after the last beat, so its index is past them.
        beat = beats[entry["index"] - 1] if entry["index"] <= len(beats) else None
        tag = tags.get(entry["index"]) if beat is not None else None
        if tag in config.SFX_PICTURE_TAGS:
            got = take(tag)
            if got and Path(got[0]).name in config.SFX_VOICE_FILES:
                # A voice would talk over the narrator: wait for the line to
                # end, at the level of a picture sound.
                after_line(entry, tag, "picture", got)
            elif got:
                entry.setdefault("sfx", []).append(
                    {"tag": tag, "kind": "picture", "file": got[0], "at": 0.0})
        elif tag in config.SFX_AFTER_TAGS:
            after_line(entry, tag, "after")

        nxt = entries[k + 1] if k + 1 < len(entries) else None
        # A real location change only: into the outro (no location) the outro
        # sound is enough, and a script without locations has no changes.
        if (beat is not None and nxt is not None and entry.get("location")
                and nxt.get("location") and nxt["location"] != entry["location"]):
            got = take(config.SFX_TRANSITION_TAG)
            if got:
                entry.setdefault("sfx", []).append(
                    {"tag": config.SFX_TRANSITION_TAG, "kind": "transition",
                     "file": got[0], "at": entry["duration"]})
                entry["duration"] = round(entry["duration"]
                                          + config.SFX_TRANSITION_PAUSE, 3)
        if beat is None and nxt is None:
            after_line(entry, config.SFX_OUTRO_TAG, "outro")
    return sum(len(e.get("sfx", [])) for e in entries)


def cmd_prompts(args) -> int:
    """Turn script.json into frames.json and warn about anything off-spec."""
    run_dir = resolve_run(args.run)
    data = load_script(run_dir)
    music_moods(data)   # stops here on a bad mood, before any images are made
    sfx_plan(data, warn=True)   # and here on a bad sound tag
    beats = data["beats"]
    frames = build_frames(data)
    out_path = run_dir / "frames.json"

    out_path.write_text(json.dumps({
        "generated_by": "pipeline.py prompts from script.json - do not edit "
                        "by hand, edit script.json and re-run",
        "frames": frames,
    }, indent=2), encoding="utf-8")

    establish = [f for f in frames if f["mode"] == "establish"]
    edits = len(frames) - len(establish)
    print(f"[prompts] {len(beats)} beats -> {len(frames)} frames -> {out_path}")
    print(f"[prompts]   {len(establish)} drawn fresh from the reference, "
          f"{edits} edited from the frame before")
    print(f"[prompts] style block on all {len(establish)} fresh frames "
          f"(identical every scene, every video)")
    alts = sum(1 for f in establish if f["alt"])
    edit_alts = sum(1 for f in frames if f["mode"] == "edit" and f["alt"])
    if alts or edit_alts:
        print(f"[prompts] fallbacks for refused prompts: "
              f"{alts}/{len(establish)} fresh, {edit_alts}/{edits} edits")

    # Location/setting anchors come from plan, not from the beat text. See
    # _anchor_map: the beats used to carry a paraphrased copy each.
    setting_anchor, location_anchors = _anchor_map(data)
    if location_anchors or setting_anchor:
        missing = [f["beat"] for f in establish
                   if location_anchors and f["location"] not in location_anchors]
        print(f"[prompts] location anchor injected into "
              f"{len(establish) - len(missing)}/{len(establish)} fresh frames")
        if missing:
            shown = ",".join(str(n) for n in missing[:12])
            more = f" (+{len(missing) - 12})" if len(missing) > 12 else ""
            print(f"[warn] no matching plan.locations entry: {shown}{more}")
            print("       beat.location must match plan.locations[].name exactly; "
                  "these beats carry no location description at all")

    stripped = sum(1 for b in beats
                   if "style:" in (b.get("image_prompt") or "").lower())
    if stripped:
        print(f"[prompts] replaced the model's own style block in {stripped} "
              f"prompt(s) with config.STYLE_BLOCK")

    for start, run in _long_chains(frames):
        print(f"[warn] {run} edits in a row from beat {start} "
              f"(limit {config.CHAIN_MAX_EDITS})")
        print("       every edit drifts a little and it compounds; give a beat "
              "partway through a fresh image_prompt")

    longest = max(len(f["prompt"]) for f in frames)
    typing_s = longest * 55 / 1000
    print(f"[prompts] longest prompt {longest} chars (~{typing_s:.0f}s to type)")

    _warn_off_spec(beats, data.get("format", ""), n_frames=len(frames))
    print(f"\nNext:  python pipeline.py images")
    return 0


# Words per beat, by format. Arithmetic, not taste: one image is held for its
# whole narration, so the word count IS the cut rate. Skits cut faster still,
# because a joke's timing is the image change. Progression runs short too,
# because the format is built on short declarative sentences.
#
# These are the SINGLE-BAND formats: every beat aims at the same length. The
# explainer format no longer works this way - see RHYTHM_FORMATS below.
WORD_BANDS = {"skit": (12, 15), "progression": (14, 19)}
DEFAULT_WORD_BAND = (17, 21)

# Measured over 231 shipped beats across five finished videos: 4207 spoken
# words against 1425s of narration audio. The audio is tightly trimmed (no
# detectable silence at -30dB), so this is real delivery rate, not padding.
#
# The previous 206 came from a single 17-beat run and made every length
# estimate ~16% short. Do not restore it without re-measuring across several
# finished runs: sum the spoken words in each manifest entry and divide by the
# sum of its durations. One run is not enough to see it.
#
# Lives in config because modules/voice_generator.py needs it as well, and a
# module importing pipeline would be a cycle.
WORDS_PER_MINUTE = config.WORDS_PER_MINUTE

# --- Three-tier rhythm (explainer) -----------------------------------------
# Video length fixes the total spoken words, so more beats does NOT mean more
# narration - it means the same words cut into smaller pieces.
#
# Since 2026-10-11 every beat is exactly ONE picture (a fresh drawing or one
# edit of the picture before), so a beat's length IS how long its picture
# stays up:
#
#   SHORT beat    3-5 words   ~1.5s   a reaction, a consequence, a punch
#   MEDIUM beat   6-8 words   ~2.3s   ordinary explaining
#   LONG beat     9-12 words  ~3.5s   the big fact, the number, the turn
#
# About a quarter / half / quarter averages ~2.4s a picture, ~75 beats for 3
# minutes (config.TARGET_VIDEO_SECONDS; it was ~45 beats for 2 minutes from
# 2026-10-20 to 2026-10-21). Replaces the two-tier 3-6 / 8-12 split (2026-10-07), which pass2
# then cut into a picture every ~1.1s - too fast. Before that, 4-8 / 10-15.
#
# The MIX is the rule. Uniformly short beats are a metronome, uniformly long
# ones a slideshow, so the checks police the shares and the runs, and only
# flag a single beat when it is too long to sit under one still image.
RHYTHM_FORMATS = {"explainer", "facts_short"}
SHORT_MAX_WORDS = 5       # at or under this, a beat counts as SHORT
MEDIUM_MAX_WORDS = 8      # over SHORT and at or under this, MEDIUM; above, LONG
LONG_MAX_WORDS = 12       # over this, the image freezes while narration runs
MIN_WORDS = 3             # under this it does not register as a beat at all
TIER_SHARE = {"short": (0.15, 0.35), "medium": (0.35, 0.65),
              "long": (0.15, 0.35)}
MAX_RUN_SAME = 3          # more of one length in a row and the rhythm goes flat

# Mirrors OUTRO_FRAMES in remotion/src/constants.ts (30 frames at 30fps):
# the hold on the last image after the final word.
OUTRO_HOLD_SECONDS = 1.0


def _check_rhythm(beats: list[dict], spoken_words, report) -> None:
    """
    Police the three-tier rhythm for RHYTHM_FORMATS: the share of short,
    medium and long beats, and runs of one length back to back.
    """
    counts = [spoken_words(b["narration"]) for b in beats]
    n = len(counts)
    if not n:
        return

    report(f"narration over {LONG_MAX_WORDS} words",
           [i for i, c in enumerate(counts, 1) if c > LONG_MAX_WORDS],
           "the image sits frozen while the narration keeps going")
    report(f"narration under {MIN_WORDS} words",
           [i for i, c in enumerate(counts, 1) if c < MIN_WORDS],
           "too short to register as its own beat")

    def tier(c: int) -> str:
        if c <= SHORT_MAX_WORDS:
            return "short"
        return "medium" if c <= MEDIUM_MAX_WORDS else "long"

    tiers = [tier(c) for c in counts]
    for name, (lo, hi) in TIER_SHARE.items():
        share = tiers.count(name) / n
        if not lo <= share <= hi:
            print(f"[warn] {share:.0%} of beats are {name} "
                  f"(want {lo:.0%}-{hi:.0%})")

    # Collapse into runs so a stretch of six short beats is reported once.
    bad, start = [], 0
    for i in range(1, n + 1):
        if i == n or tiers[i] != tiers[start]:
            if i - start > MAX_RUN_SAME:
                bad.append(f"{start + 1}-{i} ({tiers[start]})")
            start = i
    if bad:
        print(f"[warn] {len(bad)} run(s) of more than {MAX_RUN_SAME} beats of "
              f"one length: {', '.join(bad[:8])}")
        print("       vary the length - one length in a row reads flat")

    print(f"[prompts] rhythm: {tiers.count('short')} short / "
          f"{tiers.count('medium')} medium / {tiers.count('long')} long, "
          f"avg {sum(counts) / n:.1f} words a beat")


def _warn_off_spec(beats: list[dict], fmt: str = "",
                   n_frames: int | None = None) -> None:
    """
    Flag beats that drift from the spec in prompts/pass1_narration.txt.

    Warnings, not errors - the script is still usable. But catching them here
    costs nothing, whereas noticing after a full Flow run costs hours.
    """
    # Emotion tags like [surprised] are spoken as delivery, not words.
    def spoken_words(text: str) -> int:
        return len(re.sub(r"\[[^\]]*\]", " ", text).split())

    key = fmt.strip().lower()
    rhythm = key in RHYTHM_FORMATS
    lo, hi = WORD_BANDS.get(key, DEFAULT_WORD_BAND)
    if fmt and rhythm:
        print(f"[prompts] format {fmt!r}: short <={SHORT_MAX_WORDS} / medium "
              f"<={MEDIUM_MAX_WORDS} / long <={LONG_MAX_WORDS} words, one "
              f"picture per beat")
    elif fmt:
        print(f"[prompts] format {fmt!r}: expecting {lo}-{hi} words per beat")

    short = [] if rhythm else [i for i, b in enumerate(beats, 1)
                               if spoken_words(b["narration"]) < lo]
    long_ = [] if rhythm else [i for i, b in enumerate(beats, 1)
                               if spoken_words(b["narration"]) > hi]
    # Only beats that draw a fresh picture carry an image_prompt. An edit-only
    # beat continues the picture before it, so the checks on how a picture is
    # first staged (reference, alt, back view) apply to these alone, while the
    # checks on what ends up on screen (render words, photos, labels) read the
    # edits too.
    def prompt(b: dict) -> str:
        return b.get("image_prompt") or ""

    def visual(b: dict) -> str:
        return " ".join([prompt(b)] + [_edit_parts(e)[0]
                                       for e in b.get("edits") or []])

    drawn = [(i, b) for i, b in enumerate(beats, 1) if prompt(b).strip()]
    no_ref = [i for i, b in drawn
              if "reference character" not in prompt(b).lower()]

    def report(label, items, why):
        if not items:
            return
        shown = ",".join(str(n) for n in items[:12])
        more = f" (+{len(items) - 12})" if len(items) > 12 else ""
        print(f"[warn] {label}: {shown}{more}")
        print(f"       {why}")

    if rhythm:
        _check_rhythm(beats, spoken_words, report)
    else:
        report(f"narration under {lo} words", short,
               "beat is short; the video cuts faster than the script needs")
        report(f"narration over {hi} words", long_,
               "beat runs long; the image sits frozen while narration continues")
    report('missing "the reference character"', no_ref,
           "the character may not be locked to your reference art")

    # An alt identical to its primary is not a fallback. If the first wording
    # was refused, the same wording gets refused again and the run stops - the
    # retry is spent achieving nothing.
    def flat(t: str) -> str:
        return " ".join((t or "").split()).lower()

    copies = [i for i, b in drawn
              if b.get("image_prompt_alt")
              and flat(b["image_prompt_alt"]) == flat(prompt(b))]
    missing_alt = [i for i, b in drawn
                   if not (b.get("image_prompt_alt") or "").strip()]

    report("no image_prompt_alt", missing_alt,
           "a refused beat has no second attempt and stops the run")
    report("image_prompt_alt identical to image_prompt", copies,
           "an identical retry gets refused identically - reword or restage it")

    edited = [(i, b) for i, b in enumerate(beats, 1) if b.get("edits")]
    report("no edit_alt",
           [i for i, b in edited if not (b.get("edit_alt") or "").strip()],
           "a refused edit has no second attempt and stops the run")
    report("edit_alt identical to its edit",
           [i for i, b in edited if len(b["edits"]) == 1 and b.get("edit_alt")
            and flat(b["edit_alt"]) == flat(_edit_parts(b["edits"][0])[0])],
           "an identical retry gets refused identically - show it differently")

    # The reference art is a single front-facing pose. Ask for his back and the
    # model has nothing to work from, so it puts his face on a back-facing body
    # and the head comes out rotated 180 degrees.
    back_view = re.compile(
        r"(from behind|over[- ]the[- ]shoulder|over his shoulder|"
        r"back to the camera|seen from behind|from the back)", re.I)
    # A back view is fine as long as the prompt says there is no face on that
    # side. Without it the reference's front-facing head gets pasted on and
    # comes out rotated.
    no_face = re.compile(r"(no face|back of his (plain white )?head|"
                           r"face not visible)", re.I)
    backs = [i for i, b in drawn
             if back_view.search(prompt(b))
             and not no_face.search(prompt(b))]
    if backs:
        print(f"[warn] back view without a 'no face' clause: "
              f"{','.join(str(n) for n in backs)}")
        print("       add 'showing the back of his plain white head with no "
              "face', or his head comes out rotated")

    # Lighting and atmosphere words are STYLE instructions wearing a scene
    # description's clothes. "grey overcast light" tells the model how to
    # RENDER, and it renders photographically. Combined with a real-world
    # subject it produced an actual photograph with the character pasted on.
    render_words = re.compile(
        r"\b(overcast|lighting|lamplight|backlit|glow\w*|shadowy|haze|hazy|"
        r"blurred|out of focus|depth of field|gleaming|shimmer\w*|"
        r"realistic|detailed|photo\w*|cinematic)\b", re.I)
    # "photo cutout" is the one sanctioned photo phrase (see the photo checks
    # below), so it is taken out before looking for stray photo words.
    cutout = re.compile(r"\bphoto cutout\b", re.I)
    risky = [(i, sorted(set(w.lower() for w in render_words.findall(
                 cutout.sub(" ", visual(b))))))
             for i, b in enumerate(beats, 1)]
    risky = [(i, w) for i, w in risky if w]
    if risky:
        print("[warn] render/lighting words (these push the image photographic):")
        for i, words in risky[:8]:
            print(f"       beat {i}: {', '.join(words)}")
        print("       describe WHAT is there, not how it is lit or rendered")

    # The white-page style allows two gags that work only while they are rare:
    # a photo cutout of one object, and a short quoted label. Photo wording is
    # also what drags a whole frame photographic, so the cap is a safety limit
    # as well as a taste one. Limits mirror section 0B of pass2_visuals.txt.
    n = len(beats)
    photos = [i for i, b in enumerate(beats, 1)
              if cutout.search(visual(b))]
    if len(photos) > n / 6:
        print(f"[warn] {len(photos)} photo cutouts in {n} beats "
              f"(max ~{n // 6}, 1 in 6): {','.join(map(str, photos[:12]))}")
        print("       rare is the joke; every frame a photo is just clutter")
    elif len(photos) < n / 15:
        print(f"[warn] only {len(photos)} photo cutouts in {n} beats "
              f"(aim ~{n // 10}, 1 in 10)")
    paired = [f"{a}-{b}" for a, b in zip(photos, photos[1:]) if b == a + 1]
    if paired:
        print(f"[warn] photo cutouts in back-to-back beats: {', '.join(paired)}")
    alt_photos = [i for i, b in enumerate(beats, 1)
                  if cutout.search(b.get("image_prompt_alt") or "")]
    if alt_photos:
        print(f"[warn] photo cutout in image_prompt_alt: "
              f"{','.join(map(str, alt_photos[:12]))}")
        print("       the alt is the fallback; it should be the doodle version")
    labels = [i for i, b in enumerate(beats, 1)
              if re.search(r'"[^"]+"', visual(b))]
    if len(labels) > n / 4:
        print(f"[warn] {len(labels)} beats with quoted labels in {n} "
              f"(max ~{n // 4}, 1 in 4)")
        print("       labels only where the words ARE the joke")

    # An edit keeps the frame's camera. Asking an edit for a new shot makes the
    # model redraw the whole picture, which breaks the chain it exists for -
    # a new framing needs a fresh image_prompt instead.
    camera = re.compile(
        r"\b(close-?up|wide shot|medium shot|long shot|two-shot|"
        r"zoom(s|ing)? (in|out)|"
        r"low[- ]angle|high[- ]angle|camera)\b", re.I)
    reframed = [i for i, b in enumerate(beats, 1)
                if any(camera.search(_edit_parts(e)[0])
                       for e in b.get("edits") or [])]
    if reframed:
        print(f"[warn] edits asking for a new camera shot: "
              f"{','.join(map(str, reframed[:12]))}")
        print("       an edit keeps the framing; use a fresh image_prompt "
              "to reframe")

    # Word-timed edits: the word has to be in the beat, in order, or the
    # manifest cannot time it and the beat falls back to an even split.
    untimed = []
    for i, b in enumerate(beats, 1):
        words = [_word_key(w) for w in transcriber.strip_tags(b["narration"]).split()]
        pos = 0
        for e in b.get("edits") or []:
            at = _edit_parts(e)[1]
            if not at:
                continue
            found = _find_phrase(words, at, pos)
            if found < 0:
                untimed.append(i)
                break
            pos = found + 1
    if untimed:
        print(f"[warn] edit \"at\" words not found in order in the narration: "
              f"{','.join(map(str, untimed[:12]))}")
        print("       copy the word exactly from the beat; these beats split "
              "their pictures evenly instead")

    total_words = sum(spoken_words(b["narration"]) for b in beats)
    narration_s = total_words / WORDS_PER_MINUTE * 60 / config.NARRATION_SPEED

    # The finished video is longer than its narration. Every hard cut adds a
    # breath that no transition eats (config.CUT_PAD_SECONDS), and the pipeline
    # bolts on an outro beat afterwards. A dissolve costs nothing - its tail is
    # consumed by the overlap - so only same-location boundaries are counted.
    locations = [" ".join((b.get("location") or "").split()) for b in beats]
    redraws = _redraw_beats(beats)
    hard_cuts = sum(1 for i, (a, b) in enumerate(zip(locations, locations[1:]), 2)
                    if a and a == b and i not in redraws)
    pad_s = hard_cuts * config.CUT_PAD_SECONDS
    outro = config.OUTRO_ENABLED and key not in config.NO_OUTRO_FORMATS
    outro_s = (OUTRO_HOLD_SECONDS + 2.1) if outro else 0.0

    # Sounds tagged "after" get their own pause (~1.5s measured on
    # crazy_f1_facts), and a location change holds SFX_TRANSITION_PAUSE
    # before its dissolve. The last picture holds OUTRO_HOLD_SECONDS even
    # when the format has no outro. Missing these made crazy_f1_facts
    # estimate 49s and render 62s.
    after_n = sum(1 for b in beats if b.get("sfx") in config.SFX_AFTER_TAGS)
    changes = sum(1 for a, b in zip(locations, locations[1:]) if a != b)
    sfx_s = (after_n * 1.5 + changes * config.SFX_TRANSITION_PAUSE
             if config.SFX_ENABLED else 0.0)
    hold_s = 0.0 if outro else OUTRO_HOLD_SECONDS

    est = narration_s + pad_s + outro_s + sfx_s + hold_s
    per_beat = narration_s / len(beats) if beats else 0
    print(f"[prompts] ~{total_words} spoken words, {narration_s:.0f}s narration "
          f"+ {pad_s:.0f}s cut pads + {sfx_s:.0f}s sound pauses "
          f"+ {outro_s + hold_s:.0f}s outro/end hold")
    print(f"[prompts] estimated final video {est:.0f}s ({est / 60:.1f} min)")
    print(f"[prompts] ~{per_beat:.1f}s per beat across {len(beats)} beats")
    if n_frames:
        print(f"[prompts] ~{narration_s / n_frames:.1f}s per image across "
              f"{n_frames} frames")
        _report_tempo(beats, spoken_words)

    # Catch a script that is the wrong LENGTH while it is still just text. The
    # alternative is finding out after a full Flow run and a full TTS run.
    target = config.TARGET_SECONDS_BY_FORMAT.get(
        key, getattr(config, "TARGET_VIDEO_SECONDS", 0.0))
    tol = getattr(config, "TARGET_VIDEO_TOLERANCE", 0.15)
    if target and beats:
        drift = (est - target) / target
        if abs(drift) > tol:
            direction = "over" if drift > 0 else "under"
            need = round(abs(est - target) / max(per_beat, 0.1))
            print(f"[warn] {abs(drift):.0%} {direction} the "
                  f"{target / 60:.1f} min target ({est / 60:.1f} min)")
            print(f"       adjust the script's total word budget - roughly "
                  f"{need} beat(s) {'too many' if drift > 0 else 'short'}")


# --- images ----------------------------------------------------------------

def cmd_images(args) -> int:
    """Hand frames.json to flow_runner, then check every edit took effect."""
    run_dir = resolve_run(args.run)
    frames = run_dir / "frames.json"
    if not frames.exists():
        raise SystemExit(f"No frames.json in {run_dir}. Run: python pipeline.py prompts")

    images_dir = run_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # The runner works out what is left to do (missing frames, plus any edit
    # whose parent changed) BEFORE it opens Chrome, and exits quietly when
    # that is nothing, so a resumed `all` does not pop a window just to skip.
    cmd = [sys.executable, str(FLOW_RUNNER),
           "--frames", str(frames.resolve()),
           "--output", str(images_dir.resolve())]
    if args.only:
        cmd += ["--only", args.only]

    print(f"[images] handing off to flow_runner -> {images_dir}")
    code = subprocess.run(cmd, cwd=str(FLOW_RUNNER.parent)).returncode
    if code == 0:
        _report_changes(run_dir, json.loads(frames.read_text())["frames"])
    return code


# --- voice -----------------------------------------------------------------

def cmd_voice(args) -> int:
    """
    Narrate every beat that has no audio yet, via ElevenLabs.

    --limit N does only the first N beats (a cheap check before a full
    script), and --force redoes clips that already exist.
    """
    from modules import voice_generator

    run_dir = resolve_run(args.run)
    beats = load_script(run_dir)["beats"]
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    todo = list(enumerate(beats, start=1))
    if args.limit:
        todo = todo[: args.limit]
    if not args.force:
        todo = [(i, b) for i, b in todo if not find_audio(run_dir, i)]

    # Batch consecutive beats into one request so they are one performance and
    # therefore consistent with each other. Only English: the ru/es path uses
    # text_to_speech, which has request stitching and does not need this.
    size = 1 if args.lang != "en" else max(1, config.ELEVENLABS_BATCH_SIZE)

    # The ~2000 character API ceiling is what actually binds, and beat length
    # is bimodal now (see config.ELEVENLABS_BATCH_CHARS), so group by
    # characters and treat the beat count as a cap on top of that.
    budget = max(1, getattr(config, "ELEVENLABS_BATCH_CHARS", 1400))

    def fill(run: list, cap: int) -> list[list]:
        """Greedy fill of one contiguous run, respecting both caps."""
        out: list[list] = []
        chars = 0
        for index, beat in run:
            size_of = len(beat["narration"])
            if out and len(out[-1]) < cap and chars + size_of <= budget:
                out[-1].append((index, beat))
                chars += size_of
            else:
                out.append([(index, beat)])
                chars = size_of
        return out

    # Only group beats that are actually adjacent: --limit and --force can
    # leave holes, and a batch spanning a hole would be performed as continuous
    # speech that is not continuous in the video.
    runs: list[list] = []
    for index, beat in todo:
        if runs and runs[-1][-1][0] == index - 1:
            runs[-1].append((index, beat))
        else:
            runs.append([(index, beat)])

    # Balance each run instead of filling greedily to the cap, because a
    # straight greedy fill leaves a remainder: 55 beats at 18 gives 18/18/18/1,
    # and a group of ONE skips the batch path entirely (len(group) > 1 below).
    # That beat then becomes its own performance and drifts from the other 54 -
    # precisely what batching exists to prevent. Splitting the same run into
    # equal groups gives 14/14/14/13 for the same number of requests.
    groups: list[list] = []
    for run in runs:
        needed = len(fill(run, size))
        even = -(-len(run) // needed) if needed else size
        groups.extend(fill(run, even))

    if size > 1:
        biggest = max((sum(len(b["narration"]) for _, b in g) for g in groups),
                      default=0)
        print(f"[voice] {len(todo)} beat(s) in {len(groups)} request(s), "
              f"up to {size} per request / {budget} chars "
              f"(largest {biggest})")

    failures = []
    for group in groups:
        indices = [i for i, _ in group]

        if len(group) > 1:
            try:
                made = voice_generator.generate_batch(
                    [b["narration"] for _, b in group], indices,
                    audio_dir, voice=args.voice)
                for index, (path, duration) in zip(indices, made):
                    print(f"  [voice] {index:03} -> {path.name} "
                          f"({duration:.2f}s)")
                continue
            except Exception as exc:
                # Never let a batching problem cost a whole overnight run.
                print(f"  [voice] batch {indices[0]}-{indices[-1]} failed "
                      f"({type(exc).__name__}: {exc})")
                print(f"  [voice] falling back to one request per beat")

        for index, beat in group:
            try:
                path, duration = voice_generator.generate(
                    beat["narration"], index, audio_dir,
                    voice=args.voice, lang=args.lang)
                print(f"  [voice] {index:03} -> {path.name} ({duration:.2f}s)")
            except Exception as exc:
                print(f"  [voice] {index:03} FAILED: "
                      f"{type(exc).__name__}: {exc}")
                failures.append(index)

    if failures:
        print(f"\n{len(failures)} beat(s) failed: "
              f"{','.join(str(n) for n in failures)}")
        return 1
    print(f"\nNext:  python pipeline.py manifest")
    return 0


# --- check -----------------------------------------------------------------

def cmd_check(args) -> int:
    """Report missing or stale images and missing audio. Changes nothing."""
    run_dir = resolve_run(args.run)
    data = load_script(run_dir)
    beats = data["beats"]
    frames = build_frames(data)

    # Frames are named in --only's own terms (beat.frame), so the fix line
    # below can be pasted straight back in.
    missing_images, stale = [], []
    for f in frames:
        path = find_frame(run_dir, f["name"])
        if path is None:
            missing_images.append(f"{f['beat']}.{f['frame']}")
            continue
        parent = find_frame(run_dir, f["parent"]) if f["parent"] else None
        if parent and parent.stat().st_mtime > path.stat().st_mtime:
            stale.append(f"{f['beat']}.{f['frame']}")
    missing_audio = [i for i in range(1, len(beats) + 1)
                     if find_audio(run_dir, i) is None]

    have_i = len(frames) - len(missing_images)
    have_a = len(beats) - len(missing_audio)
    print(f"\nrun     : {run_dir.name}")
    print(f"beats   : {len(beats)}")
    print(f"images  : {have_i}/{len(frames)} frames")
    print(f"audio   : {have_a}/{len(beats)}")
    _report_music(run_dir, data)
    _report_sfx(run_dir, data)

    def summarise(label, missing, fix):
        if not missing:
            return True
        shown = ",".join(str(n) for n in missing[:15])
        more = f" (+{len(missing) - 15} more)" if len(missing) > 15 else ""
        print(f"\nmissing {label}: {shown}{more}")
        print(f"  {fix}")
        return False

    if len(missing_images) < len(frames):
        _report_changes(run_dir, frames)
    ok = summarise("images", missing_images, "python pipeline.py images")
    # An edit older than the frame it was made from shows the old version of
    # that frame. `images` redoes these by itself; this only says why it will.
    ok &= summarise("images (edited from a frame that has since changed)",
                    stale, "python pipeline.py images")
    ok &= summarise("audio", missing_audio, "python pipeline.py voice")

    if ok:
        print("\nEverything present. Next: python pipeline.py manifest")
    return 0 if ok else 1


def _report_music(run_dir: Path, data: dict) -> None:
    """Print the mood music plan: when each piece starts, once timings exist."""
    moods = music_moods(data)
    if not moods:
        return
    from modules import video_editor
    manifest = run_dir / "manifest.json"
    if not manifest.exists():
        print("music   : " + ", ".join(f"{loc} = {m}" for loc, m in moods.items()))
        return
    plan = video_editor.mood_plan(json.loads(manifest.read_text()), moods, run_dir.name)
    print(f"music   : {len(plan)} section(s)")
    for sec in plan:
        name = sec["piece"].name if sec["piece"] else "-"
        print(f"  {_fmt(sec['start']):>7}  {sec['mood']:9} {name:22} "
              f"{', '.join(sec['locations'])}")
    if len(plan) - 1 > config.MUSIC_MAX_SWITCHES:
        print(f"  WARNING: {len(plan) - 1} music switches, more than "
              f"{config.MUSIC_MAX_SWITCHES} tends to feel jumpy")


def _report_sfx(run_dir: Path, data: dict) -> None:
    """
    Print every tagged sentence, so the tags can be approved or struck by
    hand before rendering. Once a manifest exists, also when each sound plays
    and which file it got.
    """
    tags = sfx_plan(data, warn=True)
    if not tags:
        return
    print(f"sfx     : {len(tags)} tagged beat(s)")
    for i, tag in tags.items():
        kind = "after" if tag in config.SFX_AFTER_TAGS else "picture"
        line = transcriber.strip_tags(data["beats"][i - 1]["narration"])
        print(f"  {i:3}  {tag:9} {kind:7}  {line[:70]}")

    manifest = run_dir / "manifest.json"
    if not manifest.exists():
        return
    from modules import video_editor
    entries = json.loads(manifest.read_text())
    starts, _ = video_editor._beat_starts(entries)
    placed = [(start + s["at"], s) for start, e in zip(starts, entries)
              for s in e.get("sfx") or []]
    if placed:
        print(f"  in manifest.json, {len(placed)} sound(s) incl. transitions/outro:")
        for when, s in placed:
            print(f"  {_fmt(when):>7}  {s['tag']:10} {s['file']}")


# --- Frame timing ------------------------------------------------------------
#
# A beat's frames used to share its time evenly, so a sign could appear before
# the narrator got to it. An edit can now name its word ({"at": "six meters"}),
# and the picture changes as that word is spoken. Whisper finds WHEN each word
# is said (modules/transcriber.py); the words themselves come from the script.

WORD_TIMES_FILE = "word_times.json"


def _word_key(word: str) -> str:
    return re.sub(r"[^a-z0-9]", "", word.lower())


def _find_phrase(keys: list[str], phrase: str, start: int = 0) -> int:
    """Index of `phrase` in the word keys at or after `start`, or -1."""
    want = [_word_key(w) for w in phrase.split() if _word_key(w)]
    if not want:
        return -1
    for i in range(start, len(keys) - len(want) + 1):
        if keys[i:i + len(want)] == want:
            return i
    return -1


def _word_times(narration: str, audio: Path, cache: dict) -> list[dict]:
    """The beat's words with start/end seconds, cached per audio clip."""
    size = audio.stat().st_size
    hit = cache.get(audio.name)
    if hit and hit.get("size") == size and hit.get("narration") == narration:
        return hit["words"]
    words = transcriber.align(narration, audio)
    cache[audio.name] = {"size": size, "narration": narration, "words": words}
    return words


def _frame_starts(frames: list[dict], words: list[dict],
                  duration: float) -> list[float] | None:
    """
    When each of a beat's frames starts, in seconds from the beat's start.

    None means "split evenly", which is what happens when nothing is timed, a
    word cannot be found, or two words sit so close that a frame would flash
    by in under config.MIN_FRAME_SECONDS. The first frame always starts with
    the beat. A frame with no word of its own shares the gap between its
    timed neighbours.
    """
    if len(frames) < 2 or not words or not any(f.get("at") for f in frames[1:]):
        return None
    keys = [_word_key(w["w"]) for w in words]
    starts: list[float | None] = [0.0] + [None] * (len(frames) - 1)
    pos = 0
    for k, f in enumerate(frames[1:], 1):
        if f.get("at"):
            i = _find_phrase(keys, f["at"], pos)
            if i < 0:
                return None
            starts[k], pos = words[i]["s"], i + 1

    starts.append(duration)                   # sentinel for the last gap
    k = 1
    while k < len(frames):
        if starts[k] is None:
            j = k
            while starts[j] is None:
                j += 1
            lo, hi = starts[k - 1], starts[j]
            for m in range(k, j):
                starts[m] = lo + (hi - lo) * (m - k + 1) / (j - k + 1)
            k = j
        k += 1
    gaps = [b - a for a, b in zip(starts, starts[1:])]
    starts.pop()
    if min(gaps) < config.MIN_FRAME_SECONDS:
        return None
    return [round(x, 3) for x in starts]


# --- Change check --------------------------------------------------------------
#
# Every edit compared with the frame it was made from. Pixel arithmetic, no AI:
# both are shrunk and blurred (so JPEG grain does not count), and a pixel counts
# as changed when any colour channel moved by 48+ out of 255. Colour, not just
# brightness, because a gold tag turning grey barely changes brightness.

def _frame_changes(run_dir: Path, frames: list[dict]):
    """(ignored, big): [(frame id, fraction changed)] past either threshold."""
    from PIL import Image, ImageChops, ImageFilter
    w, h = 192, 108

    def load(name):
        path = find_frame(run_dir, name)
        if path is None:
            return None
        return (Image.open(path).convert("RGB").resize((w, h), Image.BILINEAR)
                .filter(ImageFilter.GaussianBlur(1)))

    ignored, big = [], []
    for f in frames:
        if f["mode"] != "edit":
            continue
        before, after = load(f["parent"]), load(f["name"])
        if before is None or after is None:
            continue
        r, g, b = ImageChops.difference(before, after).split()
        diff = ImageChops.lighter(ImageChops.lighter(r, g), b)
        changed = sum(diff.histogram()[48:]) / (w * h)
        fid = f"{f['beat']}.{f['frame']}"
        if changed < config.CHANGE_MIN_FRACTION:
            ignored.append((fid, changed))
        elif changed > config.CHANGE_MAX_FRACTION:
            big.append((fid, changed))
    return ignored, big


def _report_changes(run_dir: Path, frames: list[dict]) -> None:
    ignored, big = _frame_changes(run_dir, frames)
    if ignored:
        ids = ",".join(i for i, _ in ignored)
        print(f"[check] {len(ignored)} edit(s) came back nearly identical to the "
              f"frame before - the image model ignored them: {ids}")
        print(f"        redo: python pipeline.py images --only {ids} "
              f"--run {run_dir.name}")
        print("        (a redo also remakes the edits after it in that location;"
              " if one is ignored again, reword it in script.json)")
    if big:
        shown = ", ".join(f"{i} ({c:.0%})" for i, c in big)
        print(f"[check] {len(big)} edit(s) changed over "
              f"{config.CHANGE_MAX_FRACTION:.0%} of the picture, worth a look: "
              f"{shown}")
        print("        fine if the edit asked for a big change; redo with --only "
              "if everything moved")
    if not ignored and not big:
        print("[check] every edit changed something, and none redrew the whole "
              "picture")


# --- manifest --------------------------------------------------------------

def _audio_duration(path: Path) -> float:
    """Read real duration with ffprobe; it handles mp3/wav/m4a alike."""
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def _make_silence(path: Path, seconds: float) -> None:
    subprocess.run(
        ["ffmpeg", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", str(seconds), "-q:a", "9", "-y", str(path)],
        capture_output=True, check=True,
    )


def _outro_assets() -> tuple[Path, Path] | None:
    """
    The cached outro image and voice line, generating them if missing.

    Made once and reused by every video: identical wording, voice and card on
    every upload, and no API calls after the first run. Returns None if the
    voice line cannot be produced, so a failure here never blocks a render.
    """
    config.OUTRO_DIR.mkdir(parents=True, exist_ok=True)

    image = next((p for p in sorted(config.OUTRO_DIR.iterdir())
                  if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")), None)
    if image is None:
        # Fall back to the character reference so this works out of the box.
        # Drop a purpose-made card in assets/outro/ to replace it.
        image = next((p for p in sorted(config.REFERENCE_DIR.iterdir())
                      if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")),
                     None) if config.REFERENCE_DIR.exists() else None
        if image is None:
            print("[outro] no image available, skipping outro")
            return None
        print(f"[outro] using {image.name} as the card "
              f"(put your own in {config.OUTRO_DIR.name}/ to replace it)")

    audio = config.OUTRO_DIR / "outro.mp3"
    if not audio.exists():
        from modules import voice_generator
        print("[outro] generating the voice line once (cached from now on)")
        try:
            made, _ = voice_generator.generate(config.OUTRO_LINE, 0, config.OUTRO_DIR)
            made.replace(audio)
        except Exception as exc:
            print(f"[outro] voice failed ({type(exc).__name__}), skipping outro")
            return None

    return image, audio


def _video_seconds(entries: list[dict]) -> float:
    """
    The finished video's length, from the manifest. Mirrors totalFrames in
    remotion/src/constants.ts.

    A dissolve does NOT shorten the video: its beat carries a dissolve-length
    tail that the overlap consumes, so the two cancel. A hard cut's pad has no
    overlap to absorb it, so every hard cut adds CUT_PAD_SECONDS. Leaving the
    pads out reported a 75-beat video ~8s shorter than it rendered.
    """
    def hard_cut(a: dict, b: dict) -> bool:
        same = bool(a.get("location")) and a.get("location") == b.get("location")
        return same and not b.get("redraw")

    cuts = sum(1 for a, b in zip(entries, entries[1:]) if hard_cut(a, b))
    return (sum(e["duration"] for e in entries)
            + cuts * config.CUT_PAD_SECONDS + OUTRO_HOLD_SECONDS)


def cmd_manifest(args) -> int:
    """
    Pair every beat's pictures with its narration clip into manifest.json.

    Measures each clip's real duration, times picture changes to their "at"
    words, and appends the outro beat. Remotion renders from this file alone.
    """
    run_dir = resolve_run(args.run)
    data = load_script(run_dir)
    beats = data["beats"]
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    by_beat: dict[int, list[dict]] = {}
    for f in build_frames(data):
        by_beat.setdefault(f["beat"], []).append(f)
    redraws = _redraw_beats(beats)

    times_path = run_dir / WORD_TIMES_FILE
    try:
        word_cache = json.loads(times_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        word_cache = {}
    timed = untimed = 0

    entries, missing = [], []
    for index, beat in enumerate(beats, start=1):
        images = [find_frame(run_dir, f["name"]) for f in by_beat.get(index, [])]
        if None in images:
            missing.append(index)
            continue
        if not images:
            # A hold beat: the last picture of the beat before stays up. The
            # boundary is a hard cut between two identical images, so it is
            # invisible.
            if not entries:
                missing.append(index)
                continue
            images = [run_dir / entries[-1]["frames"][-1]]
        image = images[0]

        audio = find_audio(run_dir, index)
        if audio is None:
            if not args.silent:
                missing.append(index)
                continue
            # Test path: silent track of a fixed length, so a render can be
            # proven end to end from images alone, before ElevenLabs works.
            audio = audio_dir / f"{audio_name(index)}.mp3"
            _make_silence(audio, args.silent)
            duration = args.silent
        else:
            duration = _audio_duration(audio)

        # Emotion tags are delivery instructions for ElevenLabs. They are never
        # spoken, so they must never be rendered as subtitle text either.
        spoken = transcriber.strip_tags(beat["narration"])

        entry = {
            "index": index,
            "narration": spoken,
            # Paths are relative to run_dir, which Remotion gets as --public-dir.
            "image": f"images/{image.name}",
            # Every frame of the beat, first included, hard cut between them.
            # frame_starts (below) times them to their words; without it the
            # render splits the beat evenly.
            "frames": [f"images/{p.name}" for p in images],
            "audio": f"audio/{audio.name}",
            "duration": round(duration, 3),
            # Carried so the render can tell a cut WITHIN a place from a move
            # BETWEEN places: same location cuts hard, a change dissolves.
            # See remotion/src/compositions/LectureVideo.tsx.
            "location": " ".join((beat.get("location") or "").split()),
        }
        # A fresh picture mid-location dissolves in rather than jumping.
        if index in redraws:
            entry["redraw"] = True

        frames = by_beat.get(index, [])
        if not args.silent and any(f.get("at") for f in frames[1:]):
            starts = _frame_starts(
                frames, _word_times(beat["narration"], audio, word_cache), duration)
            if starts:
                entry["frame_starts"] = starts
                timed += 1
            else:
                untimed += 1


        entries.append(entry)

    if missing:
        shown = ",".join(str(n) for n in missing[:15])
        more = f" (+{len(missing) - 15} more)" if len(missing) > 15 else ""
        print(f"Missing assets for beat(s): {shown}{more}")
        print("Run `python pipeline.py check` for detail, or pass --silent 5")
        print("to build a picture-only manifest for a render test.")
        return 1

    # Appended as an ordinary beat, so it cuts or dissolves in like any other.
    # The script never mentions the channel (pass1_narration.txt bans it), so
    # the outro is added here instead.
    fmt = data.get("format", "").strip().lower()
    if (config.OUTRO_ENABLED and fmt not in config.NO_OUTRO_FORMATS
            and not args.silent):
        assets = _outro_assets()
        if assets:
            image_src, audio_src = assets
            out_image = run_dir / "images" / f"outro{image_src.suffix.lower()}"
            out_audio = run_dir / "audio" / "outro.mp3"
            shutil.copy(image_src, out_image)
            shutil.copy(audio_src, out_audio)

            entry = {
                "index": len(entries) + 1,
                "narration": transcriber.strip_tags(config.OUTRO_LINE),
                "image": f"images/{out_image.name}",
                "audio": f"audio/{out_audio.name}",
                "duration": round(_audio_duration(out_audio), 3),
            }
            entries.append(entry)
            print(f"[manifest] + outro beat ({entry['duration']:.1f}s)")

    if not args.silent:
        placed = _place_sfx(entries, beats, sfx_plan(data), run_dir.name)
        if placed:
            print(f"[manifest] {placed} sound effect(s) placed "
                  f"(see `python pipeline.py check`)")

    if word_cache:
        times_path.write_text(json.dumps(word_cache, indent=1), encoding="utf-8")
    if timed or untimed:
        print(f"[manifest] pictures timed to their words in {timed} beat(s)"
              + (f", {untimed} fell back to an even split (word not heard, or "
                 f"two changes under {config.MIN_FRAME_SECONDS}s apart)"
                 if untimed else ""))

    path = run_dir / "manifest.json"
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    total = _video_seconds(entries)
    print(f"[manifest] {len(entries)} beats -> {path}")
    print(f"[manifest] final video {total:.1f}s ({total / 60:.1f} min)")
    if args.silent:
        print(f"[manifest] SILENT placeholder audio at {args.silent}s per beat")
    print(f"\nNext:  python pipeline.py render")
    return 0


# --- demo ------------------------------------------------------------------
#
# A full dry run: script, images and audio all fabricated locally so the video
# can be watched end to end without touching Flow or ElevenLabs. Exists to test
# the things that are easy to get wrong and expensive to discover late -
# frame timing, framing, cuts and dissolves, and whether image N really is
# paired with narration N.

DEMO_NARRATION = [
    "He had heard the stories about humanity's strongest soldier, but nobody mentioned how short the man was.",
    "[surprised] The alley was narrow and grey, and neither of them seemed willing to speak first about it.",
    "Somewhere above them the wall blocked out most of the sky, throwing a long cold shadow down.",
    "He wondered whether saying nothing at all was somehow worse than saying something extremely stupid right now.",
    "[laughs] The shorter man finally sighed, adjusted his blades, and muttered something about wasting valuable daylight.",
    "They walked together past shuttered windows and red tile roofs without exchanging a single further word.",
    "The cobblestones were uneven enough that looking down felt safer than looking at each other directly.",
    "He decided that humanity's strongest was probably just as tired as everybody else in this town.",
    "[whispers] Behind them the enormous wall kept doing the only thing it had ever really done.",
    "Neither of them mentioned it again, and that felt like the closest thing to friendship available.",
]


def _demo_image(path: Path, index: int, total: int, caption: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    # Distinct hue per beat: if two adjacent beats swap, the colour change makes
    # it obvious on screen even before you read the number.
    r, g, b = colorsys.hsv_to_rgb((index / max(1, total)) % 1.0, 0.55, 0.75)
    bg = (int(r * 255), int(g * 255), int(b * 255))

    img = Image.new("RGB", (config.WIDTH, config.HEIGHT), bg)
    draw = ImageDraw.Draw(img)

    def font(size: int):
        for name in ("/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                     "/System/Library/Fonts/Helvetica.ttc"):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                continue
        return ImageFont.load_default()

    number = f"{index:02}"
    big = font(460)
    box = draw.textbbox((0, 0), number, font=big)
    draw.text((config.WIDTH / 2 - (box[2] - box[0]) / 2,
               config.HEIGHT / 2 - (box[3] - box[1]) / 2 - 60),
              number, fill=(255, 255, 255), font=big)

    small = font(46)
    label = f"beat {index} of {total} - {caption[:52]}"
    box = draw.textbbox((0, 0), label, font=small)
    draw.text((config.WIDTH / 2 - (box[2] - box[0]) / 2, config.HEIGHT - 170),
              label, fill=(20, 20, 20), font=small)

    # Corner marks make any crop visible: the frame is static now, so all
    # four should sit fully on screen for the whole beat.
    for x, y in ((60, 60), (config.WIDTH - 160, 60),
                 (60, config.HEIGHT - 160), (config.WIDTH - 160, config.HEIGHT - 160)):
        draw.rectangle([x, y, x + 100, y + 100], outline=(255, 255, 255), width=8)

    img.save(path)


def cmd_demo(args) -> int:
    slug = args.run or "_demo"
    run_dir = config.OUTPUT_DIR / slug
    (run_dir / "images").mkdir(parents=True, exist_ok=True)
    (run_dir / "audio").mkdir(parents=True, exist_ok=True)

    count = args.beats
    beats = []
    for i in range(count):
        narration = DEMO_NARRATION[i % len(DEMO_NARRATION)]
        beats.append({"narration": narration,
                      "image_prompt": f"placeholder for beat {i + 1}"})
    (run_dir / "script.json").write_text(
        json.dumps({"topic": slug, "beats": beats}, indent=2), encoding="utf-8")

    # Real photos if you point at a folder, generated cards otherwise.
    supplied = []
    if args.images:
        src = Path(args.images)
        supplied = sorted(p for p in src.iterdir()
                          if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"))
        if not supplied:
            raise SystemExit(f"No images found in {src}")
        print(f"[demo] using {len(supplied)} image(s) from {src}")

    for i, beat in enumerate(beats, start=1):
        if supplied:
            src = supplied[(i - 1) % len(supplied)]
            shutil.copy(src, run_dir / "images" / f"scene_{i:03}{src.suffix.lower()}")
        else:
            _demo_image(run_dir / "images" / f"scene_{i:03}.png", i, count,
                        beat["narration"])

    # Silence, but sized per beat from its own word count rather than a flat
    # number. Uniform durations would hide exactly the timing problems this is
    # meant to expose.
    #
    # Uses the same measured words-per-minute the length estimator does, so a
    # demo render comes out the length a real run of the same script would.
    for i, beat in enumerate(beats, start=1):
        words = len(re.sub(r"\[[^\]]*\]", " ", beat["narration"]).split())
        seconds = round(
            words / config.WORDS_PER_MINUTE * 60 / config.NARRATION_SPEED, 2)
        _make_silence(run_dir / "audio" / f"beat_{i:03}.mp3", seconds)

    print(f"[demo] {count} beats -> {run_dir}")
    print("[demo] images are numbered: beat N must show the number N")
    args.run, args.silent = slug, None
    cmd_manifest(args)
    print(f"\nWatch it with:  python pipeline.py render --run {slug}")
    return 0


# --- render ----------------------------------------------------------------

def cmd_render(args) -> int:
    """Render manifest.json to final.mp4 with Remotion, then mix in music."""
    from modules import video_editor

    run_dir = resolve_run(args.run)
    manifest = run_dir / "manifest.json"
    if not manifest.exists():
        raise SystemExit(f"No manifest.json in {run_dir}. Run: pipeline.py manifest")

    moods = music_moods(load_script(run_dir))
    final = video_editor.render(manifest, run_dir, moods=moods)
    print(f"[render] done -> {final}")
    return 0


# --- all -------------------------------------------------------------------

def _fmt(seconds: float) -> str:
    """Seconds as m:ss, since a full run is minutes not seconds."""
    return f"{int(seconds) // 60}m {int(seconds) % 60:02d}s"


def cmd_all(args) -> int:
    """
    Everything, in order, for one run folder. This is what bare
    `python pipeline.py` does - paste your JSON, hit Run, walk away.

    Safe to re-run: every stage skips work that already exists, so if this
    dies at image 20 the next run picks up at image 20 rather than starting
    from scratch.

    A Chrome window WILL appear during the image stage and drive itself. That
    is by design - headless Chrome is trivially detected - and needs nothing
    from you beyond leaving it alone.
    """
    # A pasted script wins over "most recent", so hitting Run right after
    # pasting always works on what you just pasted.
    if not args.run:
        args.run = adopt_pasted_script()

    run_dir = resolve_run(args.run)
    args.run = run_dir.name              # resolve once, so stages stay quiet

    stages = [
        ("prompts", cmd_prompts),
        ("images", cmd_images),
        ("voice", cmd_voice),
        ("manifest", cmd_manifest),
        ("render", cmd_render),
    ]

    started = time.monotonic()
    timings = []

    for i, (name, func) in enumerate(stages, start=1):
        print(f"\n{'=' * 60}\n[{i}/{len(stages)}] {name}\n{'=' * 60}")
        stage_started = time.monotonic()
        code = func(args)
        timings.append((name, time.monotonic() - stage_started))
        if code:
            print(f"\nStopped at '{name}'. Fix the above, then run again - "
                  f"finished work is kept and will be skipped.")
            return code

    total = time.monotonic() - started
    print(f"\n{'=' * 60}")
    print(f"DONE -> {run_dir / 'final.mp4'}")
    print(f"{'=' * 60}")
    for name, seconds in timings:
        share = seconds / total * 100 if total else 0
        print(f"  {name:<9} {_fmt(seconds):>9}  {share:4.0f}%")
    print(f"  {'TOTAL':<9} {_fmt(total):>9}")
    print("=" * 60)
    print("Frames to review:")
    _report_changes(run_dir, build_frames(load_script(run_dir)))
    return 0


# --- CLI -------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # No subcommand means "do everything", so hitting Run in PyCharm with no
    # arguments does the whole video.
    parser.add_argument("--run", default=None,
                        help="run slug (default: most recent). Works before or "
                             "after the subcommand.")
    parser.set_defaults(func=cmd_all, only=None, limit=None,
                        force=False, lang="en", silent=None,
                        voice=config.ELEVENLABS_DEFAULT_VOICE)
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("init", help="create a run folder + script.json template")
    p.add_argument("slug")
    p.set_defaults(func=cmd_init)

    def with_run(name, help_text, func):
        sp = sub.add_parser(name, help=help_text)
        # SUPPRESS, not None: without it the subparser's default would clobber
        # a --run given BEFORE the subcommand.
        sp.add_argument("--run", default=argparse.SUPPRESS,
                        help="run slug (default: most recent)")
        sp.set_defaults(func=func)
        return sp

    with_run("prompts", "script.json -> frames.json", cmd_prompts)

    sp = with_run("images", "generate images via Flow", cmd_images)
    sp.add_argument("--only", help="beats (12) or single frames (12.2), "
                    "comma-separated. Later edits in the same chain are redone too.")

    sp = with_run("voice", "narration via ElevenLabs", cmd_voice)
    sp.add_argument("--limit", type=int, help="only the first N beats")
    sp.add_argument("--force", action="store_true", help="redo existing clips")
    sp.add_argument("--voice", default=config.ELEVENLABS_DEFAULT_VOICE,
                    choices=sorted(config.ELEVENLABS_VOICES))
    sp.add_argument("--lang", default="en",
                    help="ru/es route through multilingual_v2 instead of v4")

    with_run("check", "report what is present and what is missing", cmd_check)

    sp = with_run("manifest", "pair images+audio, measure durations", cmd_manifest)
    sp.add_argument("--silent", type=float, metavar="SECONDS",
                    help="fabricate silent audio of this length for beats that "
                         "have none, so a render can be tested from images alone")

    sp = with_run("demo", "fabricate a whole run locally to test the video",
                  cmd_demo)
    sp.add_argument("--beats", type=int, default=10)
    sp.add_argument("--images", metavar="DIR",
                    help="use your own photos instead of numbered cards")

    sp = with_run("all", "every stage in order (same as no subcommand)", cmd_all)
    sp.set_defaults(only=None, limit=None, force=False, lang="en", silent=None, voice=config.ELEVENLABS_DEFAULT_VOICE)

    with_run("render", "Remotion -> final.mp4", cmd_render)

    args = parser.parse_args()
    prevent_sleep()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
