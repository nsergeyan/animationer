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
  "topic": "cricket-explained",
  "format": "explainer",
  "plan": {
    "spine_question": "How can a game last five days and end in a draw, and how does cricket actually work?",
    "deflations": [
      {
        "assumed": "Cricket is just a confusing British version of baseball.",
        "actual": "Cricket is a massive global sport with completely unique rules and three distinct formats.",
        "who_decided": "The evolution of the sport over centuries and its massive adoption in South Asia.",
        "build_beat": "From far away, cricket looks like baseball.",
        "drop_beat": "[flatly] After that, almost nothing is the same."
      }
    ],
    "cast": [
      {
        "name": "Jasprit Bumrah",
        "why": "Star fast bowler for India who dominated the 2026 T20 World Cup."
      },
      {
        "name": "Virat Kohli",
        "why": "India's biggest star, now plays only One Day cricket after quitting Tests and T20s."
      },
      {
        "name": "Aiden Markram",
        "why": "South African batter who scored a historic 136 in the 2025 WTC Final."
      },
      {
        "name": "Pat Cummins",
        "why": "Australian captain who led his team to the 2023 World Cup victory."
      }
    ],
    "specifics": [
      {
        "fact": "India beat New Zealand by 96 runs in the 2026 T20 World Cup final in Ahmedabad, the biggest margin in a T20 World Cup final.",
        "source": "newsonair.gov.in, 8 March 2026",
        "beat": "They beat New Zealand by ninety six runs in the final."
      },
      {
        "fact": "Bumrah took 14 wickets, most of the tournament, 4/15 in the final.",
        "source": "T20 World Cup 2026 statistics",
        "beat": "He got fourteen batters out, more than anyone."
      },
      {
        "fact": "South Africa beat Australia in the 2025 WTC final at Lord's, Markram 136.",
        "source": "ICC WTC 2025 final",
        "beat": "Aiden Markram scored one hundred thirty six runs."
      },
      {
        "fact": "Australia beat India in the 2023 ODI World Cup final in Ahmedabad, Cummins captain, their sixth title.",
        "source": "ICC 2023 Cricket World Cup",
        "beat": "Australia has won this World Cup six times."
      }
    ],
    "facts_to_check": [
      {
        "claim": "India won 2026 T20 WC by 96 runs, biggest final margin; Bumrah 14 wickets, 4 in final",
        "source": "newsonair.gov.in, ratopati, navbharatlive"
      },
      {
        "claim": "South Africa won 2025 WTC final vs Australia at Lord's, Markram 136",
        "source": "ICC"
      },
      {
        "claim": "Australia six ODI World Cups, 2023 final vs India in Ahmedabad",
        "source": "ICC"
      },
      {
        "claim": "Narendra Modi Stadium, Ahmedabad: world's largest cricket stadium, about 132,000 capacity",
        "source": "Wikipedia / GCA"
      },
      {
        "claim": "Twenty20 started in England in 2003",
        "source": "ECB / Wikipedia"
      },
      {
        "claim": "Ten ways of being out in the Laws of Cricket",
        "source": "MCC Laws of Cricket"
      },
      {
        "claim": "Kohli quit T20Is 2024 and Tests May 2025, ODI only, aged 37, aims for 2027 World Cup",
        "source": "crictracker, cricket.com"
      },
      {
        "claim": "Kohli is the most followed cricketer on Instagram",
        "source": "Instagram"
      }
    ],
    "locations": [
      {"name": "the five day test match", "visual_anchor": "", "music": "playful"},
      {"name": "the batting crease", "visual_anchor": "", "music": "calm"},
      {"name": "the run scoring outfield", "visual_anchor": "", "music": "playful"},
      {"name": "lord's in london", "visual_anchor": "", "music": "calm"},
      {"name": "the comment break", "visual_anchor": "", "music": "calm"},
      {"name": "the twenty twenty final", "visual_anchor": "", "music": "building"},
      {"name": "the ahmedabad stadium", "visual_anchor": "", "music": "calm"},
      {"name": "the indian fan lane", "visual_anchor": "", "music": "playful"},
      {"name": "the centre pitch", "visual_anchor": "", "music": "calm"}
    ],
    "setting_anchor": ""
  },
  "beats": [
    {
      "narration": "[curious] A cricket match can last five days.",
      "location": "the five day test match",
      "image_prompt": "reference character sits at frame left, curious, watching Virat Kohli, a brown-skinned batter with a thick dark beard in a white shirt with the number 18, standing at three tan wooden stumps, wide shot",
      "image_prompt_alt": "reference character sits cross-legged in the foreground, curious, as a fit medium-height brown-skinned man with short spiky dark hair, a batter with a thick dark beard in a white shirt with the number 18, waits at three tan wooden stumps, medium-wide shot"
    },
    {
      "narration": "They stop for lunch.",
      "location": "the five day test match",
      "edits": [
        "one big white plate holding one red apple appears at frame right, the batter turning toward it"
      ]
    },
    {
      "narration": "They stop again for tea.",
      "location": "the five day test match",
      "edits": [
        "the plate disappears and one big blue teacup appears at frame right in its place"
      ]
    },
    {
      "narration": "[deadpan] And then it can end in a draw.",
      "location": "the five day test match",
      "edits": [
        "the teacup disappears and a big sign reading \"DRAW\" appears above the stumps, the character's jaw dropping"
      ]
    },
    {
      "narration": "From far away, cricket looks like baseball.",
      "location": "the five day test match",
      "image_prompt": "reference character stands at frame right squinting, skeptical, at one doodle baseball player in a red cap beside one doodle cricket batter in white, long shot",
      "image_prompt_alt": "reference character leans in from the foreground left, skeptical, eyeing one doodle baseball player in a red cap and one doodle cricket batter in white side by side, medium shot"
    },
    {
      "narration": "One player throws a ball.",
      "location": "the five day test match",
      "edits": [
        "the baseball player throws one small white ball across to the cricket batter beside him"
      ]
    },
    {
      "narration": "Another player hits it.",
      "location": "the five day test match",
      "edits": [
        "the cricket batter swings his flat bat and the white ball flies off upward"
      ]
    },
    {
      "narration": "[flatly] After that, almost nothing is the same.",
      "location": "the five day test match",
      "edits": [
        "the baseball player disappears and the character folds his arms, flat-faced"
      ]
    },
    {
      "narration": "Two teams of eleven players share one big field.",
      "location": "the batting crease",
      "image_prompt": "reference character stands at frame center, attentive, between three doodle players in blue shirts at frame left and three doodle players in yellow shirts at frame right, wide shot",
      "image_prompt_alt": "reference character stands in the foreground, mildly curious, as three doodle players in blue shirts face three doodle players in yellow shirts across the page behind him, high-angle shot"
    },
    {
      "narration": "The batter holds a wide, flat wooden bat.",
      "location": "the batting crease",
      "edits": [
        "both groups disappear and a real photo cutout of a cricket bat, roughly pasted onto the drawing, stands big beside the character"
      ]
    },
    {
      "narration": "Behind him stand three wooden sticks called stumps.",
      "location": "the batting crease",
      "edits": [
        "three tall wooden stumps appear at frame right of the bat, as tall as the character's chest"
      ]
    },
    {
      "narration": "Two tiny pieces called bails sit on top.",
      "location": "the batting crease",
      "edits": [
        "two tiny red bails appear lying across the tops of the three stumps"
      ]
    },
    {
      "narration": "Together they make the wicket.",
      "location": "the batting crease",
      "edits": [
        "a big sign reading \"WICKET\" appears above the stumps, the character pointing at it"
      ]
    },
    {
      "narration": "The bowler runs in and delivers a hard leather ball.",
      "location": "the batting crease",
      "image_prompt": "reference character stands beside three wooden stumps at frame right, attentive, as Jasprit Bumrah, a brown-skinned slim fast bowler with a short black beard in a blue shirt with the number 93, runs in with one red ball, wide shot",
      "image_prompt_alt": "reference character crouches beside three wooden stumps in the foreground, attentive, watching a slim medium-height brown-skinned man with short black hair, a slim fast bowler with a short black beard in a blue shirt with the number 93, sprint in with one red leather ball, low-angle shot"
    },
    {
      "narration": "His arm must stay straight.",
      "location": "the batting crease",
      "edits": [
        "the bowler's right arm swings straight up above his head, stiff as a stick"
      ]
    },
    {
      "narration": "[deadpan] Throwing it is illegal.",
      "location": "the batting crease",
      "edits": [
        "a big sign reading \"NO THROWING\" appears above the bowler's straight arm, the character nodding"
      ]
    },
    {
      "narration": "Usually the ball bounces once before it reaches the batter.",
      "location": "the batting crease",
      "edits": [
        "the sign disappears and the red ball bounces once halfway to the stumps, a dotted line tracing its path"
      ]
    },
    {
      "narration": "The bounce can send it anywhere.",
      "location": "the batting crease",
      "edits": [
        "the dotted line zigzags wildly off toward the top of the frame and the character's eyes go wide"
      ]
    },
    {
      "narration": "The batting team wants runs.",
      "location": "the run scoring outfield",
      "image_prompt": "reference character stands at frame left, curious, watching Virat Kohli, a brown-skinned batter with a thick dark beard in a white shirt with the number 18, beside one doodle partner batter in white, both holding red-handled bats, medium-wide shot",
      "image_prompt_alt": "reference character peeks in from frame right, curious, at a fit medium-height brown-skinned man with short spiky dark hair, a batter with a thick dark beard in a white shirt with the number 18, beside one doodle partner batter in white, both holding red-handled bats, wide shot"
    },
    {
      "narration": "After a hit, the two batters can run between the wickets.",
      "location": "the run scoring outfield",
      "edits": [
        "both batters sprint past each other across the page, bats stretched out in front"
      ]
    },
    {
      "narration": "Each trip is one run.",
      "location": "the run scoring outfield",
      "edits": [
        "a big tag reading \"1 RUN\" appears above the two batters, the character holding up one finger"
      ]
    },
    {
      "narration": "[calm] But hitting it far is better.",
      "location": "the run scoring outfield",
      "edits": [
        "the tag and the partner batter disappear and the bearded batter swings his bat in a huge arc"
      ]
    },
    {
      "narration": "If the ball reaches the rope, that is four runs.",
      "location": "the run scoring outfield",
      "image_prompt": "reference character crouches at frame left, interested, beside one long white rope across the page, one red leather ball rolling up against it, low wide shot",
      "image_prompt_alt": "reference character kneels at frame right, interested, watching one red leather ball roll to a stop against one long white rope stretched across the page, medium shot"
    },
    {
      "narration": "If it flies over the rope, that is six.",
      "location": "the run scoring outfield",
      "edits": [
        "the red ball becomes a real photo cutout of a cricket ball, roughly pasted onto the drawing, flying high over the rope"
      ]
    },
    {
      "narration": "The fielding team wants the batters out.",
      "location": "the run scoring outfield",
      "edits": [
        "the rope disappears and one doodle fielder in a navy shirt sprints in from frame right, arms open, toward the ball"
      ]
    },
    {
      "narration": "[understated] There are ten ways to do it.",
      "location": "the run scoring outfield",
      "edits": [
        "the ball disappears and a big sign reading \"10 WAYS\" appears above the fielder"
      ]
    },
    {
      "narration": "The ball can knock the bails off.",
      "location": "the run scoring outfield",
      "edits": [
        "the sign and the fielder disappear and three wooden stumps appear at frame right, their two red bails flying off"
      ]
    },
    {
      "narration": "Or a fielder catches the ball before it lands.",
      "location": "the run scoring outfield",
      "image_prompt": "reference character stands at frame right, eyes wide, as one diving doodle fielder in a navy shirt catches one red leather ball just above the page, medium shot",
      "image_prompt_alt": "reference character watches from the foreground left, eyes wide, while one doodle fielder in a navy shirt dives full length to grab one red leather ball, wide shot"
    },
    {
      "narration": "An out batter walks off and the next one comes in.",
      "location": "the run scoring outfield",
      "edits": [
        "the fielder and the ball disappear and one doodle batter in white walks off toward frame left, head down"
      ]
    },
    {
      "narration": "Ten outs end the team's innings.",
      "location": "the run scoring outfield",
      "edits": [
        "a big tag reading \"10 OUT\" appears above the walking batter"
      ]
    },
    {
      "narration": "[thoughtful] Why not eleven?",
      "location": "the run scoring outfield",
      "edits": [
        "the tag disappears and the character scratches his head, one eyebrow raised"
      ]
    },
    {
      "narration": "The last batter has no partner to run with.",
      "location": "the run scoring outfield",
      "edits": [
        "the walking batter turns around and stands alone at frame left, shrugging"
      ]
    },
    {
      "narration": "Then the two teams swap roles.",
      "location": "the run scoring outfield",
      "edits": [
        "one doodle fielder in a navy shirt appears beside the lone batter, who hands him his bat"
      ]
    },
    {
      "narration": "Cricket comes in three formats.",
      "location": "lord's in london",
      "image_prompt": "reference character stands at frame left, attentive, before a row of red alarm clocks, one huge, one medium, one tiny, wide shot",
      "image_prompt_alt": "reference character sits on the page at frame right, attentive, looking at a row of red alarm clocks shrinking from huge to medium to tiny, high-angle shot"
    },
    {
      "narration": "Test cricket is the oldest.",
      "location": "lord's in london",
      "edits": [
        "the medium and tiny clocks disappear and the huge red clock grows a long white beard"
      ]
    },
    {
      "narration": "[peaceful] The players wear all white.",
      "location": "lord's in london",
      "edits": [
        "one doodle player in all-white cricket clothes appears at frame right beside the huge clock"
      ]
    },
    {
      "narration": "This is the five day format from the start.",
      "location": "lord's in london",
      "edits": [
        "a big tag reading \"5 DAYS\" hangs from the huge clock, the character's eyebrows rising"
      ]
    },
    {
      "narration": "South Africa won the World Test Championship in twenty twenty five.",
      "location": "lord's in london",
      "image_prompt": "reference character stands at frame right, warmly interested, watching a real photo cutout of Aiden Markram, roughly pasted onto the drawing, a tall batter with a short brown beard in white and a green cap, raising his bat, medium shot",
      "image_prompt_alt": "reference character stands in the foreground left, warmly interested, as a tall light-skinned man with short brown hair, a tall batter with a short brown beard in white and a green cap, raises his bat high, low-angle shot"
    },
    {
      "narration": "They beat Australia in the final at Lord's in London.",
      "location": "lord's in london",
      "edits": [
        "one doodle bowler in white with a yellow helmet appears at frame left, sitting slumped"
      ]
    },
    {
      "narration": "Aiden Markram scored one hundred thirty six runs.",
      "location": "lord's in london",
      "edits": [
        "the slumped bowler disappears and a big tag reading \"136\" appears above the raised bat"
      ]
    },
    {
      "narration": "A good batter can stay in all day.",
      "location": "lord's in london",
      "edits": [
        "the tag disappears and one big yellow sun appears at top right, the character's eyelids drooping sleepily"
      ]
    },
    {
      "narration": "[curious] Quick question before we go on.",
      "location": "the comment break",
      "image_prompt": "reference character stands alone at frame center facing the viewer, holding up one big blank white sign with one large black question mark, medium shot",
      "image_prompt_alt": "reference character faces the viewer at frame center, lifting one big blank white sign showing one large black question mark above his head, medium-wide shot"
    },
    {
      "narration": "Which sport is next?",
      "location": "the comment break",
      "edits": [
        "the character points down toward the bottom edge of the frame"
      ]
    },
    {
      "narration": "Write it in the comments.",
      "location": "the comment break",
      "edits": [
        "the character gives a small nod, still pointing down"
      ]
    },
    {
      "narration": "[deadpan] Not everyone has five days free.",
      "location": "the twenty twenty final",
      "image_prompt": "reference character slumps at frame left, tired, staring at one huge red alarm clock ringing beside him, medium shot",
      "image_prompt_alt": "reference character sits slouched in the foreground right, tired, as one huge red alarm clock rings wildly at frame left, wide shot"
    },
    {
      "narration": "So England invented Twenty Twenty cricket in two thousand three.",
      "location": "the twenty twenty final",
      "edits": [
        "the clock shrinks to half size and a big sign reading \"T20\" appears at frame right"
      ]
    },
    {
      "narration": "Each team gets just one hundred twenty balls.",
      "location": "the twenty twenty final",
      "edits": [
        "the sign disappears and a real photo cutout of a white cricket ball, roughly pasted onto the drawing, sits big at the character's feet"
      ]
    },
    {
      "narration": "A match takes three hours.",
      "location": "the twenty twenty final",
      "edits": [
        "the clock's hands spin round fast and the character's eyes go wide"
      ]
    },
    {
      "narration": "Players wear bright team colors.",
      "location": "the twenty twenty final",
      "edits": [
        "the ball disappears and one doodle batter in a bright blue shirt appears at frame right"
      ]
    },
    {
      "narration": "Batters swing at almost everything.",
      "location": "the twenty twenty final",
      "edits": [
        "the blue batter swings his bat wildly in a full circle, motion lines around him"
      ]
    },
    {
      "narration": "India won this format's World Cup in March twenty twenty six.",
      "location": "the twenty twenty final",
      "image_prompt": "reference character stands at frame left, impressed, watching a real photo cutout of Jasprit Bumrah, roughly pasted onto the drawing, a slim fast bowler with a short black beard in a blue shirt, leaping with both arms up, medium-wide shot",
      "image_prompt_alt": "reference character stands at frame right, impressed, as a slim medium-height brown-skinned man with short black hair, a slim fast bowler with a short black beard in a blue shirt with the number 93, leaps with both arms up, low-angle shot"
    },
    {
      "narration": "They beat New Zealand by ninety six runs in the final.",
      "location": "the twenty twenty final",
      "edits": [
        "one doodle batter in an all-black shirt appears at frame right, slumped and walking away"
      ]
    },
    {
      "narration": "[understated] No final had ever been that one sided.",
      "location": "the twenty twenty final",
      "edits": [
        "a big tag reading \"96 RUNS\" appears above the black-shirted batter, the character's jaw dropping"
      ]
    },
    {
      "narration": "Their star is fast bowler Jasprit Bumrah.",
      "location": "the twenty twenty final",
      "edits": [
        "the tag and the black-shirted batter disappear and a big yellow star appears above the photo cutout bowler"
      ]
    },
    {
      "narration": "He got fourteen batters out, the most of anyone.",
      "location": "the twenty twenty final",
      "edits": [
        "a big tag reading \"14 OUT\" appears beside the bowler and the character's eyes go wide"
      ]
    },
    {
      "narration": "The third format sits in the middle.",
      "location": "the ahmedabad stadium",
      "image_prompt": "reference character sits on the page at frame left, curious, one huge red alarm clock towering at frame right beside one tiny red alarm clock, low-angle shot",
      "image_prompt_alt": "reference character stands at frame right, curious, glancing between one tiny red alarm clock at his feet and one huge red alarm clock at frame left, wide shot"
    },
    {
      "narration": "[calm] One Day games give each team three hundred balls.",
      "location": "the ahmedabad stadium",
      "edits": [
        "both clocks disappear and one medium red alarm clock appears beside the character, a big tag reading \"300 BALLS\" on it"
      ]
    },
    {
      "narration": "A match lasts about eight hours.",
      "location": "the ahmedabad stadium",
      "edits": [
        "the tag disappears and the medium clock's hands creep round as the character yawns"
      ]
    },
    {
      "narration": "Australia has won this World Cup six times.",
      "location": "the ahmedabad stadium",
      "edits": [
        "one doodle player in a bright yellow shirt appears at frame right, both arms raised"
      ]
    },
    {
      "narration": "The latest was in twenty twenty three.",
      "location": "the ahmedabad stadium",
      "edits": [
        "the yellow player jumps high in celebration and the character gives a small nod"
      ]
    },
    {
      "narration": "Pat Cummins was captain.",
      "location": "the ahmedabad stadium",
      "image_prompt": "reference character stands at frame right, attentive, watching a real photo cutout of Pat Cummins, roughly pasted onto the drawing, a tall dark-haired fast bowler in a yellow shirt, arms folded, medium shot",
      "image_prompt_alt": "reference character stands in the foreground left, attentive, beside a tall lean light-skinned man with short wavy dark hair, a tall dark-haired fast bowler in a yellow shirt with the number 30, arms folded, wide shot"
    },
    {
      "narration": "They beat India in the final, in Ahmedabad.",
      "location": "the ahmedabad stadium",
      "edits": [
        "three doodle fans in blue shirts appear at frame left, slumping with heads down"
      ]
    },
    {
      "narration": "[softly] The home crowd went quiet.",
      "location": "the ahmedabad stadium",
      "edits": [
        "the three blue fans sit down silently and the character looks down softly"
      ]
    },
    {
      "narration": "That stadium is the biggest cricket ground in the world.",
      "location": "the ahmedabad stadium",
      "edits": [
        "the photo cutout man disappears and one huge grey round stadium outline rises behind the fans, towering over the character"
      ]
    },
    {
      "narration": "It holds about one hundred thirty thousand people.",
      "location": "the ahmedabad stadium",
      "edits": [
        "a big tag reading \"130,000\" hangs from the stadium rim, the character's eyes going wide"
      ]
    },
    {
      "narration": "[thoughtful] In India, cricket is close to a religion.",
      "location": "the indian fan lane",
      "image_prompt": "reference character stands at frame right, amused, as three doodle fans in blue shirts bow toward a real photo cutout of Virat Kohli, roughly pasted onto the drawing, a batter with a thick dark beard in a white shirt, medium shot",
      "image_prompt_alt": "reference character stands at frame left, amused, as three doodle fans in blue shirts bow toward a fit medium-height brown-skinned man with short spiky dark hair, a batter with a thick dark beard in a white shirt with the number 18, wide shot"
    },
    {
      "narration": "Its king is Virat Kohli.",
      "location": "the indian fan lane",
      "edits": [
        "a big sign reading \"KING\" appears above the photo cutout man"
      ]
    },
    {
      "narration": "He has quit Test and Twenty Twenty cricket.",
      "location": "the indian fan lane",
      "edits": [
        "the sign disappears and the character waves goodbye toward the photo cutout man"
      ]
    },
    {
      "narration": "Now he only plays One Day games.",
      "location": "the indian fan lane",
      "edits": [
        "a big tag reading \"ODI ONLY\" appears beside the photo cutout man, the character nodding"
      ]
    },
    {
      "narration": "At thirty seven, he still wants the next World Cup.",
      "location": "the indian fan lane",
      "edits": [
        "the tag disappears and a big tag reading \"37\" and a small golden trophy appear above the photo cutout man"
      ]
    },
    {
      "narration": "[light chuckle] No cricketer has more Instagram followers.",
      "location": "the indian fan lane",
      "edits": [
        "one big red heart appears above the photo cutout man and the character chuckles"
      ]
    },
    {
      "narration": "Five days, eight hours, or three hours.",
      "location": "the centre pitch",
      "image_prompt": "reference character stands at frame center, thoughtful, one huge red alarm clock at frame left and one tiny red alarm clock at frame right, wide shot at eye level",
      "image_prompt_alt": "reference character sits in the foreground, thoughtful, looking up at one huge red alarm clock and one tiny red alarm clock side by side, high-angle shot"
    },
    {
      "narration": "It is all one fight.",
      "location": "the centre pitch",
      "edits": [
        "both clocks disappear and one doodle bowler in white faces one doodle batter in white, both glaring"
      ]
    },
    {
      "narration": "The bowler tries to hit three wooden sticks.",
      "location": "the centre pitch",
      "edits": [
        "the batter disappears and a real photo cutout of three cricket stumps, roughly pasted onto the drawing, stands big at frame right as the bowler aims"
      ]
    },
    {
      "narration": "[content] The batter guards them with a flat piece of wood.",
      "location": "the centre pitch",
      "edits": [
        "the bowler disappears and one doodle batter in white stands guarding the stumps, flat bat raised, the character smiling"
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
                frame["alt"] = None
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


def cmd_prompts(args) -> int:
    """Turn script.json into frames.json and warn about anything off-spec."""
    run_dir = resolve_run(args.run)
    data = load_script(run_dir)
    music_moods(data)   # stops here on a bad mood, before any images are made
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
    if alts:
        print(f"[prompts] {alts} fallback description(s) for refused prompts")

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
# minutes. Replaces the two-tier 3-6 / 8-12 split (2026-10-07), which pass2
# then cut into a picture every ~1.1s - too fast. Before that, 4-8 / 10-15.
#
# The MIX is the rule. Uniformly short beats are a metronome, uniformly long
# ones a slideshow, so the checks police the shares and the runs, and only
# flag a single beat when it is too long to sit under one still image.
RHYTHM_FORMATS = {"explainer"}
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
    outro_s = (OUTRO_HOLD_SECONDS + 2.1) if config.OUTRO_ENABLED else 0.0

    est = narration_s + pad_s + outro_s
    per_beat = narration_s / len(beats) if beats else 0
    print(f"[prompts] ~{total_words} spoken words, {narration_s:.0f}s narration "
          f"+ {pad_s:.0f}s cut pads + {outro_s:.0f}s outro")
    print(f"[prompts] estimated final video {est:.0f}s ({est / 60:.1f} min)")
    print(f"[prompts] ~{per_beat:.1f}s per beat across {len(beats)} beats")
    if n_frames:
        print(f"[prompts] ~{narration_s / n_frames:.1f}s per image across "
              f"{n_frames} frames")
        _report_tempo(beats, spoken_words)

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
        print(f"  {_fmt(sec['start']):>7}  {sec['mood']:9} {sec['piece'].name:22} "
              f"{', '.join(sec['locations'])}")
    if len(plan) - 1 > config.MUSIC_MAX_SWITCHES:
        print(f"  WARNING: {len(plan) - 1} music switches, more than "
              f"{config.MUSIC_MAX_SWITCHES} tends to feel jumpy")


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
    if config.OUTRO_ENABLED and not args.silent:
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
