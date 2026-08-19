# Animationer

Automated pipeline for a "lore" YouTube Shorts / TikTok channel: one topic in,
one narrated 16:9 animated `.mp4` out. A hand-written script of short beats
(narration sentence + image description) drives everything downstream - one
AI-generated still per beat, one narration clip per beat, timed and composited
into a final video with Ken Burns pan/zoom, crossfades, and a music bed.

See `README.md` for the full pipeline diagram, setup, and usage. This file is
for how the project is *built*, not how to run it.

## Pipeline (implementation)

```
prompts/manualprompt.txt --(pasted into an LLM by hand)--> script.json
pipeline.py orchestrates every stage below, one folder per video under
output/<slug>/. Every stage reads/writes files only - nothing is carried in
memory between stages - so any stage can be re-run alone and finished work is
skipped on re-run.

  cmd_prompts   script.json -> scenes.txt
  cmd_images    flow_runner/ (Playwright on Google Flow) -> images/*.png
  cmd_voice     modules/voice_generator.py (ElevenLabs)  -> audio/*.mp3
  cmd_manifest  pairs images+audio, measures durations, adds outro beat
  cmd_music     modules/music_generator.py (ElevenLabs Music) -> music.mp3
  cmd_render    modules/video_editor.py -> remotion/ render -> ffmpeg mix -> final.mp4
```

`python pipeline.py` with no subcommand runs every stage in order (`cmd_all`).
`python pipeline.py check` reports what's present/missing for a run without
doing anything.

## Status (trust levels)

- `pipeline.py`, `modules/voice_generator.py`, `modules/music_generator.py`,
  `modules/video_editor.py`, `flow_runner/` - **live and proven.** Two full
  videos have been produced end to end (see `output/`, gitignored). Treat
  these as working code, not drafts.
- `modules/image_generator.py` - **dead code, not called.** It was the
  original direct-Gemini-API image path; Gemini image access is blocked on
  this account, so `flow_runner/` (browser automation against Google Flow)
  replaced it. Kept around in case direct API access becomes available again.
- `modules/transcriber.py` - **built but not wired into rendering.** Only
  `strip_tags()` is used today (stripping `[emotion]` tags before a beat's
  text is stored). `transcribe_words()` / `align()` do real Whisper-based
  word-level timing and are ready for a future captions pass, but
  `remotion/src/compositions/LectureVideo.tsx` currently ships **no captions
  at all**, by design ("the art carries the frame, the narration carries the
  meaning").
- `remotion/` - **live and proven**, 30fps/1920x1080, `LectureVideo`
  composition: `KenBurnsImage.tsx` alternates a push-in and a left-to-right
  drift by beat index (not random, so re-renders are byte-identical), and
  `TransitionSeries` crossfades between beats.

## Conventions

- All tunable constants (pacing, zoom range, crossfade length, model names,
  the visual style prompt) live in `config.py` - don't hardcode them in
  modules. `remotion/src/constants.ts` mirrors the video-geometry constants
  and is kept in sync **by hand** - if you change `FPS`/`WIDTH`/`HEIGHT`/zoom
  in `config.py`, update `constants.ts` too.
- Each pipeline stage is one file in `modules/`, takes/returns plain dicts and
  file paths (no shared state/classes) so stages stay independently testable
  and swappable.
- Every beat is `{"narration": str, "image_prompt": str, ...}`. Downstream
  artifacts are named so ordering is obvious from a directory listing
  (`beat_{index:03}.png`, etc.) - see `pipeline.py`'s `image_name`/`audio_name`.
- `flow_runner/config.py` is the single place that knows Google Flow's actual
  DOM. Every selector there is commented with the exact failure it exists to
  fix - read the comment before "simplifying" a selector, several look
  redundant but aren't (e.g. why `ADD_TO_PROMPT_SELECTORS` is separate from
  `UPLOAD_TRIGGER_SELECTORS`, why `CLEAR_PROMPT_SELECTORS_DO_NOT_USE` is kept
  as a documented dead end rather than deleted).
- `config.py`'s `STYLE_PREFIX`/`STYLE_BLOCK` are written defensively from real
  failures (grounding against real photos, invented on-image text, drawn UI
  chrome) - each rule exists because a specific bad generation happened
  first. Read the comments above them before editing.

## Known gaps / likely next tasks

1. Character-consistency scoring: no automatic check that a generated image
   still matches the reference character, and no retry-on-drift. Over ~100
   generations per video, drift is visible by the end.
2. Wire `modules/transcriber.py`'s word alignment into
   `LectureVideo.tsx` if/when karaoke-style captions are wanted - the
   alignment code already exists, only the Remotion side does not consume it.
3. No cost tracking. Worth logging image/TTS/music call counts per run so
   per-video API cost is visible before scaling up how many videos get made.
4. `flow_runner/` selectors are hand-inspected guesses against Flow's current
   DOM (`python flow_runner/runner.py --inspect` regenerates them). Expect
   breakage whenever Google changes the UI.

## Setup / Run

See `README.md` - kept there so it's accurate for anyone reading the repo on
GitHub, not duplicated here.
