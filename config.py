"""
Central config for the AI Lecture Pipeline.

Every tunable constant lives here (pacing, zoom range, crossfade length,
model names, directories) so modules never hardcode them. Change behavior
here, not inside the stage modules.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Directories -----------------------------------------------------------
ROOT_DIR = Path(__file__).parent
ASSETS_DIR = ROOT_DIR / "assets"
REFERENCE_DIR = ASSETS_DIR / "reference"          # hand-drawn character/env art
OUTPUT_DIR = ROOT_DIR / "output"                  # one subfolder per run
REMOTION_DIR = ROOT_DIR / "remotion"              # the React/TS render project

# --- API keys (loaded from .env) -------------------------------------------
# GEMINI_API_KEY is unused by every shipped stage - images come from Google
# Flow through flow_runner/, which authenticates with a browser login, not a
# key. It is read here only for the unbuilt consistency pass (CONSISTENCY_MODEL
# below), so leaving it blank in .env costs nothing today.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# --- Visual style ----------------------------------------------------------
# THE style. Appended verbatim to every image prompt by pipeline.py, so it is
# byte-identical on every scene of every video, whatever the topic.
#
# It lives here, not in script.json, because anything an LLM writes it will
# eventually paraphrase - and a paraphrased style block is a different style.
# Claude writes the SCENE; this writes the LOOK.
#
# Two rules if you edit it, both from Google's Nano Banana guidance:
#   1. Positive framing only. "no shading" puts shading in front of the model
#      and asks it not to draw it. Say what the surface IS instead.
#   2. Do NOT describe the reference character here. The attached reference art
#      already defines him, and re-describing him competes with it - excessive
#      character detail in the prompt measurably REDUCES consistency.
# Declared BEFORE the scene as well as after it. This matters: the style block
# alone sits at the end of a ~750 character prompt, so the model reads hundreds
# of words of realistic scene description before being told the medium. Naming
# the medium in the first few words makes it commit up front.
#
# The failure this fixes: "a stone wall covered in carved wooden name plaques,
# hundreds of them" is a real-world photographic subject, and Nano Banana 2
# grounds real subjects against real images. It returned an actual photograph
# with the character pasted on top.
# Phrased as a DIRECTIVE, not a noun phrase. "A crude flat MS Paint doodle
# drawing." reads as a thing to depict, and the model duly depicted it: a
# scribbled "CRUDE MS PAINT ADVENTURE" title card in one scene, and MS Paint's
# own dashed selection marquee and canvas border in another. "Drawn in X style"
# cannot be read as content.
STYLE_PREFIX = "Drawn crudely in flat MS Paint doodle style."


# The two negative clauses are load-bearing, both added after real failures:
#   - The scribble clause has to cover EVERYTHING, and it has to be separate
#     from the do-not-invent-lettering clause. Narrowing it to "a sign or a
#     written notice" (an attempt to stop invented title cards) quietly
#     excluded notebooks and TV screens, and those came back full of confident
#     misspelled English: "THE VOID IS WATCHING", "study for for quiz". Both
#     jobs are now stated separately: all writing is scribble, AND nothing
#     unrequested gets added.
#   - Naming a paint program invites the model to draw the program. Forbidding
#     the window furniture outright is what stops the dashed marquee and the
#     grey canvas border showing up around the picture.
#
# The edge-margin clause is the one rule here that is not driven by a bad
# generation - it is driven by the render. Ken Burns crops up to 10% off the
# frame (remotion/src/constants.ts), and the previous move was clamped down to
# an invisible 3% precisely because full-bleed art had no margin to give. This
# asks for the margin instead, so the camera can move. Phrased as what the
# composition IS, per rule 1 - "leave space at the edges" reads as an
# instruction about the canvas, not about where to put the subject.
STYLE_BLOCK = (
    "STYLE: crude MS Paint doodle, drawn shakily with a computer mouse. "
    "Thick wobbly black outlines of uneven weight. Flat bucket-filled colour, "
    "every shape a single uniform block with hard edges. Flat 2D composition. "
    "Any writing anywhere in the picture is wobbly unreadable scribble, never "
    "real letters or words: on signs, screens, pages, notebooks, labels and "
    "packaging alike. Never add a title, caption, watermark or any lettering "
    "the scene did not ask for. "
    "Never show an application window, toolbar, menu, canvas edge or dashed "
    "selection outline - the drawing fills the whole frame edge to edge. "
    "The main subject sits well inside the frame with clear space along all "
    "four edges. "
    "Childlike, amateur, deliberately badly drawn. 16:9 horizontal."
)

# --- Sleep prevention -------------------------------------------------------
# A full video can take over an hour of unattended generation, and a Mac that
# idles to sleep halfway through leaves the Chrome session dead. caffeinate is
# started for the life of the run and dies with it.
#
# NOTE: this cannot defeat CLOSING THE LID - macOS sleeps on lid close whatever
# caffeinate says, unless the Mac is on power with an external display. Leave
# the lid open.
PREVENT_SLEEP = True

# --- Music ------------------------------------------------------------------
# A single bed track reused by every video, mixed under the narration after
# Remotion renders. Drop one file in assets/music/ - the first audio file found
# is used. Generate it with the prompt in the session notes: flat energy, no
# swells, purely instrumental, mid range left clear for the voice.
MUSIC_ENABLED = True
MUSIC_DIR = ASSETS_DIR / "music"      # fallback bed, used if a run has no music

# Composed per video from the script's own "music_prompt", so a bleak what-if
# and a silly skit get different beds. Falls back to MUSIC_DIR when a script
# carries no music_prompt.
MUSIC_PER_VIDEO = True
MUSIC_MIN_SECONDS = 10.0
MUSIC_MAX_SECONDS = 300.0            # API ceiling; longer videos loop the bed
# How far BELOW the narration the bed sits, in dB. This is measured, not a
# fixed multiplier: the music is composed fresh per video so its loudness
# varies run to run, and a blind gain would land anywhere from "fighting the
# voice" to "inaudible". 18 dB is the usual range for a bed under speech.
# Lower the number to make music more present, raise it to push it back.
MUSIC_DUCK_DB = 18.0
MUSIC_VOLUME = 0.10          # fallback gain, only if loudness cannot be read
MUSIC_FADE_SECONDS = 2.0     # fade out over the outro so it does not stop dead

# --- Outro ------------------------------------------------------------------
# The subscribe/like card, appended as a final BEAT rather than a special
# component, so it inherits the crossfade, subtitles and timing for free.
#
# Both files are generated ONCE and cached here, then reused by every video:
# same wording, same voice, same image, so the channel ends consistently and it
# costs no API calls after the first run.
OUTRO_ENABLED = True
OUTRO_DIR = ASSETS_DIR / "outro"
OUTRO_LINE = "If you want more of these, subscribe and hit like."

# --- ElevenLabs ------------------------------------------------------------
# The US regional endpoint serves the good eleven_v3 render. The global default
# (api.elevenlabs.io) returns a flat/robotic voice on this account - it only
# matches the website when we hit this host. Confirmed by capturing the web
# app's own request. Do not "simplify" this back to the default base URL.
ELEVENLABS_BASE_URL = "https://api.us.elevenlabs.io"

# Loaded from .env rather than hardcoded: these are voice IDs from one
# specific ElevenLabs account, one of them a voice custom-designed for this
# channel. Keeping them out of source means the repo carries no identifiers
# tied to a real account. Format: comma-separated name:voice_id pairs, e.g.
#   ELEVENLABS_VOICES=narrator:abc123,sidekick:def456
def _parse_voice_map(raw: str) -> dict[str, str]:
    voices = {}
    for pair in raw.split(","):
        name, _, voice_id = pair.strip().partition(":")
        if name and voice_id:
            voices[name] = voice_id
    return voices


ELEVENLABS_VOICES = _parse_voice_map(os.getenv("ELEVENLABS_VOICES", ""))
ELEVENLABS_DEFAULT_VOICE = os.getenv("ELEVENLABS_DEFAULT_VOICE", next(iter(ELEVENLABS_VOICES), ""))

# English goes through text_to_dialogue + eleven_v3, which is what gives the
# lively read and supports inline emotion tags like [surprised]. ru/es fall back
# to multilingual_v2 via plain text_to_speech.
ELEVENLABS_MODEL_DIALOGUE = "eleven_v3"
ELEVENLABS_MODEL_MULTILINGUAL = "eleven_multilingual_v2"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_192"
ELEVENLABS_STABILITY = 0.5

# How many beats go into ONE eleven_v3 request.
#
# This is the consistency fix. eleven_v3 is not deterministic and is excluded
# from ElevenLabs' request-stitching feature, so there is no way to tell one
# request what the previous one sounded like. Beats generated separately are
# separate performances and they drift.
#
# Beats sent together are ONE performance, so they match by construction. The
# reply carries voice_segments, which say exactly where each beat starts and
# ends, and the batch audio is cut back into per-beat files on those bounds.
#
# HARD CEILING: ElevenLabs documents ~2000 characters per text_to_dialogue
# request. That ceiling is measured in CHARACTERS, so characters are what the
# batcher counts - a beat count was only ever a proxy for it.
#
# The proxy broke with the two-tier rhythm. Beat length used to be uniform at
# ~105 characters, so "10 beats" reliably meant ~1050. Now beats are bimodal:
# a short beat is ~35 characters and a long one ~85, so the same 10 beats is
# anywhere from 350 to 850 - and a batch of long beats could approach the
# ceiling while a batch of short ones wastes most of the request.
#
# So ELEVENLABS_BATCH_CHARS is the real limit and BATCH_SIZE is just a safety
# cap on top of it. 1400 leaves headroom under the documented 2000 for the
# per-line overhead the dialogue endpoint adds, and sits far above the ~250
# ElevenLabs suggests for stable output.
#
# Bigger batches mean fewer seams, but a failed batch drops more beats onto
# the inconsistent per-beat fallback, and long single generations are what v3
# is least reliable at. At the new ~52 characters a beat, 1400 works out to
# ~27 beats, so BATCH_SIZE 18 is what actually binds - roughly five requests
# for a 90-beat script, the same request count 45-beat scripts used to need.
#
# Set BATCH_SIZE to 1 to disable batching and restore one request per beat.
ELEVENLABS_BATCH_SIZE = 18
ELEVENLABS_BATCH_CHARS = 1400

# Post-generation speed-up via FFmpeg atempo. 1.0 disables it entirely and
# skips the re-encode. Valid range for one atempo pass is 0.5-2.0.
#
# Beat durations are measured AFTER this, so changing it changes how long every
# image stays on screen: at 1.0 a 35-word beat runs about thirteen seconds
# rather than ten, which means fewer images per video.
NARRATION_SPEED = 1.0

# --- Model names -----------------------------------------------------------
# The script is authored by hand (pasted into output/<slug>/script.json), so
# there is no script-generation model here, and images come from Google Flow
# via flow_runner/ rather than an API, so there is no image model either.
#
# This is reserved for the character-consistency pass described in the README,
# which is not built yet: score a generated image against the reference art and
# re-roll when it drifts off-model. Needs `google-genai` installed to use.
CONSISTENCY_MODEL = "gemini-2.5-flash"

# --- Narration rate --------------------------------------------------------
# Measured over 231 shipped beats across five finished videos: 4207 spoken
# words against 1425s of narration audio, which is tightly trimmed (no
# detectable silence at -30dB), so this is real delivery rate, not padding.
#
# Used in two places: estimating a script's finished length before anything is
# generated, and sanity-checking that a batched beat's audio is not far
# shorter than its text could possibly be spoken in.
WORDS_PER_MINUTE = 177

# --- Video / pacing --------------------------------------------------------
# What a script is aiming at, in seconds. Only used to sanity-check a script
# before any money is spent on it: pipeline.py estimates the finished length
# from the spoken word count and warns when it lands well off this.
#
# It is a target, not a constraint - nothing truncates a video to fit. Change
# it here AND change the total word budget in the prompt template, or the two
# will disagree and the warning will fire on every run.
TARGET_VIDEO_SECONDS = 180.0
TARGET_VIDEO_TOLERANCE = 0.15      # warn outside +/-15%

FPS = 30                                           # Remotion runs at 30fps
WIDTH = 1920                                        # 16:9
HEIGHT = 1080

# --- Ken Burns + transitions -----------------------------------------------
# ALL of these mirror remotion/src/constants.ts and are kept in sync BY HAND.
# Remotion is the one that actually renders; these exist so the Python side can
# predict a finished video's length without running a render. Change one, change
# the other, or the length estimate silently drifts from reality.
ZOOM_MIN = 1.0                    # start scale of a push in
ZOOM_MAX = 1.10                   # end scale (was 1.06, invisible at this pace)
PAN_SCALE = 1.06                  # fixed scale a pan holds
PAN_PERCENT = 2.5                 # travel, under the 2.83% ceiling for 1.06

# Two kinds of boundary now. Within a location beats hard cut; a change of
# location dissolves. A dissolve's tail is consumed by the overlap so it costs
# no timeline, but a hard cut's pad is real added length - which is why the
# estimate below has to count them.
DISSOLVE_SECONDS = 8 / 30         # 0.27s, only where the location changes
CUT_PAD_SECONDS = 4 / 30          # 0.13s breath between beats on a hard cut


