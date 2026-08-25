import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import config
from modules import transcriber

FLOW_RUNNER = config.ROOT_DIR / "flow_runner" / "runner.py"

NEW_SCRIPT = {
  "topic": "moon-landing-fake",
  "format": "explainer",
  "plan": {
    "spine_question": "Why do millions of people still think the Apollo 11 moon landing was a giant movie set?",
    "payoff_line": "So, the moon landing is real, but human paranoia? That's the real infinite universe.",
    "deflations": [
      {
        "assumed": "The flag blowing in the wind proves it was filmed on Earth.",
        "actual": "It is rippling because of a metal rod and the twisting motion used to plant it, not wind.",
        "who_decided": "People who do not understand vacuum physics.",
        "build_beat": "[frustrated] 'Look at it! It is blowing in the wind!'",
        "drop_beat": "[laughs] It is not wind. It is just... physics."
      }
    ],
    "specifics": [
      {
        "fact": "Over 400,000 people worked on the Apollo project.",
        "source": "NASA historical archives",
        "beat": "Four hundred thousand people worked on the Apollo project."
      }
    ],
    "facts_to_check": [
      {
        "claim": "Astronauts passing through the Van Allen belts received only a small, non-lethal dose of radiation.",
        "source": "NASA / radiation dosimetry records from Apollo missions"
      }
    ],
    "locations": [
      {
        "name": "sun-bright lunar photograph archive",
        "visual_anchor": "pale grey plaster walls, polished pale wood flooring, one wide arched window, a long oak reading table, a tall steel shelving unit, red archive folders and blue photograph sleeves stacked along the shelves, exposed white ceiling beams"
      },
      {
        "name": "flag rigging workshop",
        "visual_anchor": "rough concrete walls, scuffed grey rubber flooring, one tall metal roller door, a heavy steel workbench, a rack of thin metal rods, a folded fabric flag draped across a stand, red tool cabinets and blue storage crates nearby"
      },
      {
        "name": "camera exposure testing chamber",
        "visual_anchor": "matte black felt-lined walls, dark rubber flooring, one small round porthole window, a heavy tripod-mounted camera on a steel stand, a wide white photo backdrop screen, red camera equipment cases and blue calibration charts stacked nearby"
      },
      {
        "name": "film prop and set-dressing storage bay",
        "visual_anchor": "rough plywood walls, painted concrete flooring, one large sliding freight door, a tall shelving rack of foam props, a large canvas backdrop rolled against the wall, red gaffer tape spools and blue plastic prop crates stacked in the corner"
      },
      {
        "name": "radiation dosimetry monitoring room",
        "visual_anchor": "brushed steel wall panels, dark grey tiled flooring, one thick round viewing window, a wide instrument console with dial gauges, a tall rack of cabled equipment, red warning lamps and blue indicator lights fixed along the panels"
      },
      {
        "name": "overflowing conspiracy theory archive",
        "visual_anchor": "cluttered cork board walls, worn checkered tile flooring, one narrow frosted window, a long cluttered worktable, a tall filing cabinet stuffed with folders, red string connecting pinned photographs and blue evidence folders scattered across the table"
      }
    ],
    "setting_anchor": "recurring red archival accents paired with blue equipment and evidence markings appear across every location"
  },
  "beats": [
    {
      "narration": "[curious] Let's travel back to 1969.",
      "location": "sun-bright lunar photograph archive",
      "image_prompt": "reference character sits at a long oak table scattered with lunar photographs, leaning forward with a curious expression while opening a thick red folder, wide shot, pale wood table surface, one blue photograph sleeve resting open beside a stack of glossy prints",
      "image_prompt_alt": "reference character stands beside a tall steel shelving unit stacked with photograph sleeves, tilting their head with curious interest while holding a thick red folder open in both hands, medium shot, one blue folder resting on a nearby stack of glossy prints"
    },
    {
      "narration": "The US sent humans to the moon... or so they say.",
      "location": "sun-bright lunar photograph archive",
      "image_prompt": "reference character holds up a large photograph showing an astronaut in a bulky white pressure suit standing on a grey cratered surface, studying it with a flat skeptical expression, medium close-up, red folder tucked under one arm, blue photograph sleeve resting on the table",
      "image_prompt_alt": "reference character examines a large photograph of a figure in a bulky white fabric suit with a rounded reflective helmet standing on a grey cratered surface, deadpan expression, three-quarter view, red folder tucked underarm, blue photograph sleeve resting nearby on the table"
    },
    {
      "narration": "[sarcastic] Because some people think the whole thing was filmed in a Hollywood basement.",
      "location": "sun-bright lunar photograph archive",
      "image_prompt": "reference character stands with arms crossed and one eyebrow raised in sarcastic disbelief, looking toward a crude pinned sketch of a soundstage on the wall, medium shot, red folder resting on the table nearby, blue photograph sleeve tucked beneath a stack of prints",
      "image_prompt_alt": "reference character leans against the oak table with arms crossed and a sarcastic half-smile, glancing sideways at a crude pinned sketch of a soundstage on the wall, three-quarter shot, red folder resting nearby, blue photograph sleeve tucked beneath the stack of prints"
    },
    {
      "narration": "Yes. A basement.",
      "location": "sun-bright lunar photograph archive",
      "image_prompt": "reference character gestures flatly toward a small cardboard diorama of a cluttered basement film set resting on the oak table, unimpressed expression, close-up, red folder pushed aside, blue photograph sleeve visible at the table's edge",
      "image_prompt_alt": "reference character points with an unimpressed flat expression toward a small cardboard model of a cluttered basement film set on the table, close-up, red folder pushed aside, blue photograph sleeve visible near the table's edge"
    },
    {
      "narration": "But WHY do people believe this?",
      "location": "sun-bright lunar photograph archive",
      "image_prompt": "reference character leans back in a wooden chair with a puzzled thoughtful expression, surrounded by scattered folders and photograph sleeves across the oak table, wide shot, red folder open in the foreground, blue photograph sleeve resting beside stacked prints",
      "image_prompt_alt": "reference character tilts their head back against the chair with a genuinely puzzled expression, surrounded by scattered folders and loose prints across the table, wider shot, red folder open in the foreground, blue photograph sleeve resting among the stacked prints"
    },
    {
      "narration": "First, let's look at the famous flag.",
      "location": "flag rigging workshop",
      "image_prompt": "reference character stands beside a folded fabric flag draped across a metal stand, looking toward it with curious attention, medium shot, heavy steel workbench nearby, a rack of thin metal rods mounted on the wall, red tool cabinet in the background",
      "image_prompt_alt": "reference character stands close to a folded fabric flag resting on a metal stand, curious expression, wider shot, heavy steel workbench nearby, a rack of thin metal rods mounted on the wall, red tool cabinet visible in the background"
    },
    {
      "narration": "[frustrated] 'Look at it! It is blowing in the wind!'",
      "location": "flag rigging workshop",
      "image_prompt": "reference character watches with a skeptical raised eyebrow while an unnamed frustrated bystander in a rumpled jacket points urgently at a rippling flag mounted on a metal rod, medium two-shot, heavy steel workbench beside them, blue storage crate resting on the floor",
      "image_prompt_alt": "reference character observes with a skeptical raised eyebrow while a frustrated man in a rumpled jacket and messy hair jabs a finger toward a rippling flag on a metal rod, wider two-shot, heavy steel workbench beside them, blue storage crate resting nearby on the floor"
    },
    {
      "narration": "There is NO wind in space, genius.",
      "location": "flag rigging workshop",
      "image_prompt": "reference character stands with a flat, mildly annoyed expression beside the rippling flag replica, one hand resting on the metal rod, close medium shot, heavy steel workbench in the background, red tool cabinet and blue storage crate along the wall",
      "image_prompt_alt": "reference character rests one hand on the metal flag rod with a flat, mildly annoyed expression, close-up, heavy steel workbench visible behind them, red tool cabinet and blue storage crate along the back wall"
    },
    {
      "narration": "So it MUST be fake, right?",
      "location": "flag rigging workshop",
      "image_prompt": "reference character raises both eyebrows in exaggerated mock doubt, gesturing loosely toward the flag mounted on its stand, medium shot, heavy steel workbench beside them, a rack of thin metal rods mounted on the wall, blue storage crate on the floor",
      "image_prompt_alt": "reference character shrugs with an exaggerated doubtful expression, one hand raised toward the flag on its stand, wider shot, heavy steel workbench nearby, a rack of thin metal rods mounted on the wall, blue storage crate resting on the floor"
    },
    {
      "narration": "[sighs] Wrong.",
      "location": "flag rigging workshop",
      "image_prompt": "reference character shakes their head slowly with a resigned expression, standing beside the heavy steel workbench, close-up, the flag mounted on its stand behind them, red tool cabinet and blue storage crate visible along the wall",
      "image_prompt_alt": "reference character exhales with a resigned, slightly tired expression, standing near the steel workbench, close medium shot, the flag on its stand visible behind them, red tool cabinet and blue storage crate along the back wall"
    },
    {
      "narration": "NASA knew a regular flag would just hang straight down and look sad.",
      "location": "flag rigging workshop",
      "image_prompt": "reference character points toward a second fabric flag hanging limply straight down from a bare rod, mildly amused expression, medium shot, heavy steel workbench nearby, red tool cabinet and blue storage crate along the wall",
      "image_prompt_alt": "reference character gestures toward a plain fabric flag drooping straight down from a bare metal rod, faint amused expression, wider shot, heavy steel workbench nearby, red tool cabinet and blue storage crate along the back wall"
    },
    {
      "narration": "So they put a metal rod along the top to hold it out.",
      "location": "flag rigging workshop",
      "image_prompt": "reference character watches closely as a thin metal rod is fitted along the top edge of the fabric flag on the workbench, curious expression, close-up, heavy steel workbench surface, red tool cabinet visible in the background",
      "image_prompt_alt": "reference character leans in with curious attention as a thin metal rod is slid along the top hem of the fabric flag resting on the workbench, close-up, heavy steel workbench surface, red tool cabinet visible behind them"
    },
    {
      "narration": "But the rod got stuck.",
      "location": "flag rigging workshop",
      "image_prompt": "reference character tilts their head with a puzzled expression at a metal rod jammed at an awkward angle within the flag's top hem, medium close-up, heavy steel workbench beneath, blue storage crate resting on the floor nearby",
      "image_prompt_alt": "reference character squints with a puzzled expression at a metal rod caught at an awkward angle inside the flag's top hem, close-up, heavy steel workbench beneath, blue storage crate resting nearby on the floor"
    },
    {
      "narration": "Plus, the astronauts twisted the pole to push it into the hard dirt.",
      "location": "flag rigging workshop",
      "image_prompt": "reference character watches an astronaut in a bulky white pressure suit twisting a metal pole downward into a small tray of packed grey dirt on the workbench, medium shot, rack of thin metal rods mounted on the wall, red tool cabinet nearby",
      "image_prompt_alt": "reference character observes a figure in a bulky white fabric suit with a rounded helmet twisting a metal pole into a tray of packed grey dirt on the workbench, wider shot, rack of thin metal rods mounted on the wall, red tool cabinet nearby"
    },
    {
      "narration": "That twisting made the flag ripple.",
      "location": "flag rigging workshop",
      "image_prompt": "reference character points closely at the rippled folds of fabric along the flag mounted on its stand, focused expression, close-up, heavy steel workbench in the background, blue storage crate resting on the floor",
      "image_prompt_alt": "reference character traces a finger near the rippled folds of the fabric flag on its stand, focused expression, extreme close-up, heavy steel workbench blurred behind, blue storage crate resting nearby on the floor"
    },
    {
      "narration": "[laughs] It is not wind. It is just... physics.",
      "location": "flag rigging workshop",
      "image_prompt": "reference character stands with arms crossed, laughing openly beside the rippled flag mounted on its stand, medium shot, heavy steel workbench nearby, red tool cabinet and blue storage crate along the back wall",
      "image_prompt_alt": "reference character laughs with head tilted back, arms loosely crossed near the rippled flag on its stand, wider shot, heavy steel workbench nearby, red tool cabinet and blue storage crate along the back wall"
    },
    {
      "narration": "Okay, next point.",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character walks through a narrow doorway into the chamber with a neutral curious expression, one hand trailing along a steel equipment case, medium shot, heavy tripod-mounted camera visible ahead, red camera case resting on the floor",
      "image_prompt_alt": "reference character steps forward through a narrow doorway with a neutral, mildly curious expression, glancing toward a heavy tripod-mounted camera across the room, wider shot, red camera case resting on the floor nearby"
    },
    {
      "narration": "Conspiracy fans say: 'Where are the stars in the photos?'",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character holds up a dark lunar surface photograph with no visible stars, one eyebrow raised skeptically, medium close-up, heavy tripod-mounted camera beside them, blue calibration chart resting against the wall",
      "image_prompt_alt": "reference character studies a dark lunar surface photograph empty of stars, skeptical raised eyebrow, close-up, heavy tripod-mounted camera positioned beside them, blue calibration chart leaning against the wall"
    },
    {
      "narration": "Space is full of stars, right?",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character looks upward with a curious expression toward a small illuminated star chart mounted on the wall, medium shot, heavy tripod-mounted camera nearby, red camera case resting on the floor",
      "image_prompt_alt": "reference character tilts their head upward, curious expression, toward a small round star chart fixed to the wall, wider shot, heavy tripod-mounted camera nearby, red camera case resting on the floor"
    },
    {
      "narration": "True. But think about how cameras work.",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character examines a heavy tripod-mounted camera closely, adjusting a dial with a thoughtful expression, close-up, blue calibration chart resting against the wall, red camera case on the floor nearby",
      "image_prompt_alt": "reference character crouches beside the heavy tripod-mounted camera, thoughtful expression, fingers resting near a dial on its side, close medium shot, blue calibration chart against the wall, red camera case nearby on the floor"
    },
    {
      "narration": "The sun was shining VERY brightly on the moon.",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character shields their eyes with one raised hand while facing a wide white photo backdrop screen, squinting expression, medium shot, heavy tripod-mounted camera beside them, red camera case resting on the floor",
      "image_prompt_alt": "reference character raises one hand to shield their eyes, squinting toward a wide white backdrop screen filling the frame, wider shot, heavy tripod-mounted camera beside them, red camera case resting nearby on the floor"
    },
    {
      "narration": "The astronauts were wearing bright white suits.",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character stands beside an astronaut in a bulky white fabric pressure suit positioned near the white backdrop screen, curious expression, medium two-shot, heavy tripod-mounted camera in the foreground, blue calibration chart nearby",
      "image_prompt_alt": "reference character observes a figure in a bulky white fabric suit with a rounded helmet standing near the white backdrop screen, curious expression, wider two-shot, heavy tripod-mounted camera in the foreground, blue calibration chart nearby"
    },
    {
      "narration": "To take a good picture of bright things, your camera needs a quick snap.",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character adjusts a small dial on the tripod-mounted camera with focused concentration, close-up, white backdrop screen visible behind, red camera case resting on the floor nearby",
      "image_prompt_alt": "reference character turns a small dial on the tripod-mounted camera with careful focus, close-up hands and camera body, white backdrop screen behind, red camera case nearby on the floor"
    },
    {
      "narration": "If the camera waited long enough to see the dim stars...",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character studies a slightly blurred overexposed print held in both hands, curious contemplative expression, medium close-up, heavy tripod-mounted camera resting beside them, blue calibration chart nearby",
      "image_prompt_alt": "reference character tilts a blurred overexposed print toward the light with a contemplative expression, close-up, heavy tripod-mounted camera resting nearby, blue calibration chart against the wall"
    },
    {
      "narration": "[loudly] The astronauts would look like giant glowing ghosts.",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character reacts with wide-eyed surprise at an overexposed white print pinned to the wall showing a barely visible figure, medium shot, heavy tripod-mounted camera nearby, red camera case resting on the floor",
      "image_prompt_alt": "reference character startles back with wide-eyed surprise, staring at an overexposed white print pinned up showing a barely visible outline, wider shot, heavy tripod-mounted camera nearby, red camera case resting on the floor"
    },
    {
      "narration": "Try taking a picture of the stars with your phone while standing under a bright street lamp.",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character holds a small rectangular device toward a tall metal lamp post prop standing in the corner, demonstrating expression, medium shot, heavy tripod-mounted camera resting nearby, red camera case on the floor",
      "image_prompt_alt": "reference character extends a small rectangular device toward a tall metal lamp post prop in the corner, explaining expression, wider shot, heavy tripod-mounted camera resting nearby, red camera case on the floor"
    },
    {
      "narration": "[annoyed] See? No stars.",
      "location": "camera exposure testing chamber",
      "image_prompt": "reference character holds up a plain dark print with a flat, mildly annoyed expression, close-up, heavy tripod-mounted camera resting beside them, blue calibration chart against the wall",
      "image_prompt_alt": "reference character presents a plain dark print at arm's length with a flat, mildly annoyed expression, medium close-up, heavy tripod-mounted camera resting nearby, blue calibration chart against the wall"
    },
    {
      "narration": "Now, let\u2019s talk about Stanley Kubrick.",
      "location": "film prop and set-dressing storage bay",
      "image_prompt": "reference character stands beside an empty canvas director's chair and a wooden clapperboard resting on a shelf, mildly intrigued expression, medium shot, tall shelving rack of foam props nearby, red gaffer tape spool on the floor",
      "image_prompt_alt": "reference character leans against an empty canvas director's chair near a wooden clapperboard, mildly intrigued expression, wider shot, tall shelving rack of foam props nearby, red gaffer tape spool resting on the floor"
    },
    {
      "narration": "Some people think the government hired this famous movie maker to direct the fake landing.",
      "location": "film prop and set-dressing storage bay",
      "image_prompt": "reference character watches with a skeptical expression as Stanley Kubrick sits in a canvas director's chair studying a script, medium two-shot, tall shelving rack of foam props behind them, blue plastic prop crate resting on the floor",
      "image_prompt_alt": "reference character observes with a skeptical expression as a lean middle-aged film director with a thick dark beard and round wire-frame glasses sits in a canvas director's chair studying a script, wider two-shot, tall shelving rack of foam props behind them, blue plastic prop crate on the floor"
    },
    {
      "narration": "Because he made a famous space movie.",
      "location": "film prop and set-dressing storage bay",
      "image_prompt": "reference character glances toward Stanley Kubrick, who stands holding a round metal film reel case beside a large canvas backdrop rolled against the wall, medium shot, red gaffer tape spool resting on the floor nearby",
      "image_prompt_alt": "reference character glances toward a lean bearded film director in a rumpled cardigan holding a round metal film reel case beside a large canvas backdrop rolled against the wall, wider shot, red gaffer tape spool resting on the floor nearby"
    },
    {
      "narration": "[laughs harder] But here is the funny part.",
      "location": "film prop and set-dressing storage bay",
      "image_prompt": "reference character laughs with head tilted back, one hand braced on the tall shelving rack of foam props, Stanley Kubrick visible nearby examining a prop, medium shot, blue plastic prop crate on the floor",
      "image_prompt_alt": "reference character laughs openly, bracing one hand on the shelving rack of foam props, a bearded film director in a rumpled cardigan visible nearby examining a prop, wider shot, blue plastic prop crate on the floor"
    },
    {
      "narration": "Kubrick was known for wanting everything to be absolutely perfect.",
      "location": "film prop and set-dressing storage bay",
      "image_prompt": "reference character watches Stanley Kubrick inspecting a foam prop closely with a meticulous expression, medium two-shot, tall shelving rack behind them, red gaffer tape spool and blue plastic prop crate on the floor",
      "image_prompt_alt": "reference character watches a bearded film director in round wire-frame glasses inspecting a foam prop closely with a meticulous expression, wider two-shot, tall shelving rack behind them, red gaffer tape spool and blue plastic prop crate on the floor"
    },
    {
      "narration": "If he directed the moon landing...",
      "location": "film prop and set-dressing storage bay",
      "image_prompt": "reference character raises an eyebrow skeptically while Stanley Kubrick points toward a small lunar module mockup resting on a shelf, medium shot, canvas backdrop rolled against the wall behind them, blue plastic prop crate nearby",
      "image_prompt_alt": "reference character raises a skeptical eyebrow while a bearded film director points toward a small lunar module mockup resting on a shelf, wider shot, canvas backdrop rolled against the wall behind them, blue plastic prop crate nearby"
    },
    {
      "narration": "He would have demanded they shoot it on real location.",
      "location": "film prop and set-dressing storage bay",
      "image_prompt": "reference character watches Stanley Kubrick gesturing firmly toward the large canvas backdrop rolled against the wall, unimpressed expression, medium shot, tall shelving rack of foam props nearby, red gaffer tape spool on the floor",
      "image_prompt_alt": "reference character observes a bearded film director gesturing firmly toward the large canvas backdrop rolled against the wall, unimpressed expression, wider shot, tall shelving rack of foam props nearby, red gaffer tape spool on the floor"
    },
    {
      "narration": "[snorts] On the actual moon.",
      "location": "film prop and set-dressing storage bay",
      "image_prompt": "reference character smirks with a short amused snort, arms crossed, standing beside the rolled canvas backdrop, close-up, tall shelving rack of foam props blurred behind, blue plastic prop crate on the floor",
      "image_prompt_alt": "reference character huffs a short amused laugh, arms crossed, standing near the rolled canvas backdrop, close medium shot, tall shelving rack of foam props behind, blue plastic prop crate resting on the floor"
    },
    {
      "narration": "What about the deadly radiation?",
      "location": "radiation dosimetry monitoring room",
      "image_prompt": "reference character steps toward a wide instrument console with dial gauges, curious expression, medium shot, tall rack of cabled equipment beside them, red warning lamp fixed above the console",
      "image_prompt_alt": "reference character approaches a wide instrument console covered in dial gauges, curious expression, wider shot, tall rack of cabled equipment nearby, red warning lamp fixed above the console"
    },
    {
      "narration": "Earth has invisible rings of radiation around it.",
      "location": "radiation dosimetry monitoring room",
      "image_prompt": "reference character studies a curved ring-shaped diagram model mounted above the instrument console, thoughtful expression, medium close-up, blue indicator light fixed nearby, tall rack of cabled equipment in the background",
      "image_prompt_alt": "reference character leans in to study a curved ring-shaped model fixed above the instrument console, thoughtful expression, close-up, blue indicator light nearby, tall rack of cabled equipment blurred behind"
    },
    {
      "narration": "People say flying through them would cook the astronauts like hot pockets.",
      "location": "radiation dosimetry monitoring room",
      "image_prompt": "reference character raises an eyebrow with dry amusement while dial gauges on the console spike sharply, medium shot, red warning lamp fixed above, tall rack of cabled equipment beside them",
      "image_prompt_alt": "reference character smirks with dry amusement watching the console's dial gauges spike sharply, wider shot, red warning lamp fixed above, tall rack of cabled equipment beside them"
    },
    {
      "narration": "[calm] But NASA was not stupid.",
      "location": "radiation dosimetry monitoring room",
      "image_prompt": "reference character leans calmly against the wide instrument console, arms folded, composed expression, medium shot, blue indicator light fixed nearby, tall rack of cabled equipment in the background",
      "image_prompt_alt": "reference character rests calmly against the edge of the instrument console, arms folded, composed expression, wider shot, blue indicator light nearby, tall rack of cabled equipment behind"
    },
    {
      "narration": "The rocket moved VERY fast.",
      "location": "radiation dosimetry monitoring room",
      "image_prompt": "reference character points toward a small rocket model mounted beside the instrument rack, focused expression, medium close-up, red warning lamp fixed above, blue indicator light nearby",
      "image_prompt_alt": "reference character gestures toward a small metallic rocket model mounted beside the instrument rack, focused expression, close-up, red warning lamp fixed above, blue indicator light nearby"
    },
    {
      "narration": "They passed through the thinnest part of the rings.",
      "location": "radiation dosimetry monitoring room",
      "image_prompt": "reference character traces a finger along a narrow section of the curved ring-shaped diagram model, focused expression, close-up, tall rack of cabled equipment blurred behind, red warning lamp fixed above",
      "image_prompt_alt": "reference character points precisely at a narrow section of the curved ring-shaped model, focused expression, extreme close-up, tall rack of cabled equipment behind, red warning lamp fixed above"
    },
    {
      "narration": "Total radiation they got was about the same as a hospital X-ray.",
      "location": "radiation dosimetry monitoring room",
      "image_prompt": "reference character holds a small handheld dosimeter device, comparing its dial reading with a thoughtful expression, medium close-up, wide instrument console beside them, blue indicator light fixed nearby",
      "image_prompt_alt": "reference character studies the dial reading on a small handheld dosimeter device with a thoughtful expression, close-up, wide instrument console beside them, blue indicator light fixed nearby"
    },
    {
      "narration": "Not great, but definitely not deadly.",
      "location": "radiation dosimetry monitoring room",
      "image_prompt": "reference character shrugs mildly with a resigned expression, standing beside the wide instrument console, medium shot, tall rack of cabled equipment behind them, red warning lamp fixed above",
      "image_prompt_alt": "reference character gives a small resigned shrug, leaning against the instrument console, wider shot, tall rack of cabled equipment behind them, red warning lamp fixed above"
    },
    {
      "narration": "So, the science clearly shows the landing was real.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character stands with arms crossed and a confident, satisfied expression amid a cluttered worktable covered with folders, medium shot, tall filing cabinet stuffed with folders behind them, red string connecting pinned photographs on the wall",
      "image_prompt_alt": "reference character stands with arms crossed and a quietly satisfied expression beside the cluttered worktable, wider shot, tall filing cabinet stuffed with folders behind them, red string connecting pinned photographs on the wall"
    },
    {
      "narration": "Why do the fake stories survive?",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character tilts their head with a puzzled expression, looking toward a cork board covered with pinned photographs connected by red string, medium shot, cluttered worktable in the foreground, blue evidence folder resting on top",
      "image_prompt_alt": "reference character tilts their head, genuinely puzzled, studying a cork board of pinned photographs connected by red string, wider shot, cluttered worktable in the foreground, blue evidence folder resting on top"
    },
    {
      "narration": "Because our brains are built to look for secrets.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character examines a pinned diagram connected by red string on the cork board, curious focused expression, medium close-up, tall filing cabinet nearby, blue evidence folder resting on the worktable",
      "image_prompt_alt": "reference character leans close to study a pinned diagram connected by red string, curious focused expression, close-up, tall filing cabinet nearby, blue evidence folder resting on the worktable"
    },
    {
      "narration": "When something HUGE happens, a simple explanation feels boring.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character flips through a thin folder with an unimpressed flat expression, medium shot, cluttered worktable covered with scattered papers, blue evidence folder resting nearby, tall filing cabinet in the background",
      "image_prompt_alt": "reference character leafs through a thin folder with a flat, unimpressed expression, close medium shot, cluttered worktable covered with scattered papers, blue evidence folder nearby, tall filing cabinet behind"
    },
    {
      "narration": "We want a big mystery.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character leans back against the tall filing cabinet with a faint amused expression, arms crossed, medium shot, cluttered worktable in the foreground, red string connecting pinned photographs on the wall behind",
      "image_prompt_alt": "reference character rests against the tall filing cabinet with a faint amused expression, arms loosely crossed, wider shot, cluttered worktable in the foreground, red string connecting pinned photographs behind"
    },
    {
      "narration": "It makes the believer feel special. Like they know a secret we do not.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character holds a small magnifying glass over a photograph on the worktable, skeptical focused expression, close-up, tall filing cabinet blurred behind, blue evidence folder resting nearby",
      "image_prompt_alt": "reference character peers through a small magnifying glass at a photograph on the worktable, skeptical focused expression, close medium shot, tall filing cabinet behind, blue evidence folder nearby"
    },
    {
      "narration": "[thoughtful] Plus, trusting the government is hard.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character sits at the cluttered worktable resting their chin on one hand, thoughtful expression, medium shot, tall filing cabinet behind them, red string connecting pinned photographs on the wall",
      "image_prompt_alt": "reference character sits at the worktable with chin propped on one hand, quietly thoughtful, wider shot, tall filing cabinet behind them, red string connecting pinned photographs on the wall"
    },
    {
      "narration": "But keeping a secret THIS big?",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character raises both eyebrows doubtfully at a tall stack of folders piled on the worktable, medium close-up, tall filing cabinet nearby, blue evidence folder resting on top of the stack",
      "image_prompt_alt": "reference character eyes a tall stack of folders on the worktable with doubtful raised eyebrows, close-up, tall filing cabinet nearby, blue evidence folder resting on top of the stack"
    },
    {
      "narration": "Four hundred thousand people worked on the Apollo project.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character gestures broadly across the worktable spread with rows of small folders and identification badges, matter-of-fact expression, wide shot, tall filing cabinet stuffed with folders in the background",
      "image_prompt_alt": "reference character sweeps an open hand across the worktable covered in rows of small folders and identification badges, matter-of-fact expression, wider shot, tall filing cabinet stuffed with folders behind"
    },
    {
      "narration": "You can not even get four friends to agree on a pizza topping.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character holds up a small handful of mismatched papers with a wry smirk, close-up, cluttered worktable in the background, blue evidence folder resting nearby",
      "image_prompt_alt": "reference character fans out a small handful of mismatched papers with a wry smirking expression, medium close-up, cluttered worktable behind, blue evidence folder resting nearby"
    },
    {
      "narration": "[chuckles] Imagine keeping 400,000 people quiet for fifty years.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character chuckles with head shaking slightly, leaning against the tall filing cabinet, medium shot, cluttered worktable in the foreground, red string connecting pinned photographs on the wall",
      "image_prompt_alt": "reference character laughs quietly with a small headshake, resting against the tall filing cabinet, wider shot, cluttered worktable in the foreground, red string connecting pinned photographs behind"
    },
    {
      "narration": "So, the moon landing is real, but human paranoia? That's the real infinite universe.",
      "location": "overflowing conspiracy theory archive",
      "image_prompt": "reference character closes a folder on the cluttered worktable with a resigned, faintly amused expression, sitting back in a wooden chair, medium shot, tall filing cabinet behind them, red string connecting pinned photographs on the wall",
      "image_prompt_alt": "reference character shuts a folder on the worktable, leaning back with a resigned, faintly amused expression, wider shot, tall filing cabinet behind them, red string connecting pinned photographs on the wall"
    }
  ],
  "music_prompt": "Sparse instrumental bed matching the topic's dry, inquisitive mood, around eighty-two BPM. Plucked acoustic guitar, soft marimba, low sustained cello, and light brushed drum kit. Flat consistent energy with no build, no swells and no drops. Sits far in the background under a spoken narrator with the mid range left clear. Purely instrumental with no vocals of any kind. Understated rather than comedic."
}



SCRIPT_TEMPLATE = {
    "topic": "",
    "beats": [
        {"narration": "", "image_prompt": ""},
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
    import re
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
        for field in ("narration", "image_prompt"):
            if not isinstance(beat.get(field), str) or not beat[field].strip():
                raise SystemExit(f"Beat {i} is missing a non-empty {field!r}.")
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


def find_image(run_dir: Path, index: int) -> Path | None:
    """Extension is unknown until Flow downloads it, so glob for it."""
    return next((run_dir / "images").glob(f"{image_name(index)}.*"), None)


def find_audio(run_dir: Path, index: int) -> Path | None:
    return next((run_dir / "audio").glob(f"{audio_name(index)}.*"), None)


# --- init ------------------------------------------------------------------

def cmd_init(args) -> int:
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

    Same argument as config.STYLE_PREFIX/STYLE_BLOCK, applied one level down:
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


def cmd_prompts(args) -> int:
    run_dir = resolve_run(args.run)
    data = load_script(run_dir)
    beats = data["beats"]
    out_path = run_dir / "scenes.txt"

    lines = [
        "# Generated by pipeline.py - do not edit by hand.",
        "# Line order IS scene order: line 1 -> scene_001, and so on.",
        f"# {len(beats)} beats from script.json",
        "",
    ]
    # Location/setting anchors come from plan, not from the beat text. See
    # _anchor_map: the beats used to carry a paraphrased copy each.
    setting_anchor, location_anchors = _anchor_map(data)
    missing_anchor: list[int] = []
    anchored = 0

    collapsed = stripped = 0
    for index, beat in enumerate(beats, 1):
        # scenes.txt is strictly one prompt per line. A newline inside a prompt
        # scenes.txt is strictly one prompt per line. A newline inside a prompt
        # would split one beat into two and shift every scene after it, so
        # whitespace is flattened here rather than trusted.
        text = " ".join(beat["image_prompt"].split())
        if text != beat["image_prompt"].strip():
            collapsed += 1

        # Style is OURS, not the model's. Drop any block Claude wrote out of
        # habit - a paraphrased copy would compete with the real one, and the
        # whole point is that this text never varies between scenes or videos.
        cut = text.lower().find("style:")
        if cut != -1:
            text = text[:cut].rstrip(" .,;") + "."
            stripped += 1

        # Order matches the prompts that already worked: subject and action
        # first, then the place, then the style. Leading with the place buries
        # the subject a hundred words deep.
        loc = " ".join((beat.get("location") or "").split()).lower()
        loc_anchor = location_anchors.get(loc, "")
        if location_anchors and not loc_anchor:
            missing_anchor.append(index)
        anchor = " ".join(a for a in (loc_anchor, setting_anchor) if a)
        if anchor:
            anchored += 1

        lines.append(" ".join(part for part in (
            config.STYLE_PREFIX, _fragment(text), anchor, config.STYLE_BLOCK
        ) if part))

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Fallback descriptions, line-for-line with scenes.txt. Flow refuses a
    # prompt now and then; retrying the same words gets the same answer, so a
    # milder description of the same moment is what actually recovers it.
    alt_path = run_dir / "scenes_alt.txt"
    alts = [b.get("image_prompt_alt", "").strip() for b in beats]
    if any(alts):
        alt_lines = list(lines[:4])
        for beat, alt in zip(beats, alts):
            # Fall back to the primary when a beat has no alternate, so the
            # line numbering can never drift out of step.
            text = " ".join((alt or beat["image_prompt"]).split())
            cut = text.lower().find("style:")
            if cut != -1:
                text = text[:cut].rstrip(" .,;") + "."
            loc = " ".join((beat.get("location") or "").split()).lower()
            anchor = " ".join(a for a in (location_anchors.get(loc, ""),
                                          setting_anchor) if a)
            alt_lines.append(" ".join(part for part in (
                config.STYLE_PREFIX, _fragment(text), anchor, config.STYLE_BLOCK
            ) if part))
        alt_path.write_text("\n".join(alt_lines) + "\n", encoding="utf-8")
        print(f"[prompts] {sum(1 for a in alts if a)} fallback description(s) "
              f"-> {alt_path.name}")
    elif alt_path.exists():
        alt_path.unlink()

    print(f"[prompts] {len(beats)} beats -> {out_path}")
    print(f"[prompts] style block appended to all {len(beats)} "
          f"(identical every scene, every video)")
    if anchored:
        print(f"[prompts] location anchor injected into {anchored}/{len(beats)} "
              f"(byte-identical within each location)")
    if missing_anchor:
        shown = ",".join(str(n) for n in missing_anchor[:12])
        more = f" (+{len(missing_anchor) - 12})" if len(missing_anchor) > 12 else ""
        print(f"[warn] no matching plan.locations entry: {shown}{more}")
        print("       beat.location must match plan.locations[].name exactly; "
              "these beats carry no location description at all")
    if collapsed:
        print(f"[prompts] flattened whitespace in {collapsed} prompt(s)")
    if stripped:
        print(f"[prompts] replaced the model's own style block in {stripped} "
              f"prompt(s) with config.STYLE_BLOCK")

    longest = max(len(line) for line in lines[4:])
    typing_s = longest * 55 / 1000
    print(f"[prompts] longest prompt {longest} chars (~{typing_s:.0f}s to type)")

    _warn_off_spec(beats, data.get("format", ""))
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

# --- Two-tier rhythm (explainer) -------------------------------------------
# Video length fixes the total spoken words, so more beats does NOT mean more
# narration - it means the same words cut into smaller pieces. A 4.6 minute
# video is ~810 spoken words whether that is 45 beats or 90.
#
#   SHORT beat   4-8 words   ~2.0s   a consequence, a reaction, one hard image
#   LONG beat   10-15 words  ~4.1s   the information, the number, the turn
#
# Half and half averages ~9 words a beat, which is the ~3.0s per image this
# channel is now cut at, down from 6.2s.
#
# The MIX is the rule, not the shortness. Uniformly short beats are not a
# faster video, they are a faster metronome - and a metronome was the original
# complaint. So the checks below police the ratio and the runs, and only flag
# an individual beat when it is too long to sit under one still image.
RHYTHM_FORMATS = {"explainer"}
SHORT_MAX_WORDS = 8       # at or under this, a beat counts as SHORT
LONG_MAX_WORDS = 15       # over this, the image freezes while narration runs
MIN_WORDS = 4             # under this it does not register as a beat at all
SHORT_SHARE = (0.35, 0.65)  # acceptable fraction of SHORT beats
MAX_RUN_SHORT = 3         # more than this in a row reads as machine-gun
MAX_RUN_LONG = 2          # more than this in a row is the old slideshow

# Mirrors OUTRO_FRAMES in remotion/src/constants.ts (30 frames at 30fps):
# the hold on the last image after the final word.
OUTRO_HOLD_SECONDS = 1.0


def _check_rhythm(beats: list[dict], spoken_words, report) -> None:
    """
    Police the two-tier rhythm for RHYTHM_FORMATS.

    Deliberately does NOT warn on a beat merely for being short - short IS the
    format now. What it polices is the shape of the whole script: the ratio of
    short to long, and how many of either run back to back.
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

    shorts = [c <= SHORT_MAX_WORDS for c in counts]
    share = sum(shorts) / n
    lo_s, hi_s = SHORT_SHARE
    if share < lo_s:
        print(f"[warn] only {share:.0%} of beats are short "
              f"(want {lo_s:.0%}-{hi_s:.0%})")
        print("       too few short beats - this is still slideshow pacing")
    elif share > hi_s:
        print(f"[warn] {share:.0%} of beats are short "
              f"(want {lo_s:.0%}-{hi_s:.0%})")
        print("       nearly all short is a metronome, not a faster video")

    # Collapse the short/long sequence into runs so a stretch of six short
    # beats is reported once, as a range, not as six separate warnings.
    runs, start = [], 0
    for i in range(1, n + 1):
        if i == n or shorts[i] != shorts[start]:
            runs.append((shorts[start], start + 1, i))
            start = i

    for is_short, limit, why in (
        (True, MAX_RUN_SHORT,
         "break the run with a long beat - back-to-back short beats "
         "read as machine-gun"),
        (False, MAX_RUN_LONG,
         "insert a short beat - this stretch cuts at the old slow rate"),
    ):
        bad = [f"{a}-{b}" for s_, a, b in runs
               if s_ is is_short and b - a + 1 > limit]
        if bad:
            kind = "short" if is_short else "long"
            print(f"[warn] {len(bad)} run(s) of more than {limit} {kind} "
                  f"beats: {', '.join(bad[:8])}")
            print(f"       {why}")

    print(f"[prompts] rhythm: {sum(shorts)} short / {n - sum(shorts)} long, "
          f"avg {sum(counts) / n:.1f} words a beat")


def _warn_off_spec(beats: list[dict], fmt: str = "") -> None:
    """
    Flag beats that drift from the spec in prompts/pass1_narration.txt.

    Warnings, not errors - the script is still usable. But catching them here
    costs nothing, whereas noticing after a full Flow run costs hours.
    """
    # Emotion tags like [surprised] are spoken as delivery, not words.
    def spoken_words(text: str) -> int:
        import re
        return len(re.sub(r"\[[^\]]*\]", " ", text).split())

    key = fmt.strip().lower()
    rhythm = key in RHYTHM_FORMATS
    lo, hi = WORD_BANDS.get(key, DEFAULT_WORD_BAND)
    if fmt and rhythm:
        print(f"[prompts] format {fmt!r}: two-tier rhythm, "
              f"short <={SHORT_MAX_WORDS} words / long <={LONG_MAX_WORDS}")
    elif fmt:
        print(f"[prompts] format {fmt!r}: expecting {lo}-{hi} words per beat")

    short = [] if rhythm else [i for i, b in enumerate(beats, 1)
                               if spoken_words(b["narration"]) < lo]
    long_ = [] if rhythm else [i for i, b in enumerate(beats, 1)
                               if spoken_words(b["narration"]) > hi]
    no_ref = [i for i, b in enumerate(beats, 1)
              if "reference character" not in b["image_prompt"].lower()]

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

    copies = [i for i, b in enumerate(beats, 1)
              if b.get("image_prompt_alt")
              and flat(b["image_prompt_alt"]) == flat(b["image_prompt"])]
    missing_alt = [i for i, b in enumerate(beats, 1)
                   if not (b.get("image_prompt_alt") or "").strip()]

    report("no image_prompt_alt", missing_alt,
           "a refused beat has no second attempt and stops the run")
    report("image_prompt_alt identical to image_prompt", copies,
           "an identical retry gets refused identically - reword or restage it")

    # The reference art is a single front-facing pose. Ask for his back and the
    # model has nothing to work from, so it puts his face on a back-facing body
    # and the head comes out rotated 180 degrees.
    import re as _re2
    back_view = _re2.compile(
        r"(from behind|over[- ]the[- ]shoulder|over his shoulder|"
        r"back to the camera|seen from behind|from the back)", _re2.I)
    # A back view is fine as long as the prompt says there is no face on that
    # side. Without it the reference's front-facing head gets pasted on and
    # comes out rotated.
    no_face = _re2.compile(r"(no face|back of his (plain white )?head|"
                           r"face not visible)", _re2.I)
    backs = [i for i, b in enumerate(beats, 1)
             if back_view.search(b["image_prompt"])
             and not no_face.search(b["image_prompt"])]
    if backs:
        print(f"[warn] back view without a 'no face' clause: "
              f"{','.join(str(n) for n in backs)}")
        print("       add 'showing the back of his plain white head with no "
              "face', or his head comes out rotated")

    # Lighting and atmosphere words are STYLE instructions wearing a scene
    # description's clothes. "grey overcast light" tells the model how to
    # RENDER, and it renders photographically. Combined with a real-world
    # subject it produced an actual photograph with the character pasted on.
    import re as _re
    render_words = _re.compile(
        r"\b(overcast|lighting|lamplight|backlit|glow\w*|shadowy|haze|hazy|"
        r"blurred|out of focus|depth of field|gleaming|shimmer\w*|"
        r"realistic|detailed|photo\w*|cinematic)\b", _re.I)
    risky = [(i, sorted(set(w.lower() for w in render_words.findall(b["image_prompt"]))))
             for i, b in enumerate(beats, 1)]
    risky = [(i, w) for i, w in risky if w]
    if risky:
        print("[warn] render/lighting words (these push the image photographic):")
        for i, words in risky[:8]:
            print(f"       beat {i}: {', '.join(words)}")
        print("       describe WHAT is there, not how it is lit or rendered")

    total_words = sum(spoken_words(b["narration"]) for b in beats)
    narration_s = total_words / WORDS_PER_MINUTE * 60 / config.NARRATION_SPEED

    # The finished video is longer than its narration. Every hard cut adds a
    # breath that no transition eats (config.CUT_PAD_SECONDS), and the pipeline
    # bolts on an outro beat afterwards. A dissolve costs nothing - its tail is
    # consumed by the overlap - so only same-location boundaries are counted.
    locations = [" ".join((b.get("location") or "").split()) for b in beats]
    hard_cuts = sum(1 for a, b in zip(locations, locations[1:]) if a and a == b)
    pad_s = hard_cuts * config.CUT_PAD_SECONDS
    outro_s = (OUTRO_HOLD_SECONDS + 2.1) if config.OUTRO_ENABLED else 0.0

    est = narration_s + pad_s + outro_s
    per_beat = narration_s / len(beats) if beats else 0
    print(f"[prompts] ~{total_words} spoken words, {narration_s:.0f}s narration "
          f"+ {pad_s:.0f}s cut pads + {outro_s:.0f}s outro")
    print(f"[prompts] estimated final video {est:.0f}s ({est / 60:.1f} min)")
    print(f"[prompts] ~{per_beat:.1f}s per image across {len(beats)} beats")

    # Catch a script that is the wrong LENGTH while it is still just text. The
    # alternative is finding out after a full Flow run and a full TTS run.
    target = getattr(config, "TARGET_VIDEO_SECONDS", 0.0)
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
    run_dir = resolve_run(args.run)
    scenes = run_dir / "scenes.txt"
    if not scenes.exists():
        raise SystemExit(f"No scenes.txt in {run_dir}. Run: python pipeline.py prompts")

    images_dir = run_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    # Don't open a browser for nothing. flow_runner launches Chrome before it
    # works out which scenes are already done, so on a re-run of `all` this
    # would pop a window, log in, attach the reference and then skip every
    # scene. Checking here keeps a resumed run silent.
    if not args.only:
        beats = load_script(run_dir)["beats"]
        todo = [i for i in range(1, len(beats) + 1)
                if find_image(run_dir, i) is None]
        if not todo:
            print(f"[images] all {len(beats)} already present, skipping Flow")
            return 0
        print(f"[images] {len(todo)} of {len(beats)} still to generate")

    cmd = [sys.executable, str(FLOW_RUNNER),
           "--scenes", str(scenes.resolve()),
           "--output", str(images_dir.resolve())]
    alt = run_dir / "scenes_alt.txt"
    if alt.exists():
        cmd += ["--alt-scenes", str(alt.resolve())]
    if args.only:
        cmd += ["--only", args.only]

    print(f"[images] handing off to flow_runner -> {images_dir}")
    return subprocess.run(cmd, cwd=str(FLOW_RUNNER.parent)).returncode


# --- voice -----------------------------------------------------------------

def cmd_voice(args) -> int:
    """
    NOT YET VALIDATED against the live ElevenLabs SDK. Run one beat first
    (--limit 1) before spending credits on a full script.
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
    run_dir = resolve_run(args.run)
    beats = load_script(run_dir)["beats"]

    missing_images, missing_audio = [], []
    for index in range(1, len(beats) + 1):
        if find_image(run_dir, index) is None:
            missing_images.append(index)
        if find_audio(run_dir, index) is None:
            missing_audio.append(index)

    have_i = len(beats) - len(missing_images)
    have_a = len(beats) - len(missing_audio)
    print(f"\nrun     : {run_dir.name}")
    print(f"beats   : {len(beats)}")
    print(f"images  : {have_i}/{len(beats)}")
    print(f"audio   : {have_a}/{len(beats)}")

    def summarise(label, missing, fix):
        if not missing:
            return True
        shown = ",".join(str(n) for n in missing[:15])
        more = f" (+{len(missing) - 15} more)" if len(missing) > 15 else ""
        print(f"\nmissing {label}: {shown}{more}")
        print(f"  {fix}")
        return False

    ok = summarise("images", missing_images,
                   f"python pipeline.py images --only "
                   f"{','.join(str(n) for n in missing_images[:15])}")
    ok &= summarise("audio", missing_audio, "python pipeline.py voice")

    if ok:
        print("\nEverything present. Next: python pipeline.py manifest")
    return 0 if ok else 1


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


def cmd_manifest(args) -> int:
    run_dir = resolve_run(args.run)
    beats = load_script(run_dir)["beats"]
    audio_dir = run_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    entries, missing = [], []
    for index, beat in enumerate(beats, start=1):
        image = find_image(run_dir, index)
        if image is None:
            missing.append(index)
            continue

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
            "audio": f"audio/{audio.name}",
            "duration": round(duration, 3),
            # Carried so the render can tell a cut WITHIN a place from a move
            # BETWEEN places: same location cuts hard, a change dissolves.
            # See remotion/src/compositions/LectureVideo.tsx.
            "location": " ".join((beat.get("location") or "").split()),
        }


        entries.append(entry)

    if missing:
        shown = ",".join(str(n) for n in missing[:15])
        more = f" (+{len(missing) - 15} more)" if len(missing) > 15 else ""
        print(f"Missing assets for beat(s): {shown}{more}")
        print("Run `python pipeline.py check` for detail, or pass --silent 5")
        print("to build a picture-only manifest for a render test.")
        return 1

    # Appended as an ordinary beat, so it cuts or dissolves in and gets
    # subtitles like any other. The script never mentions the channel - that
    # stays banned in pass1_narration.txt - the outro is bolted on here instead.
    if config.OUTRO_ENABLED and not args.silent:
        assets = _outro_assets()
        if assets:
            image_src, audio_src = assets
            import shutil
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

    path = run_dir / "manifest.json"
    path.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    # Crossfades do NOT shorten the video: each beat carries a crossfade-length
    # tail that its transition consumes, so the two cancel. The real length is
    # the sum of the audio plus the outro hold. This used to subtract the
    # overlap and reported a video ~8s shorter than it actually was.
    total = sum(e["duration"] for e in entries) + OUTRO_HOLD_SECONDS
    print(f"[manifest] {len(entries)} beats -> {path}")
    print(f"[manifest] final video {total:.1f}s ({total / 60:.1f} min)")
    if args.silent:
        print(f"[manifest] SILENT placeholder audio at {args.silent}s per beat")
    print(f"\nNext:  python pipeline.py music")
    return 0


# --- demo ------------------------------------------------------------------
#
# A full dry run: script, images and audio all fabricated locally so the video
# can be watched end to end without touching Flow or ElevenLabs. Exists to test
# the things that are easy to get wrong and expensive to discover late -
# subtitle timing and legibility, Ken Burns framing, crossfades, and whether
# image N really is paired with narration N.

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
    import colorsys
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

    # Corner marks make the Ken Burns crop visible: if a corner drifts out of
    # frame you can see exactly how much the zoom is eating.
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

    import shutil
    for i, beat in enumerate(beats, start=1):
        if supplied:
            src = supplied[(i - 1) % len(supplied)]
            shutil.copy(src, run_dir / "images" / f"scene_{i:03}{src.suffix.lower()}")
        else:
            _demo_image(run_dir / "images" / f"scene_{i:03}.png", i, count,
                        beat["narration"])

    # Silence, but sized per beat from its own word count rather than a flat
    # number. Uniform durations would hide exactly the subtitle timing problems
    # this is meant to expose.
    #
    # Uses the same measured words-per-minute the length estimator does, so a
    # demo render comes out the length a real run of the same script would.
    import re
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


# --- music -----------------------------------------------------------------

def cmd_music(args) -> int:
    """
    Compose this video's bed from the script's own music_prompt.

    Runs after manifest because it needs the finished length. Skipped silently
    when the script carries no music_prompt - the shared bed in assets/music/
    then covers it, and a missing bed is never fatal.
    """
    run_dir = resolve_run(args.run)
    data = load_script(run_dir)
    prompt = (data.get("music_prompt") or "").strip()
    out_path = run_dir / "music.mp3"

    if not config.MUSIC_ENABLED or not config.MUSIC_PER_VIDEO:
        print("[music] per-video music is off")
        return 0
    if not prompt:
        print("[music] script has no 'music_prompt', using assets/music/ if present")
        return 0
    if out_path.exists() and not args.force:
        print(f"[music] {out_path.name} already exists (--force to redo)")
        return 0

    manifest = run_dir / "manifest.json"
    if not manifest.exists():
        raise SystemExit("Run `python pipeline.py manifest` first - music needs "
                         "the finished video length.")
    entries = json.loads(manifest.read_text())
    seconds = sum(e["duration"] for e in entries) + OUTRO_HOLD_SECONDS

    from modules import music_generator
    print(f"[music] composing {seconds:.0f}s for: {prompt[:60]}...")
    try:
        path = music_generator.generate(prompt, seconds, out_path)
    except Exception as exc:
        print(f"[music] failed ({type(exc).__name__}: {exc})")
        print("[music] continuing without a per-video bed")
        return 0
    print(f"[music] {path.name} ({path.stat().st_size // 1024} KB)")
    return 0


# --- render ----------------------------------------------------------------

def cmd_render(args) -> int:
    from modules import video_editor

    run_dir = resolve_run(args.run)
    manifest = run_dir / "manifest.json"
    if not manifest.exists():
        raise SystemExit(f"No manifest.json in {run_dir}. Run: pipeline.py manifest")

    # A missing bed is not fatal, so this warns rather than stops. But it is
    # worth shouting about: the music stage sits between manifest and render,
    # so driving the stages by hand skips it easily, and the result is a
    # finished video with no music that looks like a completely normal success.
    if ((load_script(run_dir).get("music_prompt") or "").strip()
            and not (run_dir / "music.mp3").exists()):
        print("[render] WARNING: this script has a music_prompt but there is "
              "no music.mp3 in the run folder.")
        print("[render] Run `python pipeline.py music` first, or the narration "
              "renders with no bed under it.")

    final = video_editor.render(manifest, run_dir)
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
        ("music", cmd_music),
        ("render", cmd_render),
    ]

    import time as _time
    started = _time.monotonic()
    timings = []

    for i, (name, func) in enumerate(stages, start=1):
        print(f"\n{'=' * 60}\n[{i}/{len(stages)}] {name}\n{'=' * 60}")
        stage_started = _time.monotonic()
        code = func(args)
        timings.append((name, _time.monotonic() - stage_started))
        if code:
            print(f"\nStopped at '{name}'. Fix the above, then run again - "
                  f"finished work is kept and will be skipped.")
            return code

    total = _time.monotonic() - started
    print(f"\n{'=' * 60}")
    print(f"DONE -> {run_dir / 'final.mp4'}")
    print(f"{'=' * 60}")
    for name, seconds in timings:
        share = seconds / total * 100 if total else 0
        print(f"  {name:<9} {_fmt(seconds):>9}  {share:4.0f}%")
    print(f"  {'TOTAL':<9} {_fmt(total):>9}")
    print("=" * 60)
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

    with_run("prompts", "script.json -> scenes.txt", cmd_prompts)

    sp = with_run("images", "generate images via Flow", cmd_images)
    sp.add_argument("--only", help="comma-separated scene numbers")

    sp = with_run("voice", "narration via ElevenLabs", cmd_voice)
    sp.add_argument("--limit", type=int, help="only the first N beats")
    sp.add_argument("--force", action="store_true", help="redo existing clips")
    sp.add_argument("--voice", default=config.ELEVENLABS_DEFAULT_VOICE,
                    choices=sorted(config.ELEVENLABS_VOICES))
    sp.add_argument("--lang", default="en",
                    help="ru/es route through multilingual_v2 instead of v3")

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

    sp = with_run("music", "compose this video's bed from its music_prompt",
                  cmd_music)
    sp.add_argument("--force", action="store_true", help="recompose the bed")

    sp = with_run("all", "every stage in order (same as no subcommand)", cmd_all)
    sp.set_defaults(only=None, limit=None, force=False, lang="en", silent=None, voice=config.ELEVENLABS_DEFAULT_VOICE)

    with_run("render", "Remotion -> final.mp4", cmd_render)

    args = parser.parse_args()
    prevent_sleep()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
