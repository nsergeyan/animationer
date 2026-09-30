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
  "topic": "tech-university-explained",
  "format": "explainer",
  "plan": {
    "spine_question": "What is a technical university and how does it work?",
    "deflations": [
      {
        "assumed": "Tech universities are only for fixing laptops and writing computer code.",
        "actual": "They cover all major engineering branches, applied physical sciences, and practical innovation.",
        "who_decided": "Public misconception vs actual academic curriculum.",
        "build_beat": "Most people think it is only for coding geniuses or mechanical wizards.",
        "drop_beat": "But the truth is much more useful than that."
      }
    ],
    "specifics": [
      {
        "fact": "Technical universities emphasize applied research, industrial partnerships, and laboratory training over pure theoretical lectures.",
        "source": "European Association for International Education",
        "beat": "Half of your time is spent in laboratories and workshops."
      }
    ],
    "facts_to_check": [
      {
        "claim": "Technical university programs require practical internships or company-partnered thesis work.",
        "source": "Global Accreditation Board for Engineering and Technology"
      }
    ],
    "locations": [
      {
        "name": "campus laptop repair counter",
        "visual_anchor": "pale green painted cinderblock walls, speckled grey linoleum floor, one long built-in red laminate counter, dominant red"
      },
      {
        "name": "technical university glass atrium",
        "visual_anchor": "tall glass curtain walls, polished grey concrete floor, exposed steel roof trusses, one broad orange staircase, dominant orange"
      },
      {
        "name": "old humanities library hall",
        "visual_anchor": "dark oak-panelled walls, deep red carpet, one carved stone fireplace, arched plaster ceiling, dominant deep red"
      },
      {
        "name": "university engine workshop",
        "visual_anchor": "white glazed tile walls, oil-stained grey concrete floor, one yellow overhead gantry crane beam, dominant yellow"
      },
      {
        "name": "tiered lecture auditorium",
        "visual_anchor": "pale beige walls, steep curved tiers of fixed blue folding seats, one wide timber stage, dominant blue"
      },
      {
        "name": "electronics and solar testing hall",
        "visual_anchor": "white glazed brick walls, black rubber floor, one sawtooth glass roof, dominant white with green steel columns"
      },
      {
        "name": "open engineering project hall",
        "visual_anchor": "whitewashed brick walls, green epoxy floor, one long steel mezzanine walkway along the back, dominant green"
      },
      {
        "name": "applied mathematics seminar room",
        "visual_anchor": "pale blue painted walls, grey linoleum floor, one wall-length green chalkboard, tall timber window frames, dominant pale blue"
      },
      {
        "name": "professor's workshop office",
        "visual_anchor": "exposed red brick walls, oak parquet floor, one tall steel-framed industrial window, dominant brick red"
      },
      {
        "name": "partner factory production floor",
        "visual_anchor": "corrugated blue steel walls, grey concrete floor with painted yellow lanes, one overhead conveyor gantry, dominant blue"
      },
      {
        "name": "student robotics club garage",
        "visual_anchor": "purple painted breeze-block walls, grey rubber floor tiles, one roll-up steel garage door, dominant purple"
      },
      {
        "name": "overnight hackathon hall",
        "visual_anchor": "dark navy painted walls, grey carpet tiles, one high timber gallery balcony, dominant navy blue"
      },
      {
        "name": "partner company design office",
        "visual_anchor": "glass partition walls, pale oak floorboards, teal painted steel columns, one white spiral staircase, dominant teal"
      },
      {
        "name": "campus career fair sports hall",
        "visual_anchor": "tall arched windows, varnished wooden sports floor with painted court lines, yellow steel roof beams, dominant yellow"
      },
      {
        "name": "campus crossroads plaza",
        "visual_anchor": "grey cobblestone paving, a sandstone colonnade on one side, a glass-and-steel facade opposite, dominant warm sandstone"
      },
      {
        "name": "graduation project exhibition hall",
        "visual_anchor": "white gallery walls, polished grey concrete floor, one tall red steel mezzanine, dominant white and red"
      }
    ],
    "setting_anchor": ""
  },
  "beats": [
    {
      "narration": "[curious] Is a technical university just a giant room full of people fixing broken laptops?",
      "location": "campus laptop repair counter",
      "image_prompt": "a student technician in a red polo shirt bends over an opened silver laptop on a red rubber mat while reference character peers curiously from the right edge, medium shot",
      "image_prompt_alt": "high-angle shot along the counter, reference character standing at the far left end with a curious look, a student technician in a red polo shirt hunched over opened silver laptops"
    },
    {
      "narration": "Most people think it is only for coding geniuses or mechanical wizards.",
      "location": "campus laptop repair counter",
      "image_prompt": "reference character stands between a student in a grey hoodie hunched at a black keyboard and an oil-stained student in brown overalls kneeling beside a red gearbox, skeptical, wide shot",
      "image_prompt_alt": "low-angle shot, an oil-stained student in brown overalls kneeling beside a red gearbox in the foreground, a student in a grey hoodie at a black keyboard behind, reference character between, skeptical"
    },
    {
      "narration": "[surprised] But the truth is much more USEFUL than that.",
      "location": "campus laptop repair counter",
      "image_prompt": "reference character turns in surprise toward an open back doorway revealing a tall orange robotic arm beside a small white wind turbine model on a steel table, medium-wide shot",
      "image_prompt_alt": "close-up of reference character's surprised face at the foreground right, a tall orange robotic arm and a small white wind turbine model on a steel table visible beyond the doorway"
    },
    {
      "narration": "Let us break down what a tech university actually is.",
      "location": "technical university glass atrium",
      "image_prompt": "students in blue overalls and yellow goggles climb the steps in a steady stream while reference character stands attentive at the bottom left, wide shot at eye level",
      "image_prompt_alt": "high-angle shot from the upper landing, students in blue overalls and yellow goggles climbing toward camera, reference character small and attentive at the foot of the steps"
    },
    {
      "narration": "[deadpan] Without any complicated academic words.",
      "location": "technical university glass atrium",
      "image_prompt": "reference character sits on a step with a deadpan expression beside one enormous closed grey textbook with a cracked leather spine lying shut on the stair, medium shot",
      "image_prompt_alt": "overhead shot of reference character seated deadpan on the stair, one enormous closed grey textbook with a cracked leather spine lying across the step at his feet"
    },
    {
      "narration": "A technical university focuses mainly on science, technology, engineering, and mathematics.",
      "location": "technical university glass atrium",
      "image_prompt": "reference character looks up with curiosity at large models hanging from the trusses: a green double helix, a steel bridge section, a red rocket, a white molecule, low-angle wide shot",
      "image_prompt_alt": "wide shot from the upper landing, reference character leaning on the balcony rail beside a hanging red rocket model, a steel bridge section, green double helix and white molecule suspended beyond, curious"
    },
    {
      "narration": "[hesitates] You might hear people call them polytechnics or institutes of TECHNOLOGY...",
      "location": "technical university glass atrium",
      "image_prompt": "reference character tilts his head hesitantly before a wooden plinth holding three small campus models: a red brick tower, a glass cube, a white concrete dome, medium shot",
      "image_prompt_alt": "close three-quarter view across three small campus models on a wooden plinth, red brick tower nearest, glass cube and white concrete dome behind, reference character hesitating at the far side"
    },
    {
      "narration": "They are all basically describing the same idea.",
      "location": "technical university glass atrium",
      "image_prompt": "reference character nods slowly beside the three campus models on the wooden plinth, each topped with an identical small orange steel gear, medium close-up",
      "image_prompt_alt": "wide shot of the wooden plinth, three campus models each crowned with an identical small orange steel gear, reference character standing back from them nodding"
    },
    {
      "narration": "[sarcastic] A regular university loves big heavy BOOKS and history lessons.",
      "location": "old humanities library hall",
      "image_prompt": "a student in a green knitted sweater sits behind a towering stack of leather-bound books on an oak table while reference character watches from the far end, mildly amused, wide shot",
      "image_prompt_alt": "close-up past a towering stack of leather-bound books on an oak table, a student in a green knitted sweater almost hidden behind it, reference character leaning in from the left, mildly amused"
    },
    {
      "narration": "They spend years asking why things happened in the past.",
      "location": "old humanities library hall",
      "image_prompt": "a student in a green knitted sweater leans over an open atlas of faded battle maps beside a brass desk lamp, reference character seated nearby with chin on fist, patient, medium two-shot",
      "image_prompt_alt": "high-angle shot over the oak table, a large open atlas of faded battle maps between a student in a green knitted sweater and reference character, chin on fist, patient"
    },
    {
      "narration": "[understated] A tech university asks how to BUILD something today.",
      "location": "university engine workshop",
      "image_prompt": "students in blue overalls and yellow goggles gather around a bare steel engine block mounted on a red stand while reference character watches from the edge, interested, medium-wide shot",
      "image_prompt_alt": "low-angle close shot of a bare steel engine block on a red stand, students in blue overalls and yellow goggles behind it, reference character at the left edge, interested"
    },
    {
      "narration": "Imagine you want to study cars.",
      "location": "university engine workshop",
      "image_prompt": "reference character leans against the front of a stripped red car chassis on black wheels in the centre of the floor, curious, low-angle three-quarter view",
      "image_prompt_alt": "high-angle shot looking down on a stripped red car chassis resting on black wheels, reference character standing beside its front axle, curious"
    },
    {
      "narration": "[excited] A classic university teaches you the HISTORY of transport.",
      "location": "old humanities library hall",
      "image_prompt": "an elderly lecturer in a tweed waistcoat stands at a wooden lectern beside an easel holding a large painted canvas of a horse-drawn carriage, reference character in an armchair, politely attentive, medium-wide shot",
      "image_prompt_alt": "wide shot past the shoulder of an elderly lecturer in a tweed waistcoat, a painted horse-drawn carriage canvas on an easel, reference character in an armchair facing him, politely attentive"
    },
    {
      "narration": "You read about old carriages and write long essays.",
      "location": "old humanities library hall",
      "image_prompt": "a student in a green knitted sweater sits over one long curling sheet of paper spilling off the oak table onto the carpet, reference character beside him looking tired, medium shot",
      "image_prompt_alt": "low floor-level shot along one long curling sheet of paper trailing across the carpet to the oak table, a student in a green knitted sweater above it, reference character slumped nearby, tired"
    },
    {
      "narration": "[slows down] A tech university gives you tools... and tells you to build an ENGINE.",
      "location": "university engine workshop",
      "image_prompt": "a grey-bearded professor in a brown corduroy jacket stands beside a red steel toolbox and an engine block facing students in blue overalls and yellow goggles, reference character nearby, eyebrows raised, medium-wide shot",
      "image_prompt_alt": "wide shot past the students in blue overalls and yellow goggles toward a grey-bearded professor in a brown corduroy jacket beside a red steel toolbox and engine block, reference character right, eyebrows raised"
    },
    {
      "narration": "That hands-on style is the core difference.",
      "location": "university engine workshop",
      "image_prompt": "students in blue overalls and yellow goggles lower a steel piston into an engine block from a yellow chain hoist, reference character leaning close at the right, genuinely interested, close-up",
      "image_prompt_alt": "medium shot from above the engine block, a steel piston hanging on a yellow chain hoist, students in blue overalls and yellow goggles guiding it down, reference character opposite, genuinely interested"
    },
    {
      "narration": "[light chuckle] You do not just sit in huge lecture halls sleeping.",
      "location": "tiered lecture auditorium",
      "image_prompt": "reference character sits upright and alert in a blue seat among students in grey hoodies slumped asleep on their fold-down desks, faintly amused, high-angle wide shot",
      "image_prompt_alt": "medium side shot along one tier, students in grey hoodies asleep with heads on fold-down desks, reference character wide awake in the nearest blue seat, faintly amused"
    },
    {
      "narration": "Half of your time is spent in laboratories and workshops.",
      "location": "electronics and solar testing hall",
      "image_prompt": "students in blue overalls and yellow goggles bend over long steel workbenches of small grey instrument boxes with green wavy line displays, reference character strolling between benches, interested, wide shot at eye level",
      "image_prompt_alt": "close-up of one small grey instrument box with a green wavy line display on a steel workbench, students in blue overalls and yellow goggles behind, reference character leaning in, interested"
    },
    {
      "narration": "[suspicious tone] You will work in teams with real EQUIPMENT.",
      "location": "electronics and solar testing hall",
      "image_prompt": "students in blue overalls and yellow goggles gather around a large orange industrial robot arm bolted to the floor, reference character peering warily around a steel cabinet, medium-wide shot",
      "image_prompt_alt": "low-angle shot beneath the large orange industrial robot arm raised overhead, students in blue overalls and yellow goggles at its base, reference character at the frame edge, wary but curious"
    },
    {
      "narration": "You might design solar panels or test microchips.",
      "location": "electronics and solar testing hall",
      "image_prompt": "a student in blue overalls and yellow goggles stands beside a large blue solar panel angled on a steel frame, another bends over a green circuit board, reference character between them, impressed, medium three-shot",
      "image_prompt_alt": "wide shot, one student in blue overalls and yellow goggles over a green circuit board in front, another beside a large blue solar panel on a steel frame, reference character between, impressed"
    },
    {
      "narration": "[annoyed] What subjects can you actually STUDY there?",
      "location": "open engineering project hall",
      "image_prompt": "reference character seen from behind, showing the back of his plain white head with no face, overlooks bays holding a black server cabinet, a red model bridge, a white robot, high-angle wide shot",
      "image_prompt_alt": "wide eye-level shot across the hall floor, bays with a black server cabinet, a red model bridge and a white robot, reference character standing in the central aisle looking between them, curious"
    },
    {
      "narration": "Computer science is obviously a massive department.",
      "location": "open engineering project hall",
      "image_prompt": "students in grey hoodies sit at a long white desk of monitors showing green wavy lines beside tall black server cabinets, reference character leaning on one cabinet, mildly impressed, medium shot",
      "image_prompt_alt": "close three-quarter view down the long white desk, students in grey hoodies at monitors with green wavy lines, tall black server cabinets behind, reference character at the far end, mildly impressed"
    },
    {
      "narration": "[flatly] Civil engineering teaches you how bridges do not FALL.",
      "location": "open engineering project hall",
      "image_prompt": "students in blue overalls and yellow goggles stack steel weights onto a long red model bridge spanning two concrete blocks while reference character crouches beneath it, deadpan, medium-wide shot",
      "image_prompt_alt": "low floor-level shot from under the long red model bridge spanning two concrete blocks, reference character crouched in the foreground, deadpan, students in blue overalls and yellow goggles stacking steel weights above"
    },
    {
      "narration": "Mechanical engineering focuses on machines and robotics.",
      "location": "open engineering project hall",
      "image_prompt": "a white four-legged walking robot steps across the floor toward reference character, who leans back with wide curious eyes, students in blue overalls and yellow goggles watching behind, low-angle shot",
      "image_prompt_alt": "wide side view, a white four-legged walking robot mid-stride between students in blue overalls and yellow goggles on the left and reference character on the right, leaning back, curious"
    },
    {
      "narration": "[drawn out] Electrical engineering deals with power grids and CIRCUIT boards...",
      "location": "open engineering project hall",
      "image_prompt": "a tall steel model power pylon strung with orange cables stands beside a giant green circuit board laid flat on trestles, reference character walking along its edge, fascinated, overhead shot",
      "image_prompt_alt": "eye-level medium shot, reference character standing beside a giant green circuit board on trestles, a tall steel model power pylon with orange cables rising behind him, fascinated"
    },
    {
      "narration": "There are also newer fields like biotechnology and data analysis.",
      "location": "open engineering project hall",
      "image_prompt": "a student in a white lab coat and purple gloves stands at a white steel cabinet with a round window beside a tall monitor of blue bar shapes, reference character between them, intrigued, medium shot",
      "image_prompt_alt": "wide shot, intrigued reference character foreground left, a tall monitor of blue bar shapes behind, a student in a white lab coat and purple gloves at a round-windowed white steel cabinet"
    },
    {
      "narration": "[gasps] But wait... do you need to be a MATH genius?",
      "location": "applied mathematics seminar room",
      "image_prompt": "reference character stands small and startled in the foreground as the chalkboard behind him swarms with dense white chalk marks from edge to edge, low-angle wide shot",
      "image_prompt_alt": "close-up of reference character's startled face in the right foreground, dense white chalk marks crowding the green chalkboard behind him"
    },
    {
      "narration": "You definitely need math... but it is applied math.",
      "location": "applied mathematics seminar room",
      "image_prompt": "a grey-bearded professor in a brown corduroy jacket stands at the chalkboard beside a chalk drawing of a bridge arch, a small wooden bridge model on the desk, reference character nodding, medium shot",
      "image_prompt_alt": "close shot of a small wooden bridge model on the desk in the foreground, a grey-bearded professor in a brown corduroy jacket beside a chalk bridge arch behind it, reference character nodding at the side"
    },
    {
      "narration": "[nervous] You learn formulas because you need them to solve REAL problems.",
      "location": "applied mathematics seminar room",
      "image_prompt": "students in blue overalls and yellow goggles measure a sagging wooden beam laid across two desks, one steel tape stretched beneath it, reference character watching the bend anxiously, medium close-up",
      "image_prompt_alt": "low-angle shot beneath a sagging wooden beam laid across two desks, students in blue overalls and yellow goggles crouched on either side, reference character behind them, anxious"
    },
    {
      "narration": "It is not math just for fun on a blackboard.",
      "location": "applied mathematics seminar room",
      "image_prompt": "reference character leans back against the chalkboard, relaxed and convinced, beside a wheeled cart carrying a red steel pulley rig with hanging iron weights, three-quarter view",
      "image_prompt_alt": "wide shot, a wheeled cart with a red steel pulley rig and hanging iron weights in the foreground, reference character relaxed against the chalkboard behind it, convinced"
    },
    {
      "narration": "[sighs] Let us talk about the PROFESSORS.",
      "location": "professor's workshop office",
      "image_prompt": "a grey-bearded professor in a brown corduroy jacket sits at a cluttered oak desk heaped with brass gears and machine parts, reference character slouched in the visitor chair opposite, mildly tired, medium two-shot",
      "image_prompt_alt": "over-the-desk wide shot, brass gears and machine parts heaped in the foreground, a grey-bearded professor in a brown corduroy jacket behind them, reference character slouched in a chair at the side, mildly tired"
    },
    {
      "narration": "Many professors at tech universities worked in industry for years.",
      "location": "professor's workshop office",
      "image_prompt": "a grey-bearded professor in a brown corduroy jacket stands beside a framed portrait of a younger bearded man in a white hard hat before an orange steel furnace, reference character interested, medium shot",
      "image_prompt_alt": "close-up on a framed portrait of a younger bearded man in a white hard hat before an orange steel furnace, a grey-bearded professor in a brown corduroy jacket and reference character beside it, interested"
    },
    {
      "narration": "[rushed] They know what real companies actually WANT right now.",
      "location": "professor's workshop office",
      "image_prompt": "a grey-bearded professor in a brown corduroy jacket talks into a black desk phone before a wall of pinned product sketches, reference character leaning forward attentively in his chair, medium-wide shot",
      "image_prompt_alt": "close shot of a black desk phone in the foreground, a grey-bearded professor in a brown corduroy jacket talking into it, pinned product sketches behind, reference character attentive at the right"
    },
    {
      "narration": "Big companies often give money to these universities.",
      "location": "partner factory production floor",
      "image_prompt": "a factory engineer in an orange high-visibility vest and white hard hat stands beside a grey-bearded professor in a brown corduroy jacket and a new green milling machine, reference character approving, medium-wide shot",
      "image_prompt_alt": "wide shot past a new green milling machine toward a factory engineer in an orange high-visibility vest and white hard hat and a grey-bearded professor in a brown corduroy jacket, reference character aside, approving"
    },
    {
      "narration": "[mischievously] They ask students to solve real INDUSTRIAL problems.",
      "location": "partner factory production floor",
      "image_prompt": "a factory engineer in an orange high-visibility vest and white hard hat shows students in blue overalls and yellow goggles a jammed conveyor heaped with dented tin cans, reference character behind, intrigued, wide shot",
      "image_prompt_alt": "close-up of dented tin cans jammed on the conveyor, a factory engineer in an orange high-visibility vest and white hard hat and students in blue overalls and yellow goggles beyond, reference character intrigued"
    },
    {
      "narration": "So your homework might be fixing a problem for a real factory.",
      "location": "partner factory production floor",
      "image_prompt": "students in blue overalls and yellow goggles kneel beside an opened grey motor housing as tin cans flow smoothly along the conveyor again, reference character leaning on a yellow railing, pleased, medium shot",
      "image_prompt_alt": "high-angle wide shot of tin cans streaming along the conveyor, students in blue overalls and yellow goggles kneeling at an opened grey motor housing below, reference character pleased at a yellow railing"
    },
    {
      "narration": "[amazed] What about student LIFE on campus?",
      "location": "student robotics club garage",
      "image_prompt": "reference character stands at the entrance, pleasantly surprised, looking into a busy space where students in blue overalls and yellow goggles work on small robots and a low red race car, wide shot",
      "image_prompt_alt": "reverse medium shot from inside, students in blue overalls and yellow goggles at small robots and a low red race car in the foreground, reference character pleasantly surprised at the entrance behind"
    },
    {
      "narration": "It is famous for practical clubs and student competitions.",
      "location": "student robotics club garage",
      "image_prompt": "students in blue overalls and yellow goggles cheer around a square tabletop arena where two small wheeled robots shove each other, reference character leaning in from the right, grinning slightly, medium-wide shot",
      "image_prompt_alt": "overhead shot of the square tabletop arena, two small wheeled robots locked together at its centre, students in blue overalls and yellow goggles cheering around its edges, reference character among them, grinning slightly"
    },
    {
      "narration": "[frustrated] Instead of just debate teams, you get ROBOTICS teams.",
      "location": "student robotics club garage",
      "image_prompt": "a small wooden debating lectern stands forgotten in the corner while students in blue overalls and yellow goggles surround a large yellow competition robot, reference character looking from one to the other, amused, wide shot",
      "image_prompt_alt": "medium shot, a large yellow competition robot foreground with students in blue overalls and yellow goggles around it, reference character glancing back at a small wooden debating lectern in the far corner, amused"
    },
    {
      "narration": "Students build mini racing cars and compete globally.",
      "location": "student robotics club garage",
      "image_prompt": "students in blue overalls and yellow goggles push a low red single-seat race car toward the open door while reference character jogs alongside, excited, low-angle three-quarter view",
      "image_prompt_alt": "wide side shot, reference character jogging ahead of a low red single-seat race car pushed by students in blue overalls and yellow goggles toward the open door, excited"
    },
    {
      "narration": "[whispers] They host overnight coding events called hackathons.",
      "location": "overnight hackathon hall",
      "image_prompt": "students in grey hoodies hunch over laptops at long tables strewn with paper cups and flat cardboard boxes, reference character tiptoeing between them, quietly curious, wide high-angle shot",
      "image_prompt_alt": "low eye-level shot along one long table, students in grey hoodies at laptops among paper cups and flat cardboard boxes, reference character tiptoeing past in the background, quietly curious"
    },
    {
      "narration": "You spend thirty hours drinking coffee and making apps.",
      "location": "overnight hackathon hall",
      "image_prompt": "students in grey hoodies doze against their laptops beside a tall tower of stacked white paper cups, reference character slumped at the end of the table, tired but amused, medium shot",
      "image_prompt_alt": "close-up of a tall tower of stacked white paper cups in the foreground, students in grey hoodies dozing on laptops behind, reference character slumped at the far end, tired but amused"
    },
    {
      "narration": "[stammers] Before you graduate... you usually do an INTERNSHIP.",
      "location": "partner company design office",
      "image_prompt": "a young intern in a crisp white shirt and teal lanyard walks nervously into the office past rows of desks, reference character trailing behind her, slightly nervous, medium-wide shot",
      "image_prompt_alt": "front-facing long shot down the aisle of desks, a young intern in a crisp white shirt and teal lanyard approaching, reference character a step behind her, slightly nervous"
    },
    {
      "narration": "Most programs force you to work at a real company for months.",
      "location": "partner company design office",
      "image_prompt": "a young intern in a crisp white shirt and teal lanyard sits at a monitor showing a grey turbine model among engineers in teal polo shirts, reference character perched on the next desk, attentive",
      "image_prompt_alt": "wide high-angle shot of the desk cluster, engineers in teal polo shirts around a young intern in a crisp white shirt and teal lanyard at a grey turbine model monitor, reference character perched nearby, attentive"
    },
    {
      "narration": "[awe] This means you get actual work EXPERIENCE before finishing.",
      "location": "partner company design office",
      "image_prompt": "a young intern in a crisp white shirt and teal lanyard stands beside a white wind turbine blade section on a table facing engineers in teal polo shirts, reference character at the back, impressed, wide shot",
      "image_prompt_alt": "medium shot from behind the engineers in teal polo shirts, a young intern in a crisp white shirt and teal lanyard facing them beside a white wind turbine blade section, reference character at the side, impressed"
    },
    {
      "narration": "Your final project might even happen inside a company office.",
      "location": "partner company design office",
      "image_prompt": "a young intern in a crisp white shirt and teal lanyard sits beside a finished white wind turbine model as engineers in teal polo shirts gather, reference character leaning on a filing cabinet, proud, medium-wide shot",
      "image_prompt_alt": "close-up of a finished white wind turbine model on a desk, a young intern in a crisp white shirt and teal lanyard beside it, engineers in teal polo shirts behind, reference character proud at the edge"
    },
    {
      "narration": "[loudly] That brings us to JOB prospects.",
      "location": "campus career fair sports hall",
      "image_prompt": "graduates in dark suits queue at company booths with bright yellow backdrops while reference character stands at the hall entrance, eyebrows raised, wide shot at eye level",
      "image_prompt_alt": "high-angle shot over company booths with bright yellow backdrops and queues of graduates in dark suits, reference character small at the entrance, eyebrows raised"
    },
    {
      "narration": "Companies love hiring graduates from technical universities.",
      "location": "campus career fair sports hall",
      "image_prompt": "a recruiter in a navy suit leans eagerly across a yellow booth table toward one graduate in a dark suit as a second recruiter hurries over, reference character watching beside the booth, amused, medium shot",
      "image_prompt_alt": "medium-wide side shot, one graduate in a dark suit at a yellow booth table, a recruiter in a navy suit leaning toward him, a second recruiter hurrying in, reference character amused at the booth corner"
    },
    {
      "narration": "[happily] Because you already know how to use industry SOFTWARE.",
      "location": "campus career fair sports hall",
      "image_prompt": "past the shoulder of a graduate in a dark suit at a booth laptop showing a spinning grey gear model, a recruiter in a navy suit impressed beside him, reference character pleased, over-the-shoulder medium shot",
      "image_prompt_alt": "front medium shot, a graduate in a dark suit at a booth laptop with a grey gear model, a recruiter in a navy suit leaning in impressed, reference character pleased at the table edge"
    },
    {
      "narration": "You do not need six months of basic training on the job.",
      "location": "campus career fair sports hall",
      "image_prompt": "a thick grey training binder lies shut at the table edge while a graduate in a dark suit works at a laptop beside a recruiter in a navy suit, reference character nodding, close shot",
      "image_prompt_alt": "wide shot, a graduate in a dark suit already at a laptop, a recruiter in a navy suit beside him, a thick grey training binder abandoned on a chair, reference character nodding"
    },
    {
      "narration": "[worried] Is a tech university better than a NORMAL university?",
      "location": "campus crossroads plaza",
      "image_prompt": "reference character stands midway between the two buildings looking back and forth, uncertain, one red steel bench beside him, wide shot at eye level",
      "image_prompt_alt": "high-angle shot, reference character small at the plaza centre beside one red steel bench, head turned toward one building, uncertain"
    },
    {
      "narration": "Not necessarily... it just depends on your personal goal.",
      "location": "campus crossroads plaza",
      "image_prompt": "reference character sits on the red steel bench, thoughtful, at the spot where the paved path splits in two toward each building, medium shot",
      "image_prompt_alt": "overhead shot of the paved path splitting in two, one branch per building, reference character seated thoughtful on the red steel bench at the fork"
    },
    {
      "narration": "[quietly] If you love abstract philosophy or literature, go to a general college.",
      "location": "campus crossroads plaza",
      "image_prompt": "a student in a green knitted sweater sits on the sandstone steps with an open book, reference character watching from the red steel bench, calm and respectful, medium-wide shot",
      "image_prompt_alt": "close shot past the red steel bench where reference character sits calm and respectful, a student in a green knitted sweater with an open book on sandstone steps beyond"
    },
    {
      "narration": "If you like solving practical problems with technology, a tech school wins.",
      "location": "campus crossroads plaza",
      "image_prompt": "students in blue overalls and yellow goggles wheel a small solar-powered cart with a blue panel roof out of the glass entrance, reference character turning toward them with a warm smile, wide three-quarter view",
      "image_prompt_alt": "low-angle shot, a small solar-powered cart with a blue panel roof rolling toward camera, students in blue overalls and yellow goggles behind it, reference character smiling warmly at the side"
    },
    {
      "narration": "[rapid-fire] They teach you how to turn raw IDEAS into working machines.",
      "location": "graduation project exhibition hall",
      "image_prompt": "reference character walks past a row of plinths leading from a paper napkin sketch to a cardboard prototype to a finished orange delivery drone, delighted, wide side view",
      "image_prompt_alt": "low close shot of the finished orange delivery drone on its plinth in the foreground, a cardboard prototype and paper napkin sketch on plinths behind, reference character approaching, delighted"
    },
    {
      "narration": "It is challenging... but highly rewarding for practical thinkers.",
      "location": "graduation project exhibition hall",
      "image_prompt": "a student in blue overalls and yellow goggles sits tired on a wooden crate beside the finished orange delivery drone, reference character sitting next to her, both quietly satisfied, medium two-shot",
      "image_prompt_alt": "wide shot from behind the orange delivery drone, a student in blue overalls and yellow goggles and reference character seated side by side on a wooden crate, quietly satisfied"
    },
    {
      "narration": "[sigh of relief] So now you know what a technical university REALLY is.",
      "location": "graduation project exhibition hall",
      "image_prompt": "reference character leans back against a white plinth with relaxed shoulders, relieved, as a few visitors in bright coats wander among the student projects, high-angle wide shot",
      "image_prompt_alt": "medium shot at plinth height, reference character relieved and relaxed against a white plinth in the foreground, a few visitors in bright coats wandering among student projects behind"
    },
    {
      "narration": "[softly] It is where theoretical science meets practical engineering.",
      "location": "graduation project exhibition hall",
      "image_prompt": "a tall chalkboard panel of white chalk curves stands touching a working brass-and-steel steam turbine model, reference character standing between them, thoughtful, medium shot",
      "image_prompt_alt": "wide shot, reference character to the left, thoughtful, a tall chalkboard panel of white chalk curves meeting a brass-and-steel steam turbine model at the centre of the frame"
    },
    {
      "narration": "[excitedly] A place where you learn by DOING things.",
      "location": "graduation project exhibition hall",
      "image_prompt": "students in blue overalls and yellow goggles send the orange delivery drone hovering above the concrete floor, reference character looking up at it grinning, low-angle shot",
      "image_prompt_alt": "high-angle shot from above the hovering orange delivery drone, students in blue overalls and yellow goggles below, reference character grinning up at it from the side"
    },
    {
      "narration": "[calm] And that is Tech University explained.",
      "location": "graduation project exhibition hall",
      "image_prompt": "reference character seen from behind, showing the back of his plain white head with no face, sits calmly on a white plinth beside the landed orange delivery drone, overlooking the hall, wide shot",
      "image_prompt_alt": "reference character seen from behind, showing the back of his plain white head with no face, sitting calm on a white plinth, the landed orange delivery drone beside him, long shot from the balcony"
    }
  ],
  "music_prompt": "Light, curious instrumental bed at around ninety BPM. Soft plucked muted electric guitar, gentle wooden marimba, warm sustained synth pads, and a quiet brushed drum kit. Flat consistent energy with no build, no swells, no drops. Sits far in the background under a spoken narrator with the mid range left clear. Purely instrumental with no vocals of any kind. Understated rather than comedic."
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

        # Order: style, then subject and action, then the place. The style
        # leads so the model commits to the medium before it reads a word of
        # realistic scene description - see config.STYLE_BLOCK's POSITION note
        # for the photo-grounding failure that rule exists to stop. The place
        # trails because leading with it buries the subject.
        loc = " ".join((beat.get("location") or "").split()).lower()
        loc_anchor = location_anchors.get(loc, "")
        if location_anchors and not loc_anchor:
            missing_anchor.append(index)
        anchor = " ".join(a for a in (loc_anchor, setting_anchor) if a)
        if anchor:
            anchored += 1

        lines.append(" ".join(part for part in (
            config.STYLE_BLOCK, _fragment(text), anchor
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
                config.STYLE_BLOCK, _fragment(text), anchor
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
