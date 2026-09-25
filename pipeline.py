import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import config
from modules import transcriber

FLOW_RUNNER = config.ROOT_DIR / "flow_runner" / "runner.py"

NEW_SCRIPT ={
  "topic": "is-ai-really-dangerous",
  "format": "explainer",
  "plan": {
    "spine_question": "Is artificial intelligence going to destroy humanity, or are the real dangers much more ordinary?",
    "deflations": [
      {
        "assumed": "Killer robots like Terminator will take over the world and exterminate humans.",
        "actual": "AI is predictive software that makes foolish mistakes, enables financial fraud, and amplifies human bias.",
        "who_decided": "Sci-fi movies and sensational media headlines.",
        "build_beat": "Hollywood movies always show killer robots marching down the street.",
        "drop_beat": "The actual threat is much more boring... and much more EMBARRASSING."
      }
    ],
    "specifics": [
      {
        "fact": "Air Canada was held legally liable in 2024 after its chatbot invented a fake bereavement fare policy.",
        "source": "Civil Resolution Tribunal of British Columbia ruling 2024",
        "beat": "Look at what happened with Air Canada in 2024."
      },
      {
        "fact": "A finance worker transferred $25 million after being tricked by deepfakes of his CFO and colleagues on a video call.",
        "source": "Hong Kong Police Force report 2024",
        "beat": "In early 2024, a finance worker in Hong Kong joined a video call with his executive team."
      },
      {
        "fact": "An AI search query uses approximately ten times as much electricity as a standard Google search.",
        "source": "International Energy Agency Electricity 2024 Report",
        "beat": "According to the International Energy Agency, one AI search uses ten times more electricity than a basic search."
      }
    ],
    "facts_to_check": [
      {
        "claim": "Center for AI Safety published statement on AI extinction risk signed by top researchers.",
        "source": "Center for AI Safety Statement on AI Risk 2023"
      },
      {
        "claim": "European Union passed comprehensive AI regulatory framework.",
        "source": "European Union AI Act 2024"
      }
    ],
    "locations": [
      {
        "name": "robot movie prop depot",
        "visual_anchor": "corrugated steel walls painted deep red, stained concrete floor, one large roller shutter door, rusted steel ceiling girders"
      },
      {
        "name": "oak-panelled university reading room",
        "visual_anchor": "tall oak-panelled walls, green carpeted floor, one arched stained-glass window, dark green plaster ceiling with moulded cornices"
      },
      {
        "name": "backyard survival bunker",
        "visual_anchor": "curved corrugated metal walls painted olive green, packed dirt floor, one steel ladder rising to a round hatch"
      },
      {
        "name": "cramped server basement workshop",
        "visual_anchor": "grey concrete walls, raised white floor tiles, one built-in row of black server racks, deep blue ceiling"
      },
      {
        "name": "airline customer service back room",
        "visual_anchor": "cream laminate wall panels, speckled blue linoleum floor, one long built-in counter, bright red painted ceiling beams"
      },
      {
        "name": "small tribunal hearing chamber",
        "visual_anchor": "pale maple wall panelling, navy blue carpet, one raised wooden judge's bench along the front wall"
      },
      {
        "name": "police fraud evidence room",
        "visual_anchor": "painted cinderblock walls in teal, grey epoxy floor, one wall-length steel pegboard, exposed fluorescent tube fittings overhead"
      },
      {
        "name": "high-rise finance office",
        "visual_anchor": "floor-to-ceiling glass windows, charcoal carpet tiles, one white structural column, pale grey walls with orange accent panel"
      },
      {
        "name": "newspaper fact-checking room",
        "visual_anchor": "yellowed plaster walls, scuffed parquet floor, one tall sash window, mustard yellow painted pipes along the ceiling"
      },
      {
        "name": "bank loan records archive",
        "visual_anchor": "dark brick walls, worn brown linoleum floor, one arched brick vault doorway, fixed maroon steel shelving along walls"
      },
      {
        "name": "half-vacated call-centre floor",
        "visual_anchor": "white drywall partitions, grey loop-pile carpet, one wide exposed ventilation duct, lime green painted support pillars"
      },
      {
        "name": "glass-topped executive boardroom",
        "visual_anchor": "black marble walls, dark walnut floor, one floor-to-ceiling window wall, deep purple velvet wall panels"
      },
      {
        "name": "data-centre cooling hall",
        "visual_anchor": "white insulated metal walls, perforated steel floor grating, one massive overhead cooling duct, bright cyan painted pipework"
      },
      {
        "name": "parliament committee chamber",
        "visual_anchor": "curved blond wood walls, royal blue carpet, one semicircular tiered bench, high white acoustic ceiling panels"
      }
    ],
    "setting_anchor": ""
  },
  "beats": [
    {
      "location": "robot movie prop depot",
      "narration": "[curious] Is artificial intelligence going to DESTROY humanity, or are we worrying about the wrong thing?",
      "image_prompt": "reference character leans against a tall chrome robot prop with red eye lenses, arms folded, looking skeptical toward the camera, medium shot, bright red tarpaulin draped over a nearby wooden crate",
      "image_prompt_alt": "low-angle wide shot, a tall chrome robot prop with red eye lenses towers over reference character, who stands at frame right with a deadpan stare, bright red tarpaulin covering the floor"
    },
    {
      "location": "robot movie prop depot",
      "narration": "Hollywood movies always show killer robots marching down the street.",
      "image_prompt": "reference character sits on a folding chair, bored, watching five silver robot props lined up along a miniature cardboard street set painted bright red, wide shot at eye level",
      "image_prompt_alt": "over-the-shoulder shot from behind reference character, facing five silver robot props mid-stride across a bright red cardboard street set, one robot prop tipped over on the floor"
    },
    {
      "location": "robot movie prop depot",
      "narration": "[dramatically] Sci-fi stories made everyone expect a giant laser-eyed machine invasion.",
      "image_prompt": "reference character stands unimpressed beside a giant fibreglass robot head with two red laser tubes protruding from its eyes, bright orange foam scenery rocks piled at its base, medium shot",
      "image_prompt_alt": "close-up of reference character's unimpressed face in the foreground left, a giant fibreglass robot head behind with red laser tubes jutting from its eyes over bright orange foam rocks"
    },
    {
      "location": "oak-panelled university reading room",
      "narration": "[nervous] Even top tech experts signed open letters warning about potential human EXTINCTION.",
      "image_prompt": "reference character leans over a long oak table covered with cream paper sheets bearing dark signature marks, curious expression, high-angle shot, deep green leather tabletop, one brass fountain pen beside the stack",
      "image_prompt_alt": "medium shot from table level, a tall stack of cream paper sheets with dark signature marks in the foreground, reference character seated behind it frowning curiously, deep green leather tabletop"
    },
    {
      "location": "oak-panelled university reading room",
      "narration": "In 2023, the Center for AI Safety published a single sentence statement about global risk.",
      "image_prompt": "reference character sits hunched at a reading desk squinting at one cream paper sheet holding a single short line of dark marks, bright green leather blotter beneath, medium close-up",
      "image_prompt_alt": "overhead shot of one cream paper sheet with a single short line of dark marks on a bright green leather blotter, reference character's skeptical face leaning in from the frame edge"
    },
    {
      "location": "backyard survival bunker",
      "narration": "[worried] So should you start building a secret underground bunker right NOW?",
      "image_prompt": "reference character sits on an upturned metal bucket, looking resigned, beside stacked food tins and one orange hand-crank radio, olive green sleeping bag crossing the foreground, medium-wide shot",
      "image_prompt_alt": "high-angle shot looking down the ladder at reference character crouched among stacked food tins, one orange hand-crank radio at their feet, olive green sleeping bag unrolled across the dirt"
    },
    {
      "location": "robot movie prop depot",
      "narration": "[hesitates] Well... not exactly.",
      "image_prompt": "reference character stands beside a toppled chrome robot prop lying on the concrete floor, one eyebrow raised, bright red tarpaulin half pulled from the fallen prop, medium shot",
      "image_prompt_alt": "wide shot at floor level, the toppled chrome robot prop stretched across the foreground, reference character at the far end with a doubtful sideways glance, bright red tarpaulin crumpled nearby"
    },
    {
      "location": "robot movie prop depot",
      "narration": "The real danger of artificial intelligence is very different from movie monsters.",
      "image_prompt": "reference character stands between a bright red rubber monster costume hanging on a steel rail and one beige laptop on a wooden workbench, glancing toward the laptop, medium-wide shot",
      "image_prompt_alt": "reference character in the foreground right with a thoughtful look, a bright red rubber monster costume hanging from a steel rail behind, one beige laptop on a workbench at left, long shot"
    },
    {
      "location": "robot movie prop depot",
      "narration": "[flatly] It is not an evil digital mind planning to conquer Earth.",
      "image_prompt": "reference character sits on a wooden crate with a flat unimpressed stare beside a large clear plastic brain model packed with bright red wires, resting on a steel trolley, medium shot",
      "image_prompt_alt": "close-up over the clear plastic brain model filled with bright red wires on a steel trolley, reference character behind it with a flat unimpressed stare, three-quarter view"
    },
    {
      "location": "robot movie prop depot",
      "narration": "[sarcastic] The actual threat is much more boring... and much more EMBARRASSING.",
      "image_prompt": "reference character slumps on a folding chair beside a beige office printer jammed with crumpled paper, bored expression, chrome robot props standing ignored behind, bright red floor tarpaulin, wide shot",
      "image_prompt_alt": "medium close-up of the beige printer jammed with crumpled paper on a bright red floor tarpaulin, reference character slumped beside it, bored, chrome robot props standing further back"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "To understand why, we need to see how these computer programs work.",
      "image_prompt": "reference character stands at the open door of one black metal cabinet, peering at tangled bright blue cables and rows of small green indicator lamps, curious expression, medium shot",
      "image_prompt_alt": "wide shot along the aisle of black metal cabinets, reference character small in the distance leaning toward one open cabinet door, bright blue cable bundles running overhead"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "Modern AI tools do not think like human beings.",
      "image_prompt": "reference character sits at a steel desk comparing a pink rubber human brain model with one flat green circuit board resting beside it, skeptical look, close-up",
      "image_prompt_alt": "overhead shot of a steel desk holding a pink rubber brain model and a flat green circuit board side by side, reference character's skeptical face leaning in from above"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "[understated] They are basically supercharged auto-complete software.",
      "image_prompt": "reference character stands deadpan beside a jumbo red phone keypad model propped on a trolley, thick orange jump cables linking it to a car battery on the floor, medium-wide shot",
      "image_prompt_alt": "low-angle shot from floor level past a car battery and thick orange jump cables toward a jumbo red phone keypad model on a trolley, reference character deadpan behind it"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "They scan billions of lines of text from across the internet.",
      "image_prompt": "reference character sits buried to the shoulders in bright yellow continuous-feed paper spilling from a black metal cabinet, dense grey marks across every sheet, tired look, high-angle shot",
      "image_prompt_alt": "wide shot of bright yellow continuous-feed paper cascading from a black metal cabinet into a heap across the floor, reference character's tired face poking out of the pile at left"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "[rushed] Then they predict the very NEXT word in a sentence.",
      "image_prompt": "reference character leans toward a row of blank wooden blocks on a steel bench, one gap at the end and a single bright red block waiting beside it, curious, close-up",
      "image_prompt_alt": "medium shot from the side, reference character crouched at bench height eyeing a single bright red wooden block beside a gap in a row of blank wooden blocks"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "The computer does not actually understand facts or truth.",
      "image_prompt": "reference character stares blankly at a black metal cabinet while an open encyclopedia and a brass magnifying glass rest untouched on top, bright blue cable loops hanging beside, medium shot",
      "image_prompt_alt": "close-up of an open encyclopedia and brass magnifying glass on top of a black metal cabinet, reference character behind with a blank resigned stare, bright blue cables dangling"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "It only understands statistical patterns.",
      "image_prompt": "reference character stands before a large cork board in a steel frame pinned with bright orange bar charts and dot grids, head tilted, mildly interested, medium-wide shot",
      "image_prompt_alt": "three-quarter rear view from behind reference character, facing the steel-framed cork board pinned with bright orange bar charts and dot grids, one steel stool beside them"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "[clears throat] When the system makes up a mistake, scientists call it hallucination.",
      "image_prompt": "reference character stands arms crossed beside an open black metal cabinet, bright pink cotton wool puffing from its vents, skeptical expression, medium shot",
      "image_prompt_alt": "wide shot, bright pink cotton wool drifting from the vents of an open black metal cabinet across the aisle, reference character at the frame edge eyeing it skeptically"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "[mischievously] Hallucination is just a fancy scientific word for LYING with total confidence.",
      "image_prompt": "reference character raises an eyebrow at a small grey robot figurine standing proudly on a steel desk wearing a tiny purple graduation cap, beside a toppled stack of books, close-up",
      "image_prompt_alt": "medium shot from desk height, the small grey robot figurine in its purple graduation cap in the foreground, reference character leaning back behind it with a raised eyebrow"
    },
    {
      "location": "cramped server basement workshop",
      "narration": "And that causes hilarious, yet dangerous problems in real life.",
      "image_prompt": "reference character sits beside a steel desk where a yellow rubber chicken rests next to a bright red fire extinguisher, half amused and half wary, medium-wide shot",
      "image_prompt_alt": "close-up of a yellow rubber chicken and a bright red fire extinguisher side by side on a steel desk, reference character in the background with a wary half-smile"
    },
    {
      "location": "airline customer service back room",
      "narration": "[curiously] Look at what happened with Air Canada in 2024.",
      "image_prompt": "reference character leans on the counter beside a white Air Canada passenger jet model with a red tail fin on a steel stand, curious glance, bright red lanyards hanging nearby, medium shot",
      "image_prompt_alt": "low-angle close-up of a white passenger jet model with a red maple-leaf tail fin on a steel stand, reference character leaning in from behind with a curious glance"
    },
    {
      "location": "airline customer service back room",
      "narration": "A customer used their official website chatbot to ask about ticket prices after a family death.",
      "image_prompt": "reference character stands quietly at frame left watching a middle-aged passenger in a grey wool coat and black armband seated before a beige terminal showing a red speech bubble, medium two-shot",
      "image_prompt_alt": "over-the-shoulder shot behind a middle-aged passenger in a grey wool coat and black armband, facing a beige terminal showing a red speech bubble, reference character watching from the side"
    },
    {
      "location": "airline customer service back room",
      "narration": "[light chuckle] The polite chatbot cheerfully invented a completely FAKE discount rule.",
      "image_prompt": "reference character sits on the counter, unimpressed, facing a beige monitor showing a smiling yellow robot face, a stack of bright red paper tickets fanned out beside it, close-up",
      "image_prompt_alt": "medium shot from behind the beige monitor showing a smiling yellow robot face, reference character across the counter with an unimpressed stare, bright red paper tickets fanned out nearby"
    },
    {
      "location": "airline customer service back room",
      "narration": "It told the passenger to buy full price tickets today and request a refund later.",
      "image_prompt": "reference character watches skeptically as a middle-aged passenger in a grey wool coat and black armband stands at the counter beside a bright red card payment terminal and one paper ticket, medium-wide shot",
      "image_prompt_alt": "close-up of a bright red card payment terminal and one paper ticket on the counter, a middle-aged passenger in a grey wool coat and black armband behind, reference character skeptical nearby"
    },
    {
      "location": "small tribunal hearing chamber",
      "narration": "When the airline refused to pay, the passenger took them to court.",
      "image_prompt": "reference character sits on the public bench watching a middle-aged passenger in a grey wool coat and black armband stand at a lectern beside one bright blue cardboard folder, wide shot",
      "image_prompt_alt": "low-angle shot from behind the lectern, a middle-aged passenger in a grey wool coat and black armband facing forward, one bright blue cardboard folder on the lectern, reference character attentive at the side"
    },
    {
      "location": "small tribunal hearing chamber",
      "narration": "[surprised] Air Canada argued in legal court that the chatbot was responsible for its own actions.",
      "image_prompt": "reference character stares in disbelief from the public bench while an airline lawyer in a charcoal suit and red tie stands beside a beige monitor resting on the witness chair, medium-wide shot",
      "image_prompt_alt": "close-up of a beige monitor seated on the wooden witness chair, an airline lawyer in a charcoal suit and red tie beside it, reference character's disbelieving face in the foreground"
    },
    {
      "location": "small tribunal hearing chamber",
      "narration": "[deadpan] Yes... they tried to blame their computer script like a separate PERSON.",
      "image_prompt": "reference character leans back, eyes closed, exasperated, as the beige monitor on the witness chair wears a red bow tie beside an airline lawyer in a charcoal suit and red tie, medium shot",
      "image_prompt_alt": "high-angle wide shot of the beige monitor in a red bow tie on the witness chair, an airline lawyer in a charcoal suit and red tie beside it, reference character exasperated behind"
    },
    {
      "location": "small tribunal hearing chamber",
      "narration": "[laughs] The tribunal judge ruled against the airline and forced them to pay.",
      "image_prompt": "reference character gives a small satisfied smirk from the public bench as a grey-haired tribunal adjudicator in a black robe sits behind a wooden gavel on a bright red blotter, wide shot",
      "image_prompt_alt": "close-up of a wooden gavel on a bright red blotter, a grey-haired tribunal adjudicator in a black robe behind it, reference character's small satisfied smirk at frame right"
    },
    {
      "location": "small tribunal hearing chamber",
      "narration": "That sounds silly, but imagine an automated bot giving wrong medical advice.",
      "image_prompt": "reference character frowns at the beige monitor on the witness chair, now wearing a white paper nurse's cap, a bright red first-aid case with a white cross resting beside it, medium shot",
      "image_prompt_alt": "low three-quarter view, a bright red first-aid case with a white cross on the floor in the foreground, the beige monitor in a white nurse's cap behind, reference character frowning nearby"
    },
    {
      "location": "small tribunal hearing chamber",
      "narration": "[frustrated] Dumb automated mistakes are already causing REAL financial damage.",
      "image_prompt": "reference character stands arms folded, mildly annoyed, beside a tall heap of bright red paper sheets on the lawyer's wooden table, a toppled beige monitor on top, medium-wide shot",
      "image_prompt_alt": "high-angle shot looking down on a heap of bright red paper sheets and a toppled beige monitor on the lawyer's wooden table, reference character annoyed at the table edge"
    },
    {
      "location": "police fraud evidence room",
      "narration": "Now let us look at deepfakes and digital fraud.",
      "image_prompt": "reference character stands beside a steel table lined with lifelike rubber face masks on white foam heads, clear plastic zip bags with bright teal seals beside them, skeptical frown, medium shot",
      "image_prompt_alt": "close-up along the row of lifelike rubber face masks on white foam heads, bright teal-sealed plastic bags in front, reference character's skeptical frown at the far end of the table"
    },
    {
      "location": "police fraud evidence room",
      "narration": "Modern software can clone faces and voices in just a few seconds.",
      "image_prompt": "reference character watches warily as a webcam on a tripod faces a white foam head, a laptop beside it showing two identical faces on a bright orange background, medium-wide shot",
      "image_prompt_alt": "over-the-shoulder shot from behind reference character facing the laptop showing two identical faces on a bright orange background, a webcam on a tripod and white foam head at left"
    },
    {
      "location": "high-rise finance office",
      "narration": "[quietly][suspicious tone] In early 2024, a finance worker in Hong Kong joined a video call with his executive team.",
      "image_prompt": "reference character watches from the doorway as a slim finance worker with short black hair, thin glasses, white shirt and navy tie sits at a bright orange desk facing a monitor grid of six faces, medium-wide shot",
      "image_prompt_alt": "over-the-shoulder shot behind a slim finance worker with short black hair, thin glasses, white shirt and navy tie, facing a monitor grid of six faces, reference character watching suspiciously at far right"
    },
    {
      "location": "high-rise finance office",
      "narration": "Every single person on that video screen looked and sounded totally real.",
      "image_prompt": "close-up of the monitor grid of six executives in dark suits, reference character leaning in beside a slim finance worker with short black hair, thin glasses, white shirt and navy tie, curious squint",
      "image_prompt_alt": "medium two-shot from beside the monitor, a slim finance worker with short black hair, thin glasses, white shirt and navy tie nodding at it, reference character squinting over their shoulder, bright orange desk"
    },
    {
      "location": "high-rise finance office",
      "narration": "[gasps] But every single colleague on that call was actually an AI video RECREATION.",
      "image_prompt": "reference character, eyes wide, stands behind a slim finance worker with short black hair, thin glasses, white shirt and navy tie as the six monitor faces split into grey wireframe mesh, medium shot",
      "image_prompt_alt": "close-up of the monitor, six executive faces half peeled into grey wireframe mesh on bright orange, reference character surprised behind a slim finance worker with short black hair, thin glasses, white shirt and navy tie"
    },
    {
      "location": "high-rise finance office",
      "narration": "[booming] The tricked employee transferred TWENTY-FIVE million dollars to foreign scammers.",
      "image_prompt": "reference character stares in dismay as a trolley stacked shoulder-high with green canvas bank sacks rolls away from a slim finance worker with short black hair, thin glasses, white shirt and navy tie, wide shot",
      "image_prompt_alt": "low-angle shot of a trolley stacked with green canvas bank sacks rolling out the door, a slim finance worker with short black hair, thin glasses, white shirt and navy tie frozen, reference character dismayed"
    },
    {
      "location": "police fraud evidence room",
      "narration": "[whispers] Criminals do not need killer robots when they can clone family voices.",
      "image_prompt": "reference character sits at a steel table eyeing an old bright red landline telephone wired to a small black audio recorder, suspicious sideways glance, close-up",
      "image_prompt_alt": "wide shot, the bright red landline telephone and black audio recorder small on the steel table in the foreground, reference character seated at the far end, suspicious"
    },
    {
      "location": "newspaper fact-checking room",
      "narration": "Fake photos and audio can ruin individual reputations or alter entire elections.",
      "image_prompt": "reference character leans over a wide layout table comparing two nearly identical photographs of a politician at a podium, one ringed in bright red grease pencil, a white ballot box beside them, high-angle shot",
      "image_prompt_alt": "medium shot from table level, two nearly identical politician-at-podium photographs in the foreground, one ringed in bright red grease pencil, a white ballot box behind, reference character squinting skeptically"
    },
    {
      "location": "newspaper fact-checking room",
      "narration": "[sad] When people can no longer trust what they see, truth DISAPPEARS.",
      "image_prompt": "reference character sits, disappointed, beside a bright yellow plastic photo tray where a photograph of a crowd is fading into blank white paper, medium close-up",
      "image_prompt_alt": "overhead shot of a bright yellow plastic photo tray holding a crowd photograph fading into blank white paper, reference character's disappointed face at the tray's edge"
    },
    {
      "location": "newspaper fact-checking room",
      "narration": "[slows down] That causes public trust in society to break down fast.",
      "image_prompt": "reference character stands resigned beside a tall stack of newspapers collapsing sideways off a wooden trolley onto the floor, bright yellow twine snapped, wide shot",
      "image_prompt_alt": "low-angle close-up of newspapers sliding off a wooden trolley with snapped bright yellow twine, reference character standing resigned in the background"
    },
    {
      "location": "bank loan records archive",
      "narration": "Another major danger is automated prejudice.",
      "image_prompt": "reference character stands beside a brass weighing scale on a steel reading table, one pan heaped with maroon folders, the other raised high, skeptical look, medium shot",
      "image_prompt_alt": "close-up of a brass weighing scale tilted hard to one side under maroon folders on a steel reading table, reference character skeptical at frame right"
    },
    {
      "location": "bank loan records archive",
      "narration": "Computer algorithms learn from old historical human records.",
      "image_prompt": "reference character sits on a rolling ladder looking at yellowed ledger books stacked on a reading table, a thick black cable running from them into a small beige computer, curious, wide shot",
      "image_prompt_alt": "close-up of yellowed ledger books with a thick black cable running into a small beige computer, reference character seated on a rolling ladder behind, curious"
    },
    {
      "location": "bank loan records archive",
      "narration": "[annoyed] If old data contains human bias, the system copy-pastes that unfairness into FUTURE decisions.",
      "image_prompt": "reference character stands annoyed beside a beige photocopier spewing a long trail of identical sheets marked with bold red crosses across the floor, high-angle shot",
      "image_prompt_alt": "floor-level shot along the trail of identical sheets marked with bold red crosses leading back to a beige photocopier, reference character annoyed beside it"
    },
    {
      "location": "bank loan records archive",
      "narration": "[upset] Studies show facial recognition tools fail much more often on non-white faces.",
      "image_prompt": "reference character frowns at a monitor on a steel stand showing six portrait photographs of different people, bright green tracking squares on some and red error squares on others, medium shot",
      "image_prompt_alt": "close-up of a monitor showing six portrait photographs with bright green tracking squares on some and red error squares on others, reference character frowning at its side"
    },
    {
      "location": "bank loan records archive",
      "narration": "Some automated banking tools quietly deny loan applications based on flawed historical patterns.",
      "image_prompt": "reference character eyes a beige computer terminal on a steel desk pushing out paper slips each marked with a bold red cross into a growing pile, quietly disappointed, medium-wide shot",
      "image_prompt_alt": "close-up of paper slips marked with bold red crosses piling beneath a beige computer terminal, reference character leaning on the steel desk behind, disappointed"
    },
    {
      "location": "half-vacated call-centre floor",
      "narration": "Then we must consider jobs and employment.",
      "image_prompt": "reference character wanders between rows of unoccupied grey cubicle desks with lime green dividers, one headset draped over each chair, looking thoughtful, wide shot",
      "image_prompt_alt": "high-angle shot over rows of unoccupied grey cubicle desks with lime green dividers and headsets draped on chairs, reference character small in one aisle, thoughtful"
    },
    {
      "location": "half-vacated call-centre floor",
      "narration": "[drawn out] Entry-level jobs in coding, translation, and customer support are changing RAPIDLY.",
      "image_prompt": "reference character sits at a cubicle desk beside a bright green plastic crate piled with foreign-language dictionaries, a thick paperback manual and a telephone headset, resigned, medium shot",
      "image_prompt_alt": "close-up of dictionaries, a thick paperback manual and a telephone headset piled in a bright green plastic crate on the desk, reference character resigned behind them"
    },
    {
      "location": "half-vacated call-centre floor",
      "narration": "Software will not replace everyone, but workers using software will replace those who do not.",
      "image_prompt": "reference character leans on a divider thoughtfully watching a young worker in a lime green sweater at a laptop while an older worker in a brown cardigan stands beside a cardboard box, medium-wide shot",
      "image_prompt_alt": "over-the-shoulder shot from behind reference character, facing a young worker in a lime green sweater at a laptop and an older worker in a brown cardigan beside a cardboard box"
    },
    {
      "location": "glass-topped executive boardroom",
      "narration": "[angry] Meanwhile, massive technology corporations are gaining immense CONTROL over information.",
      "image_prompt": "reference character stands at the far end of a long glass table, mildly irritated, as four executives in dark suits sit around a large brass globe tangled with purple cables, wide shot",
      "image_prompt_alt": "low-angle shot from table height past the large brass globe tangled with purple cables, four executives in dark suits seated behind it, reference character irritated in the background"
    },
    {
      "location": "glass-topped executive boardroom",
      "narration": "Power is concentrating into the hands of a small group of tech executives.",
      "image_prompt": "reference character stands unimpressed beside a single towering stack of gold coins on the glass table, tiny coins scattered around it, four executives in dark suits leaning over it, medium shot",
      "image_prompt_alt": "close-up of a single towering stack of gold coins on the glass table with tiny coins scattered around, four executives in dark suits behind, reference character unimpressed at frame left"
    },
    {
      "location": "data-centre cooling hall",
      "narration": "[loudly] Furthermore, AI relies on astronomical amounts of electrical POWER.",
      "image_prompt": "reference character stands dwarfed beside tall grey ribbed metal cabinets with thick bright orange power cables coiling across the floor, tired look, low-angle wide shot",
      "image_prompt_alt": "overhead shot of thick bright orange power cables coiling across the grating toward tall grey ribbed metal cabinets, reference character standing among the coils, tired"
    },
    {
      "location": "data-centre cooling hall",
      "narration": "[awe] According to the International Energy Agency, one AI search uses ten times more electricity than a basic search.",
      "image_prompt": "reference character, eyebrows raised, stands between one light bulb on a stool and ten identical light bulbs lined along a long steel bench, all joined by bright orange cables, medium-wide shot",
      "image_prompt_alt": "close-up at bench height along ten identical light bulbs on bright orange cables, a single light bulb on a stool at far left, reference character raising eyebrows in the background"
    },
    {
      "location": "data-centre cooling hall",
      "narration": "Massive data centers consume huge amounts of local water and energy grids.",
      "image_prompt": "reference character stands mildly concerned beside a massive blue plastic water tank feeding thick pipes into black metal cabinets, a wide puddle spreading across the floor, wide shot",
      "image_prompt_alt": "low-angle close-up of a puddle beneath a massive blue plastic water tank with thick pipes running into black metal cabinets, reference character concerned behind"
    },
    {
      "location": "robot movie prop depot",
      "narration": "[stammers] So... is technology going to destroy us tomorrow?",
      "image_prompt": "reference character sits on the toppled chrome robot prop, looking doubtful, a round bright red alarm clock resting on the concrete floor beside them, medium shot",
      "image_prompt_alt": "close-up of a round bright red alarm clock on the concrete floor, the toppled chrome robot prop behind with reference character seated on it, doubtful"
    },
    {
      "location": "robot movie prop depot",
      "narration": "[sighs] No... human careless behaviour combined with fast software is the ACTUAL threat.",
      "image_prompt": "reference character stands with a resigned sigh beside a bright red go-kart carrying a beige laptop soaked by a toppled coffee mug, medium-wide shot",
      "image_prompt_alt": "low-angle shot beside the bright red go-kart, beige laptop soaked by a toppled coffee mug in the foreground, reference character standing behind with a resigned sigh"
    },
    {
      "location": "robot movie prop depot",
      "narration": "[softly] The tool itself is not evil, but humans can use it foolishly.",
      "image_prompt": "reference character sits on a crate beside a single red-handled hammer resting on a wooden workbench, one nail bent sideways in a plank nearby, gentle thoughtful look, close-up",
      "image_prompt_alt": "overhead shot of a red-handled hammer and a plank with one bent nail on the wooden workbench, reference character seated beside it, thoughtful"
    },
    {
      "location": "parliament committee chamber",
      "narration": "Governments are beginning to pass regulations like the European Union AI Act.",
      "image_prompt": "reference character sits in the back row, curious, watching lawmakers in dark suits seated along the tiered bench beneath a large European Union flag on a steel pole, wide shot",
      "image_prompt_alt": "low-angle shot from the front row toward lawmakers in dark suits on the tiered bench, a large blue flag with a ring of yellow stars behind, reference character curious at left"
    },
    {
      "location": "parliament committee chamber",
      "narration": "[happily] We need strict safety testing, transparency, and simple accountability.",
      "image_prompt": "reference character gives a slight approving nod beside a clear glass cabinet holding a beige laptop connected to bright red test clamps and a brass pressure gauge, medium shot",
      "image_prompt_alt": "close-up through the clear glass cabinet at a beige laptop with bright red test clamps and a brass pressure gauge, reference character nodding approvingly behind the glass"
    },
    {
      "location": "robot movie prop depot",
      "narration": "[amazed] Artificial intelligence will not wipe out humanity, but it is changing our REALITY.",
      "image_prompt": "reference character stands between the toppled chrome robot prop and a beige laptop on a wooden crate, mildly impressed, bright red tarpaulin spread beneath both, wide shot",
      "image_prompt_alt": "high-angle shot over the bright red tarpaulin, toppled chrome robot prop at one side and beige laptop on a crate at the other, reference character standing between, mildly impressed"
    },
    {
      "location": "robot movie prop depot",
      "narration": "[calm] Stay curious, double-check your sources, and keep thinking for yourself.",
      "image_prompt": "reference character sits on a wooden crate with a small tired smile, a brass magnifying glass and a stack of newspapers beside them, bright red tarpaulin behind, medium close-up",
      "image_prompt_alt": "wide shot at eye level, reference character seated on a wooden crate with a tired smile, brass magnifying glass and newspapers at their feet, bright red tarpaulin draping the robot props"
    }
  ],
  "music_prompt": "Sparse, curious instrumental bed with a quietly skeptical mood, around eighty BPM. Soft pulsing analog synth, muted upright piano, light brushed snare, and warm restrained bass guitar. Flat consistent energy with no build, no swells, no drops. Sits far in the background under a spoken narrator with the mid range left clear. Purely instrumental with no vocals of any kind. Understated rather than comedic."
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
