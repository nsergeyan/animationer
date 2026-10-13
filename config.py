"""
Central config for the Animationer pipeline.

Every tunable constant lives here (pacing, cut and dissolve timing, the visual
style prompt, model names, directories) so modules never hardcode them. Change
behavior here, not inside the stage modules.
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
# THE style. Pasted at the FRONT of every image prompt by pipeline.py, so it is
# byte-identical on every scene of every video, whatever the topic.
#
# It lives here, not in script.json, because anything an LLM writes it will
# eventually paraphrase, and a paraphrased style block is a different style.
# Claude writes the SCENE; this writes the LOOK.
#
# POSITION: first, always. It used to be split in two - a one-line prefix at the
# front and this block at the end - because a style block sitting alone at the
# END of a ~750 character prompt meant the model read hundreds of words of
# realistic scene description before being told the medium, and by then it had
# committed. The failure that caused: "a stone wall covered in carved wooden
# name plaques, hundreds of them" is a real-world photographic subject, and Nano
# Banana grounds real subjects against real images. It returned an actual
# photograph with the character pasted on top.
#
# Putting the whole block first does that job on its own, so the separate prefix
# is gone. This only works while the block stays SHORT: 785 characters of style
# in front of the scene would bury the subject just as badly the other way
# round. If this ever grows back past ~500 characters, that tradeoff is back.
#
# Four rules if you edit it:
#   1. Positive framing only, from Google's Nano Banana guidance. "no shading"
#      puts shading in front of the model and asks it not to draw it. Say what
#      the surface IS instead - which is why flat colour is specified as "every
#      shape one uniform block with hard edges" and never as "no gradients".
#   2. Do NOT describe the reference character here. The attached reference art
#      already defines him, and re-describing him competes with it - excessive
#      character detail in the prompt measurably REDUCES consistency.
#   3. Phrase the medium as a DIRECTIVE, not a noun phrase. "A crude flat MS
#      Paint doodle drawing." reads as a thing to depict, and the model duly
#      depicted it: a scribbled "CRUDE MS PAINT ADVENTURE" title card in one
#      scene, MS Paint's own dashed selection marquee and canvas border in
#      another. "Drawn shakily with a mouse" cannot be read as content.
#   4. Keep it short. See POSITION above.
#
# Clause by clause, each earns its place:
#   - The scribble clause and the do-not-invent-lettering clause do two
#     different jobs and must stay separate. Narrowing the first to "a sign or
#     a written notice" (an attempt to stop invented title cards) quietly
#     excluded notebooks and TV screens, and those came back full of confident
#     misspelled English: "THE VOID IS WATCHING", "study for for quiz".
#   - Naming a paint program invites the model to draw the program. Forbidding
#     the window furniture outright is what stops the dashed marquee and the
#     grey canvas border showing up around the picture.
#   - The edge-margin clause ("clear of all four edges") was added for the old
#     Ken Burns camera move, which cropped up to 10% off the frame. Frames have
#     been static since 2026-10-11, so it no longer has a reason to exist. It
#     stays until its effect on framing is judged separately.
#   - "A simple picture: few objects, drawn large, plain background" is the
#     newest clause and the only one not driven by a generation failure. It is
#     driven by a measurement: across five shipped videos every frame carried
#     ~6 separately placed objects at ~0.5 seconds of screen time each, far
#     more than a viewer can read before the cut. Stated positively per rule 1.
#
# 2026-10-07: moved to a white-page look in the spirit of Casually Explained.
# No rooms at all: the character plus a few things on plain white, colour on
# one or two key objects only. Two deliberate openings, each scoped to "only
# where the scene asks" so the old defences still hold everywhere else:
#   - Quoted labels (1-3 words) for the joke. The scribble clause stays for
#     every other bit of writing, which is what stops invented misspelled text.
#   - A rare photo cutout of one object as a punchline. pass2 caps it at 1 beat
#     in 6 and pipeline.py warns past that, because photo wording is exactly
#     what used to drag whole frames photographic.
# 2026-10-11: "The only words on the page are the quoted ones". The first
# chained video came back with captions nobody wrote ("CHECO?!", "WOW! LEWIS
# HAMILTON!", "NEW CADDY"). The scribble clause above covers writing ON
# things, not the model narrating the scene in big letters of its own.
STYLE_BLOCK = (
    "Crude MS Paint doodle drawn shakily with a mouse on a plain white page. "
    "Thick wobbly black outlines, flat 2D, deliberately low-effort. People are "
    "simple doodle figures with big round eyes and exaggerated faces. Mostly "
    "black lines on white, with a flat bucket-fill colour on one or two key "
    "objects only. A few things, drawn large, floating on empty white. Words "
    "appear only where the scene quotes them, in wobbly hand-drawn capitals; "
    "all other writing is unreadable scribble. The only words on the page are "
    "the quoted ones: no captions, titles or exclamations of its own. A photo "
    "cutout appears only "
    "where the scene asks for one. No application window, toolbar or canvas "
    "edge. Keep the subject clear of all four edges. 16:9 horizontal."
)

# --- Chained frames ----------------------------------------------------------
# 2026-10-11: a beat can show several frames, and every frame after the first in
# a location is an EDIT of the frame before it (the previous image is attached
# in Flow as the reference, in place of the character art). That continuity is
# what makes a run of stills read as animation rather than a slideshow.
#
# EDIT_TEMPLATE wraps the script's short edit line. It deliberately does NOT
# carry STYLE_BLOCK: the attached picture already IS the style, and a full
# scene description invites the model to redraw from scratch instead of
# touching up what is there. "Everything not mentioned stays where it is" is
# the clause doing the work - without it the model re-poses the whole frame.
#
# Two clauses added after the first full video (2026-10-11):
#   - Pure flat white, crisp lines. Each edit redraws the whole picture from
#     a slightly worse copy, so the page went grey and grainy deeper into a
#     chain. Asking for it does not undo that, but stops edits adding to it.
#   - No words unless asked. Edits invented captions ("MAX & CAR", "YAY!",
#     "MONEY...") and, because every edit keeps everything, they stayed on
#     screen for the rest of the chain.
EDIT_TEMPLATE = (
    "Edit the attached picture. Change only this: {edit} "
    "Everything not mentioned stays exactly where and how it is: the same "
    "crude MS Paint doodle style, line thickness and colours, the same "
    "character design and the same framing. Keep the background pure flat "
    "white with no grey, texture or grain, and the lines crisp. Add no words, "
    "letters or numbers unless this change asks for them."
)

# Every edit degrades the picture a little and the errors compound, so a long
# chain drifts off-model and the page goes grey. pipeline.py warns past this
# many edits in a row; the fix is a fresh image_prompt on a beat partway
# through the location. Was 8 until the first full video showed the grain
# building up well before that.
CHAIN_MAX_EDITS = 5

# The check after the image stage compares every edit with the frame it was
# made from. Measured on the first full video (132 edits): every edit under
# CHANGE_MIN_FRACTION of the picture came back identical to its parent, the
# image model had ignored it. Over CHANGE_MAX_FRACTION is usually a big change
# that was asked for, but it is where a whole-frame re-pose shows up too, so
# those are listed to look at rather than reported as errors.
CHANGE_MIN_FRACTION = 0.0015
CHANGE_MAX_FRACTION = 0.20

# Tempo: how long a picture stays up. pass2 mixes three (2026-10-11), since a
# constant picture-per-second felt like a metronome: FAST ~1.5s, MEDIUM ~2s,
# SLOW 3-4s, about a quarter / half / quarter. `pipeline.py prompts` reports
# the mix using these bucket edges.
TEMPO_FAST_MAX = 1.75             # under this a picture counts as fast
TEMPO_MEDIUM_MAX = 2.75           # from this up it counts as slow

# Word-timed frames: an edit can name the narration word it belongs to, and
# the picture changes as that word is spoken instead of on an even split of
# the beat. No frame is held shorter than this, so two close words cannot
# make a flicker.
MIN_FRAME_SECONDS = 0.35

# Whisper is only used to find WHEN each known word is spoken (see
# modules/transcriber.py), so the small model is enough.
WHISPER_MODEL = "base"

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
# A music bed mixed under the narration after Remotion renders. New scripts
# use mood music (below). Older runs, from before moods, carry their own
# ElevenLabs-composed music.mp3 and render over that; assets/music/ holds an
# optional shared fallback, the first audio file found there is used.
MUSIC_ENABLED = True
MUSIC_DIR = ASSETS_DIR / "music"      # fallback bed, used if a run has no music

# How far BELOW the narration the bed sits, in dB. This is measured, not a
# fixed multiplier: the music is composed fresh per video so its loudness
# varies run to run, and a blind gain would land anywhere from "fighting the
# voice" to "inaudible". 18 dB is the usual range for a bed under speech.
# Lower the number to make music more present, raise it to push it back.
MUSIC_DUCK_DB = 18.0
MUSIC_VOLUME = 0.10          # fallback gain, only if loudness cannot be read
MUSIC_FADE_SECONDS = 2.0     # fade out over the outro so it does not stop dead

# --- Mood music ---------------------------------------------------------------
# The bed: every location in the script names a mood
# (plan.locations[].music) and the music changes with the scene, crossfading
# on the dissolve. One folder per mood under MUSIC_MOODS_DIR; the folder names
# ARE the allowed moods. A script with no moods falls back to mix_music.
#
# Numbers below were tuned by ear on american_football_explained (2026-10-13)
# and judged "perfect". The 18 dB MUSIC_DUCK_DB above left sparse classical
# (solo piano) inaudible while a full orchestra still came through, so each
# piece is levelled first and then sits much closer to the voice.
MUSIC_MOODS_DIR = MUSIC_DIR / "moods"
# Every piece is evened out (quiet passages up, loud ones down) and set to this
# loudness before the gain, so a solo piano and an orchestra sit level.
MUSIC_MOOD_LEVEL_LUFS = -23.0
# How far below the narration the levelled bed sits. No sidechain ducking: the
# narration has only CUT_PAD_SECONDS between sentences, so a ducker held the
# music down the whole time and it sat ~18 dB under again.
MUSIC_MOOD_UNDER_DB = 11.0
MUSIC_CROSSFADE_SECONDS = 1.5   # centred on the location change
# Moods whose piece is trimmed so it ENDS with its section, landing the
# piece's climax on the end of the scene instead of starting from the top.
MUSIC_END_ALIGNED_MOODS = ("building",)
# More switches than this gets jumpy. A warning, not an error.
MUSIC_MAX_SWITCHES = 4

# --- Outro ------------------------------------------------------------------
# The subscribe/like card, appended as a final BEAT rather than a special
# component, so it inherits the dissolve and timing for free.
#
# Both files are generated ONCE and cached here, then reused by every video:
# same wording, same voice, same image, so the channel ends consistently and it
# costs no API calls after the first run.
OUTRO_ENABLED = True
OUTRO_DIR = ASSETS_DIR / "outro"
OUTRO_LINE = "If you want more of these, subscribe and hit like."

# --- ElevenLabs ------------------------------------------------------------
# The US regional endpoint serves the good render. The global default
# (api.elevenlabs.io) returns a flat/robotic voice on this account - it only
# matches the website when we hit this host. Confirmed by capturing the web
# app's own request, back on eleven_v3; the host is kept for v4 because the
# cause was the endpoint, not the model. Do not "simplify" this back to the
# default base URL.
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

# English goes through text_to_dialogue + eleven_v4, which is what gives the
# lively read and supports inline emotion tags like [surprised]. ru/es fall back
# to multilingual_v2 via plain text_to_speech.
ELEVENLABS_MODEL_DIALOGUE = "eleven_v4"
ELEVENLABS_MODEL_MULTILINGUAL = "eleven_multilingual_v2"
ELEVENLABS_OUTPUT_FORMAT = "mp3_44100_192"

# Stability: 0.0 creative, 0.5 natural, 1.0 robust. High values make the model
# less responsive to the inline [emotion] tags the narration leans on, so stay
# at or below 0.5. Nothing auditions these takes before they ship and 0.0 can
# hallucinate a read, so 0.5 is the floor for an unattended pipeline.
ELEVENLABS_STABILITY = 0.5

# Similarity: how closely the read tracks the reference voice. Higher tracks it
# closer at some cost in naturalness.
#
# This is eleven_v4 only. The dialogue endpoint answers a v3 request carrying
# it with 400 "similarity is not supported by the 'eleven_v3' model", so the
# model and this setting have to move together - rolling MODEL_DIALOGUE back to
# v3 means removing this from the request too, not just changing the string.
ELEVENLABS_SIMILARITY = 0.7

# How many beats go into ONE eleven_v4 request. Currently 1, so batching is
# off: see the 2026-10-11 note at the end of this comment.
#
# This is the consistency fix. eleven_v4 is not deterministic and is excluded
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
# the inconsistent per-beat fallback, and long single generations are what the
# dialogue models are least reliable at. At the new ~52 characters a beat, 1400 works out to
# ~27 beats, so BATCH_SIZE 18 is what actually binds - roughly five requests
# for a 90-beat script, the same request count 45-beat scripts used to need.
#
# Set BATCH_SIZE to 1 to disable batching and restore one request per beat.
#
# 2026-10-11: set to 1. With short 3-12 word beats the batch timings cut ~33
# of 75 beats inside a word (mostly clipping a beat's first syllable), while
# the beats that fell back to per-beat requests came out clean. Clipped words
# are worse than slight tone variation between takes. Was 18.
ELEVENLABS_BATCH_SIZE = 1
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

# --- Transitions -------------------------------------------------------------
# ALL of these mirror remotion/src/constants.ts and are kept in sync BY HAND.
# Remotion is the one that actually renders; these exist so the Python side can
# predict a finished video's length without running a render. Change one, change
# the other, or the length estimate silently drifts from reality.

# Two kinds of boundary now. Within a location beats hard cut; a change of
# location (or a fresh drawing mid-location) dissolves. A dissolve's tail is consumed by the overlap so it costs
# no timeline, but a hard cut's pad is real added length - which is why the
# estimate below has to count them.
DISSOLVE_SECONDS = 8 / 30         # 0.27s, on a location change or a redraw
CUT_PAD_SECONDS = 4 / 30          # 0.13s breath between beats on a hard cut


