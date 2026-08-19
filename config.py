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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

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

ELEVENLABS_VOICES = {
    "animatoryoung": "xlnOCsItpCGtYrgUKVqx",   # designed for this channel
    "hamid": "yr43K8H5LoTp6S1QFSGg",
    "Molodoy": "YjESejviApN7SHrbfnA2",
    "spanish_guy": "nR2KQXVwn2zMK8FALNCh",
}
ELEVENLABS_DEFAULT_VOICE = "animatoryoung"

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
# request. At ~105 characters a beat that is about 18 beats, and 15 is the
# largest batch that still fits when the longest beats happen to land
# together. Do not raise this past 15 without re-measuring the script.
#
# Ten is the balance. It is ~1150 characters worst case, comfortably past the
# ~250 ElevenLabs suggests for stable output and comfortably under the
# ceiling, and it halves the number of seams versus five. Bigger batches mean
# fewer seams but a failed batch drops more beats onto the inconsistent
# per-beat fallback, and long single generations are what v3 is least
# reliable at.
#
# 1 disables batching and restores the old one-request-per-beat behaviour.
ELEVENLABS_BATCH_SIZE = 10

# Post-generation speed-up via FFmpeg atempo. 1.0 disables it entirely and
# skips the re-encode. Valid range for one atempo pass is 0.5-2.0.
#
# Beat durations are measured AFTER this, so changing it changes how long every
# image stays on screen: at 1.0 a 35-word beat runs about thirteen seconds
# rather than ten, which means fewer images per video.
NARRATION_SPEED = 1.0

# --- Model names -----------------------------------------------------------
# NOTE: the script is authored by hand (paste JSON into main.py), so there is
# no script-generation model here. These are only for image work.
IMAGE_MODEL = "gemini-2.5-flash-image"            # "Nano Banana"
CONSISTENCY_MODEL = "gemini-2.5-flash"            # future: scores image vs reference

# --- Video / pacing --------------------------------------------------------
FPS = 30                                           # Remotion runs at 30fps
WIDTH = 1920                                        # 16:9
HEIGHT = 1080

# --- Ken Burns + transitions -----------------------------------------------
ZOOM_MIN = 1.0                                      # start scale
ZOOM_MAX = 1.06                                     # end scale; mirrored in remotion/src/constants.ts
CROSSFADE_SECONDS = 0.5                             # overlap between beats


