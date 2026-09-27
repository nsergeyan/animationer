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
  "topic": "top-5-beginner-anime",
  "format": "explainer",
  "plan": {
    "spine_question": "Which five anime series are the best starting points for someone who has never watched anime before?",
    "deflations": [
      {
        "assumed": "Anime is either too childish or requires watching hundreds of filler episodes.",
        "actual": "Top starter anime feature short, tightly structured stories with high-quality animation and mature drama.",
        "who_decided": "Newcomers who feel overwhelmed by massive long-running series like One Piece.",
        "build_beat": "Many people avoid anime because they fear getting stuck in endless filler seasons...",
        "drop_beat": "...but these five top shows deliver complete cinematic stories in just a few seasons."
      }
    ],
    "specifics": [
      {
        "fact": "Death Note consists of 37 episodes produced by Studio Madhouse with no filler content.",
        "source": "Studio Madhouse Official Catalog",
        "beat": "Beat 13"
      },
      {
        "fact": "Demon Slayer Mugen Train broke box office records to become the highest-grossing Japanese movie worldwide.",
        "source": "Box Office Mojo / Crunchyroll News",
        "beat": "Beat 24"
      },
      {
        "fact": "Fullmetal Alchemist Brotherhood was rated number one on MyAnimeList for over a decade across 64 episodes.",
        "source": "MyAnimeList Historical Stats",
        "beat": "Beat 36"
      },
      {
        "fact": "Jujutsu Kaisen was awarded the Guinness World Record for most in-demand animated series globally.",
        "source": "Guinness World Records / Parrot Analytics",
        "beat": "Beat 46"
      },
      {
        "fact": "Attack on Titan features a score composed by Hiroyuki Sawano and animation by Wit Studio and MAPPA.",
        "source": "Attack on Titan Official Credits",
        "beat": "Beat 57"
      }
    ],
    "facts_to_check": [
      {
        "claim": "Jujutsu Kaisen held the Guinness World Record for world most in-demand animated TV show.",
        "source": "Guinness World Records 2024"
      },
      {
        "claim": "Demon Slayer Mugen Train is the highest-grossing Japanese film in history.",
        "source": "The Numbers / Box Office Mojo"
      }
    ],
    "locations": [
      {
        "name": "cozy apartment living room",
        "visual_anchor": "deep teal plaster walls, worn honey oak floorboards, one broad black television mounted on the main wall"
      },
      {
        "name": "Japanese suburban teenage bedroom",
        "visual_anchor": "cream papered walls, pale beige carpet floor, one tall sliding window beside a built-in pale wooden desk alcove"
      },
      {
        "name": "Japanese high school courtyard",
        "visual_anchor": "pale grey concrete paving, cream four-storey school facade, one long green chain-link fence along the edge"
      },
      {
        "name": "Tokyo high-rise investigation suite",
        "visual_anchor": "off-white paneled walls, pale grey carpet, one floor-to-ceiling window overlooking a dense grey city skyline"
      },
      {
        "name": "snowy mountain charcoal hut",
        "visual_anchor": "rough dark timber walls, packed earth floor, one square sunken hearth, thick white snow banked against the doorway"
      },
      {
        "name": "dense cedar forest clearing",
        "visual_anchor": "towering dark cedar trunks, mossy uneven ground, one weathered stone shrine lantern, deep green canopy overhead"
      },
      {
        "name": "steam train passenger carriage",
        "visual_anchor": "polished dark wood-panelled walls, deep red upholstered bench seats, one long aisle of worn green floor matting"
      },
      {
        "name": "Elric family basement workshop",
        "visual_anchor": "rough grey fieldstone walls, dusty oak plank floor, one enormous white chalk circle drawn across the boards"
      },
      {
        "name": "dusty frontier railway platform",
        "visual_anchor": "sun-bleached timber platform boards, red brick station wall, one iron clock tower above the tracks, ochre earth beyond"
      },
      {
        "name": "urban high school sports field",
        "visual_anchor": "rust-red running track, bright green artificial turf, one tall grey concrete grandstand along the far side"
      },
      {
        "name": "concrete high school rooftop",
        "visual_anchor": "pale grey concrete floor, tall green chain-link fencing, one squat stairwell hut with a steel door"
      },
      {
        "name": "Tokyo Jujutsu High temple courtyard",
        "visual_anchor": "raked pale gravel ground, dark timber temple halls with sweeping black tiled roofs, one vermilion torii gate"
      },
      {
        "name": "Shiganshina walled district",
        "visual_anchor": "rough grey cobblestones, pale plaster townhouse facades with dark timber beams, one towering sandstone wall across the horizon"
      }
    ],
    "setting_anchor": ""
  },
  "beats": [
    {
      "narration": "[curious] Want to start watching anime but do not know where to begin?",
      "location": "cozy apartment living room",
      "image_prompt": "reference character sits on a teal velvet couch with a curious frown, looking toward the television showing a sprawling grid of colourful tiles, a black remote resting on the cushion, medium-wide shot",
      "image_prompt_alt": "over-the-shoulder shot from behind reference character seated on a teal velvet couch, head tilted curiously toward the television filled with a sprawling grid of colourful tiles, a black remote on the cushion"
    },
    {
      "narration": "[sarcastic] With thousands of shows out there, picking the wrong one can waste your whole weekend.",
      "location": "cozy apartment living room",
      "image_prompt": "reference character slumps sideways on the teal velvet couch with a tired skeptical look, a heap of crumpled white cardboard food boxes on a low pine table, high-angle shot",
      "image_prompt_alt": "low side angle toward reference character half-sunk into the teal velvet couch, skeptical and tired, a low pine table piled with crumpled white cardboard food boxes in the foreground"
    },
    {
      "narration": "[rushed] You do not need five hundred filler episodes about talking ninja dogs.",
      "location": "cozy apartment living room",
      "image_prompt": "close-up of reference character on the couch, arms crossed and unimpressed, while the television beside him shows a small cartoon pug in a bright blue ninja headband mid-chatter",
      "image_prompt_alt": "wide shot from beside the television, a small cartoon pug in a bright blue ninja headband filling the screen while reference character watches from the teal velvet couch, arms crossed, unimpressed"
    },
    {
      "narration": "[excited] You need five epic stories that grab your attention from minute one.",
      "location": "cozy apartment living room",
      "image_prompt": "reference character leans forward on the teal couch, eyes widening with interest at the television split into five bright panels: black notebook, checkered cloth, steel armor, blindfold, stone wall, medium shot",
      "image_prompt_alt": "low angle past the television edge, reference character leaning off the teal couch, intrigued, the screen divided into five bright panels: black notebook, checkered cloth, steel armor, blindfold, stone wall"
    },
    {
      "narration": "[clears throat] Here are the top five best anime for beginners.",
      "location": "cozy apartment living room",
      "image_prompt": "reference character stands beside the mounted television with arms folded and a quietly interested half-smile, a bright orange floor cushion at his feet, the screen showing solid crimson, wide shot at eye level",
      "image_prompt_alt": "medium shot, reference character standing side-on beside the television, arms folded, quietly interested, a solid crimson screen behind and a bright orange floor cushion resting on the oak boards"
    },
    {
      "narration": "[dramatically] Number five, Death Note.",
      "location": "Japanese suburban teenage bedroom",
      "image_prompt": "Light Yagami from Death Note, a neat brown-haired boy in a tan school blazer, sits bent over the black Death Note notebook at the desk while reference character watches from the doorway edge, intrigued, red desk lamp, medium-wide shot",
      "image_prompt_alt": "a neat brown-haired boy in a tan school blazer, slim and tall, sharp amber eyes, a red striped tie, bent over a slim matte black notebook at the desk, reference character intrigued at the frame edge, red desk lamp, low side angle"
    },
    {
      "narration": "A smart high school student named Light Yagami finds a mysterious notebook on the ground.",
      "location": "Japanese high school courtyard",
      "image_prompt": "high-angle shot of Light Yagami from Death Note, a neat brown-haired boy in a tan school blazer, stooping over the black Death Note notebook lying on the paving, reference character small in the background beside a blue bench, curious",
      "image_prompt_alt": "a neat brown-haired boy in a tan school blazer, slim and tall, sharp amber eyes, a red striped tie, stoops toward a slim matte black notebook lying on the paving, reference character curious beside a blue bench in the foreground, eye-level wide shot"
    },
    {
      "narration": "If he writes a person's name inside it, that person dies instantly.",
      "location": "Japanese suburban teenage bedroom",
      "image_prompt": "over-the-shoulder close-up of Light Yagami from Death Note, a neat brown-haired boy in a tan school blazer, pen poised above an open page of the black Death Note notebook, reference character wary at the frame edge, red desk lamp",
      "image_prompt_alt": "medium side shot of a neat brown-haired boy in a tan school blazer, slim and tall, sharp amber eyes, a red striped tie, pen poised above a slim matte black notebook, reference character wary in the foreground, red desk lamp"
    },
    {
      "narration": "Light decides to use this power to eliminate all bad criminals in the world.",
      "location": "Japanese suburban teenage bedroom",
      "image_prompt": "Light Yagami from Death Note, a neat brown-haired boy in a tan school blazer, writes fast in the black Death Note notebook facing a small television of grey faces, reference character uneasy on the red bedspread behind, medium-wide shot",
      "image_prompt_alt": "wide shot from the red bedspread where reference character sits uneasy, a neat brown-haired boy in a tan school blazer, slim and tall, sharp amber eyes, a red striped tie, writing fast in a slim matte black notebook beside a small television of grey faces"
    },
    {
      "narration": "[slows down] But then... a super genius detective named L enters the game.",
      "location": "Tokyo high-rise investigation suite",
      "image_prompt": "L from Death Note, a pale hunched young man with messy black hair in a white long-sleeved shirt, crouches barefoot on an armchair facing a wall of blue monitors, reference character standing behind, intrigued, low-angle shot",
      "image_prompt_alt": "side shot of a pale hunched young man with messy black hair in a white long-sleeved shirt, thin and barefoot, dark rings under wide eyes, faded blue jeans, crouched on an armchair before a wall of blue monitors, reference character intrigued by the window"
    },
    {
      "narration": "What follows is an intense mind game where both try to discover each other's identity.",
      "location": "Tokyo high-rise investigation suite",
      "image_prompt": "L from Death Note, a pale hunched young man with messy black hair in a white long-sleeved shirt, crouches opposite Light Yagami from Death Note, a neat brown-haired boy in a tan school blazer, across a low glass table, reference character absorbed between them, medium three-shot",
      "image_prompt_alt": "high-angle shot, a pale hunched young man with messy black hair in a white long-sleeved shirt, thin and barefoot, dark rings under wide eyes, faded blue jeans, crouched across a low glass table from a neat brown-haired boy in a tan school blazer, slim and tall, sharp amber eyes, a red striped tie, reference character absorbed at the far end"
    },
    {
      "narration": "[whispers] No giant magic powers, just pure intellectual battle.",
      "location": "Tokyo high-rise investigation suite",
      "image_prompt": "tight two-shot of Light Yagami from Death Note, a neat brown-haired boy in a tan school blazer, locking eyes with L from Death Note, a pale hunched young man with messy black hair in a white long-sleeved shirt, over a single white sugar cube, reference character leaning in at the edge, hushed and fascinated",
      "image_prompt_alt": "low wide shot at table height, a neat brown-haired boy in a tan school blazer, slim and tall, sharp amber eyes, a red striped tie, staring across a single white sugar cube at a pale hunched young man with messy black hair in a white long-sleeved shirt, thin and barefoot, dark rings under wide eyes, faded blue jeans, reference character hushed by the window"
    },
    {
      "narration": "The show is only thirty seven episodes long with zero slow filler.",
      "location": "Japanese suburban teenage bedroom",
      "image_prompt": "reference character watches Light Yagami from Death Note, a neat brown-haired boy in a tan school blazer, writing at speed in the black Death Note notebook while one untouched notebook lies beside him, red desk lamp, medium two-shot",
      "image_prompt_alt": "overhead shot of a neat brown-haired boy in a tan school blazer, slim and tall, sharp amber eyes, a red striped tie, writing at speed in a slim matte black notebook beside one untouched notebook, reference character impressed at the frame edge, red desk lamp"
    },
    {
      "narration": "Every episode ends with a massive cliffhanger that keeps you watching.",
      "location": "Japanese suburban teenage bedroom",
      "image_prompt": "Light Yagami from Death Note, a neat brown-haired boy in a tan school blazer, freezes and glances up at a tiny black camera tucked into the ceiling corner, reference character following his gaze, hooked, low-angle shot",
      "image_prompt_alt": "high-angle shot from the ceiling corner past a tiny black camera, a neat brown-haired boy in a tan school blazer, slim and tall, sharp amber eyes, a red striped tie, glancing upward, reference character hooked and tense below by the window"
    },
    {
      "narration": "[deadpan] There is even a scene where eating food becomes intense... drama over a potato *CHIP!*",
      "location": "Japanese suburban teenage bedroom",
      "image_prompt": "extreme close-up of Light Yagami from Death Note, a neat brown-haired boy in a tan school blazer, lifting a single potato chip from a torn bright yellow foil bag at the desk, reference character amused at the frame edge",
      "image_prompt_alt": "medium side shot of a neat brown-haired boy in a tan school blazer, slim and tall, sharp amber eyes, a red striped tie, lifting a single potato chip from a torn bright yellow foil bag, a slim matte black notebook half-hidden, reference character amused behind the bed"
    },
    {
      "narration": "[flatly] If you like detective thrillers, this is your starter pack.",
      "location": "Tokyo high-rise investigation suite",
      "image_prompt": "reference character sits back in a grey armchair, warmly convinced, watching L from Death Note, a pale hunched young man with messy black hair in a white long-sleeved shirt, crouched over a laptop across the room, blue monitors along the wall, medium-wide shot",
      "image_prompt_alt": "close-up of reference character, warmly convinced, turned toward a pale hunched young man with messy black hair in a white long-sleeved shirt, thin and barefoot, dark rings under wide eyes, faded blue jeans, crouched over a laptop in the background beside blue monitors"
    },
    {
      "narration": "[happily] Number four, Demon Slayer.",
      "location": "dense cedar forest clearing",
      "image_prompt": "Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, stands in the clearing with a black sword drawn and a tall pale wooden box strapped to his back, reference character pleased at the frame edge, wide shot",
      "image_prompt_alt": "low-angle shot of a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, black sword drawn, a tall pale wooden box on his back, reference character pleased in the foreground"
    },
    {
      "narration": "Tanjiro is a sweet boy who sells charcoal to feed his family.",
      "location": "snowy mountain charcoal hut",
      "image_prompt": "Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, steps out the snowy doorway under a wooden frame of black charcoal sacks, reference character warmly watching from beside the hearth, medium shot",
      "image_prompt_alt": "wide shot from outside in the snow, a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, stepping out under a wooden frame of black charcoal sacks, reference character warmly watching from inside"
    },
    {
      "narration": "[sorrowful] One day, an evil demon attacks his home and leaves only his sister alive.",
      "location": "snowy mountain charcoal hut",
      "image_prompt": "Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, kneels in the snow at the broken doorway beside Nezuko from Demon Slayer, a small girl in a pink kimono with a bamboo muzzle strapped across her mouth, splintered planks around them, reference character sorrowful behind, high-angle wide shot",
      "image_prompt_alt": "low-angle shot from the snow, a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, kneeling beside a small girl in a pink kimono with a bamboo muzzle strapped across her mouth, slender, long black hair fading to orange at the tips, splintered planks scattered, reference character sorrowful behind"
    },
    {
      "narration": "[happy gasp] His sister Nezuko turns into a demon... but keeps her human love for him.",
      "location": "snowy mountain charcoal hut",
      "image_prompt": "Nezuko from Demon Slayer, a small girl in a pink kimono with a bamboo muzzle strapped across her mouth, kneels protectively beside Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, eyes soft with recognition, reference character moved in the doorway, medium two-shot",
      "image_prompt_alt": "close two-shot, a small girl in a pink kimono with a bamboo muzzle strapped across her mouth, slender, long black hair fading to orange at the tips, kneeling beside a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, reference character moved in the background doorway"
    },
    {
      "narration": "Tanjiro joins an elite sword team to fight monsters and find a cure.",
      "location": "dense cedar forest clearing",
      "image_prompt": "Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, swings his sword at a hulking pale demon with long black claws, reference character crouched tense behind a cedar trunk, wide action shot",
      "image_prompt_alt": "low-angle shot of a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, swinging a sword at a hulking pale demon with long black claws, reference character tense behind a cedar trunk in the foreground"
    },
    {
      "narration": "[softly] The animation by Studio Ufotable looks like liquid art on screen.",
      "location": "dense cedar forest clearing",
      "image_prompt": "reference character stands mesmerized at the clearing edge while Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, spins mid-air, a rolling sapphire wave of water curling off his blade, medium-wide shot",
      "image_prompt_alt": "overhead shot of a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, spinning mid-air as a rolling sapphire wave of water curls off his blade, reference character mesmerized at the clearing edge below"
    },
    {
      "narration": "Water and fire effects flow from their swords in stunning detail.",
      "location": "dense cedar forest clearing",
      "image_prompt": "Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, slashes forward as a spiral of sapphire water turns into roaring orange fire along the blade, reference character leaning back, awed, low-angle shot",
      "image_prompt_alt": "wide side shot of a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, slashing forward, sapphire water turning into roaring orange fire along the blade, reference character awed at the frame edge"
    },
    {
      "narration": "[amazed] Its movie Mugen Train became a global phenomenon and set a box office *RECORD!*",
      "location": "steam train passenger carriage",
      "image_prompt": "Kyojuro Rengoku from Demon Slayer, a blond man with red-tipped hair in a white flame-patterned cape, sits beside Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, on the red bench, reference character delighted opposite, medium three-shot",
      "image_prompt_alt": "wide shot down the carriage aisle, a blond man with red-tipped hair in a white flame-patterned cape, broad-shouldered and tall, wide golden eyes, a black uniform beneath, seated beside a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, reference character delighted in the facing seat"
    },
    {
      "narration": "The plot is simple, emotional, and easy to follow.",
      "location": "dense cedar forest clearing",
      "image_prompt": "rear tracking shot of Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, walking a straight mossy path with the tall pale wooden box on his back, reference character strolling behind, relaxed and content",
      "image_prompt_alt": "front wide shot, a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, walking a straight mossy path toward camera with a tall pale wooden box on his back, reference character content a few steps behind"
    },
    {
      "narration": "You will never get lost in complex lore.",
      "location": "dense cedar forest clearing",
      "image_prompt": "reference character sits at ease on a mossy stone beside the shrine lantern as Tanjiro Kamado from Demon Slayer, a boy in a green and black checkered haori, nods down one single clear path through the cedars, medium shot",
      "image_prompt_alt": "high-angle shot, a boy in a green and black checkered haori, sturdy build, dark red hair, a scar on his forehead, dangling white rectangular earrings, standing at the head of one single clear path through the cedars, reference character at ease on a mossy stone beside him"
    },
    {
      "narration": "[giggles] Plus, Nezuko popping out of a wooden box is adorable.",
      "location": "dense cedar forest clearing",
      "image_prompt": "close-up of Nezuko from Demon Slayer, a small girl in a pink kimono with a bamboo muzzle strapped across her mouth, popping her head out of the tall pale wooden box on the mossy ground, reference character crouched beside it, grinning",
      "image_prompt_alt": "low eye-level two-shot, a small girl in a pink kimono with a bamboo muzzle strapped across her mouth, slender, long black hair fading to orange at the tips, peeking up from inside a tall pale wooden box on the moss, reference character grinning on the other side"
    },
    {
      "narration": "[excitedly] Number three, Fullmetal Alchemist Brotherhood.",
      "location": "dusty frontier railway platform",
      "image_prompt": "Edward Elric from Fullmetal Alchemist, a short blond boy in a long red coat with a steel right arm, stands beside Alphonse Elric from Fullmetal Alchemist, a towering hollow steel suit of armor, reference character leaning on the brick wall, excited, wide shot at eye level",
      "image_prompt_alt": "low-angle two-shot, a short blond boy in a long red coat with a steel right arm, slim build, a golden braid, gold eyes, black trousers, beside a towering hollow steel suit of armor, broad-shouldered, a spiked helmet with one long white tassel, a red cloth at the waist, reference character excited against the brick wall behind"
    },
    {
      "narration": "Two young brothers, Edward and Alphonse, lose their mother to illness.",
      "location": "Elric family basement workshop",
      "image_prompt": "young Edward Elric from Fullmetal Alchemist, a small blond boy with a short golden ponytail, sits beside young Alphonse Elric from Fullmetal Alchemist, a small boy with short dark-blond hair, on stone steps beneath a framed photograph of a smiling brown-haired woman, reference character sad in the corner, medium-wide shot",
      "image_prompt_alt": "close two-shot, a small blond boy with a short golden ponytail, thin build, gold eyes, a plain black vest over a white shirt, huddled beside a small boy with short dark-blond hair, round gentle face, grey eyes, a green knitted sweater, below a framed photograph of a smiling brown-haired woman, reference character sad behind"
    },
    {
      "narration": "[sad] They try forbidden alchemy to bring her back to life.",
      "location": "Elric family basement workshop",
      "image_prompt": "high-angle shot of young Edward Elric from Fullmetal Alchemist, a small blond boy with a short golden ponytail, and young Alphonse Elric from Fullmetal Alchemist, a small boy with short dark-blond hair, kneeling at the chalk circle's edge among open red leather books, reference character uneasy behind them",
      "image_prompt_alt": "floor-level side shot, a small blond boy with a short golden ponytail, thin build, gold eyes, a plain black vest over a white shirt, and a small boy with short dark-blond hair, round gentle face, grey eyes, a green knitted sweater, kneeling at the circle's edge among open red leather books, reference character uneasy in the doorway"
    },
    {
      "narration": "[drawn out] The ritual goes terribly wrong... and takes a heavy price.",
      "location": "Elric family basement workshop",
      "image_prompt": "jagged blue lightning erupts from the chalk circle as young Edward Elric from Fullmetal Alchemist, a small blond boy with a short golden ponytail, is thrown backward, reference character pressed against the stone wall, alarmed, wide shot",
      "image_prompt_alt": "low-angle shot, jagged blue lightning erupting from the circle, a small blond boy with a short golden ponytail, thin build, gold eyes, a plain black vest over a white shirt, thrown backward across the planks, reference character alarmed against the stone wall"
    },
    {
      "narration": "Edward loses two limbs, and Alphonse loses his physical body completely.",
      "location": "Elric family basement workshop",
      "image_prompt": "overhead shot of young Edward Elric from Fullmetal Alchemist, a small blond boy with a short golden ponytail, slumped on the boards with his right sleeve hanging empty beside a heap of empty green clothes in the circle's center, reference character kneeling nearby, stricken",
      "image_prompt_alt": "floor-level medium shot, a small blond boy with a short golden ponytail, thin build, gold eyes, a plain black vest over a white shirt, slumped with his right sleeve hanging empty, a heap of empty green clothes in the circle's center, reference character stricken beside him"
    },
    {
      "narration": "[surprised] To save his brother, Edward attaches his soul to a giant suit of *ARMOR!*",
      "location": "Elric family basement workshop",
      "image_prompt": "Alphonse Elric from Fullmetal Alchemist, a towering hollow steel suit of armor, sits up inside a small crimson circle, two red points in its helmet slits, young Edward Elric from Fullmetal Alchemist, a small blond boy with a short golden ponytail, collapsed against it, reference character stunned, low-angle shot",
      "image_prompt_alt": "wide shot, a towering hollow steel suit of armor, broad-shouldered, a spiked helmet with one long white tassel, a red cloth at the waist, rising inside a small crimson circle, two red points in the helmet slits, a small blond boy with a short golden ponytail, thin build, gold eyes, a plain black vest over a white shirt, collapsed against it, reference character stunned by the wall"
    },
    {
      "narration": "They travel the world to find a magical artifact and fix their bodies.",
      "location": "dusty frontier railway platform",
      "image_prompt": "rear three-quarter shot of Edward Elric from Fullmetal Alchemist, a short blond boy in a long red coat with a steel right arm, and Alphonse Elric from Fullmetal Alchemist, a towering hollow steel suit of armor, walking toward a green steam train, reference character hopeful behind",
      "image_prompt_alt": "front wide shot, a short blond boy in a long red coat with a steel right arm, slim build, a golden braid, gold eyes, black trousers, and a towering hollow steel suit of armor, broad-shouldered, a spiked helmet with one long white tassel, a red cloth at the waist, walking beside a green steam train with a brown leather suitcase, reference character hopeful behind"
    },
    {
      "narration": "[light chuckle] It blends funny comedy, deep political conspiracy, and heart.",
      "location": "dusty frontier railway platform",
      "image_prompt": "Edward Elric from Fullmetal Alchemist, a short blond boy in a long red coat with a steel right arm, stamps furiously in front of Alphonse Elric from Fullmetal Alchemist, a towering hollow steel suit of armor, reference character quietly laughing on a yellow wooden bench, medium-wide shot",
      "image_prompt_alt": "low-angle shot, a short blond boy in a long red coat with a steel right arm, slim build, a golden braid, gold eyes, black trousers, stamping furiously before a towering hollow steel suit of armor, broad-shouldered, a spiked helmet with one long white tassel, a red cloth at the waist, reference character laughing on a yellow wooden bench"
    },
    {
      "narration": "This show stayed at the top of world anime rankings for over ten years.",
      "location": "dusty frontier railway platform",
      "image_prompt": "reference character looks up in admiration at Alphonse Elric from Fullmetal Alchemist, a towering hollow steel suit of armor, standing over him, one steel hand resting on a wooden crate, the red brick wall behind, low-angle shot",
      "image_prompt_alt": "wide profile shot, reference character admiring a towering hollow steel suit of armor, broad-shouldered, a spiked helmet with one long white tassel, a red cloth at the waist, standing over him with one steel hand on a wooden crate, the clock tower above"
    },
    {
      "narration": "It has sixty four episodes and finishes with a perfect ending.",
      "location": "dusty frontier railway platform",
      "image_prompt": "wide rear shot of Edward Elric from Fullmetal Alchemist, a short blond boy in a long red coat with a steel right arm, and Alphonse Elric from Fullmetal Alchemist, a towering hollow steel suit of armor, walking down the tracks toward ochre hills, reference character satisfied on the platform edge",
      "image_prompt_alt": "high-angle shot from the clock tower, a short blond boy in a long red coat with a steel right arm, slim build, a golden braid, gold eyes, black trousers, and a towering hollow steel suit of armor, broad-shouldered, a spiked helmet with one long white tassel, a red cloth at the waist, walking away toward ochre hills, reference character satisfied below"
    },
    {
      "narration": "[booming] A masterclass in storytelling.",
      "location": "dusty frontier railway platform",
      "image_prompt": "Edward Elric from Fullmetal Alchemist, a short blond boy in a long red coat with a steel right arm, presses his palms to the boards as a jagged stone spike bursts upward, reference character stepping back, deeply impressed, medium-wide shot",
      "image_prompt_alt": "low-angle close shot, a short blond boy in a long red coat with a steel right arm, slim build, a golden braid, gold eyes, black trousers, pressing his palms to the boards as a jagged stone spike bursts upward, reference character impressed beside the brick wall"
    },
    {
      "narration": "[mischievously] Number two, Jujutsu Kaisen.",
      "location": "Tokyo Jujutsu High temple courtyard",
      "image_prompt": "Yuji Itadori from Jujutsu Kaisen, a pink-haired boy in a black school uniform, drops into a fighting stance on the gravel before the vermilion torii gate, reference character playfully intrigued on the temple steps, wide shot",
      "image_prompt_alt": "low-angle shot, a pink-haired boy in a black school uniform, athletic muscular build, spiky short hair with dark roots, a red hood at the collar, in a fighting stance on the gravel, reference character intrigued at the frame edge"
    },
    {
      "narration": "High school student Yuji Itadori is insanely strong and loves athletic sports.",
      "location": "urban high school sports field",
      "image_prompt": "Yuji Itadori from Jujutsu Kaisen, a pink-haired boy in a black school uniform, hurls a heavy iron shot put ball far across the green turf, reference character stunned beside the grandstand, wide shot",
      "image_prompt_alt": "low side shot, a pink-haired boy in a black school uniform, athletic muscular build, spiky short hair with dark roots, a red hood at the collar, mid-throw launching a heavy iron shot put ball over the green turf, reference character stunned in the foreground"
    },
    {
      "narration": "[frustrated] But his life changes when he eats a gross, cursed finger to save friends.",
      "location": "concrete high school rooftop",
      "image_prompt": "Yuji Itadori from Jujutsu Kaisen, a pink-haired boy in a black school uniform, swallows a withered grey finger as a hulking grey spirit with a cluster of bulging eyes looms over the fence, reference character recoiling, grossed out, low-angle shot",
      "image_prompt_alt": "wide shot, a pink-haired boy in a black school uniform, athletic muscular build, spiky short hair with dark roots, a red hood at the collar, swallowing a withered grey finger beneath a hulking grey spirit with a cluster of bulging eyes, reference character grossed out by the stairwell"
    },
    {
      "narration": "[stammers] Now he hosts Sukuna... the scary King of Curses inside his body.",
      "location": "concrete high school rooftop",
      "image_prompt": "close-up of Yuji Itadori from Jujutsu Kaisen, a pink-haired boy in a black school uniform, possessed by Sukuna from Jujutsu Kaisen, black tattoo lines beneath a second pair of eyes, grinning coldly, reference character nervous against the steel door",
      "image_prompt_alt": "medium shot, a pink-haired boy in a black school uniform, athletic muscular build, spiky short hair with dark roots, a red hood at the collar, black tattoo lines beneath a second pair of eyes, grinning coldly, reference character nervous at the frame edge"
    },
    {
      "narration": "Yuji attends a special school for sorcerers who fight evil spirits.",
      "location": "Tokyo Jujutsu High temple courtyard",
      "image_prompt": "wide rear shot of Yuji Itadori from Jujutsu Kaisen, a pink-haired boy in a black school uniform, walking through the vermilion torii gate toward the dark timber halls, reference character strolling beside him, curious",
      "image_prompt_alt": "front medium two-shot, a pink-haired boy in a black school uniform, athletic muscular build, spiky short hair with dark roots, a red hood at the collar, stepping through the vermilion torii gate, reference character curious at his side"
    },
    {
      "narration": "[suspicious tone] He meets Gojo Satoru, a teacher who wears a black blindfold.",
      "location": "Tokyo Jujutsu High temple courtyard",
      "image_prompt": "Gojo Satoru from Jujutsu Kaisen, a white-haired man in a black cloth blindfold, stands on the temple steps with hands in pockets, reference character squinting at him suspiciously from the gravel, medium-wide shot",
      "image_prompt_alt": "low-angle shot, a white-haired man in a black cloth blindfold, very tall and lean, spiky upswept hair, a high-collared dark navy jacket, on the temple steps, reference character squinting suspiciously in the foreground"
    },
    {
      "narration": "[shouts] Why does he cover his eyes... because he is too *STRONG!*",
      "location": "Tokyo Jujutsu High temple courtyard",
      "image_prompt": "extreme close-up of Gojo Satoru from Jujutsu Kaisen, a white-haired man in a black cloth blindfold, lifting it to reveal bright sky-blue eyes, reference character startled at the frame edge",
      "image_prompt_alt": "medium two-shot, a white-haired man in a black cloth blindfold, very tall and lean, spiky upswept hair, a high-collared dark navy jacket, raising it to reveal bright sky-blue eyes, reference character startled beside him on the gravel"
    },
    {
      "narration": "[applause] Guinness World Records crowned Jujutsu Kaisen as the most popular animated show.",
      "location": "Tokyo Jujutsu High temple courtyard",
      "image_prompt": "Yuji Itadori from Jujutsu Kaisen, a pink-haired boy in a black school uniform, stands back to back with Gojo Satoru from Jujutsu Kaisen, a white-haired man in a black cloth blindfold, amid swirling crimson smoke, reference character impressed on the temple steps, wide shot",
      "image_prompt_alt": "low-angle shot, a pink-haired boy in a black school uniform, athletic muscular build, spiky short hair with dark roots, a red hood at the collar, back to back with a white-haired man in a black cloth blindfold, very tall and lean, spiky upswept hair, a high-collared dark navy jacket, amid swirling crimson smoke, reference character impressed behind"
    },
    {
      "narration": "[rapid-fire] Modern music, fast fight choreography, and amazing characters.",
      "location": "Tokyo Jujutsu High temple courtyard",
      "image_prompt": "Yuji Itadori from Jujutsu Kaisen, a pink-haired boy in a black school uniform, drives a punch into a hulking grey spirit with a cluster of bulging eyes, black lightning crackling, reference character ducking by the gate, thrilled, low-angle shot",
      "image_prompt_alt": "wide side shot, a pink-haired boy in a black school uniform, athletic muscular build, spiky short hair with dark roots, a red hood at the collar, punching a hulking grey spirit with a cluster of bulging eyes amid crackling black lightning, reference character thrilled by the gate"
    },
    {
      "narration": "Every single battle feels like a blockbuster movie event.",
      "location": "Tokyo Jujutsu High temple courtyard",
      "image_prompt": "extreme wide shot, Gojo Satoru from Jujutsu Kaisen, a white-haired man in a black cloth blindfold, faces a towering grey spirit as a swirling violet sphere forms before him, reference character amazed on the temple steps",
      "image_prompt_alt": "low-angle medium shot, a white-haired man in a black cloth blindfold, very tall and lean, spiky upswept hair, a high-collared dark navy jacket, facing a towering grey spirit behind a swirling violet sphere, reference character amazed in the foreground"
    },
    {
      "narration": "You will be hooked after just two episodes.",
      "location": "Tokyo Jujutsu High temple courtyard",
      "image_prompt": "reference character sits on the temple steps, hooked and grinning, while Yuji Itadori from Jujutsu Kaisen, a pink-haired boy in a black school uniform, sits a few steps below eating from a red paper cup, medium shot",
      "image_prompt_alt": "wide shot from the gravel, reference character hooked and grinning on the temple steps above a pink-haired boy in a black school uniform, athletic muscular build, spiky short hair with dark roots, a red hood at the collar, eating from a red paper cup"
    },
    {
      "narration": "[nervously] Number one, Attack on Titan.",
      "location": "Shiganshina walled district",
      "image_prompt": "Eren Yeager from Attack on Titan, a dark-haired boy with fierce green eyes, stands in the cobbled street gazing up at the towering wall, reference character beside a wooden cart looking up too, apprehensive, low-angle wide shot",
      "image_prompt_alt": "medium rear shot, a dark-haired boy with fierce green eyes, lean build, messy shoulder-length hair, a brown leather strap harness over a white shirt, facing the towering wall, reference character apprehensive beside a wooden cart"
    },
    {
      "narration": "Humanity lives trapped inside three massive stone walls to stay safe.",
      "location": "Shiganshina walled district",
      "image_prompt": "extreme wide overhead shot of townsfolk in plain brown linen crowding the cobbled lanes, reference character on a red-tiled rooftop edge in the foreground, uneasy, the wall ringing the district",
      "image_prompt_alt": "wide street-level shot, townsfolk in plain brown linen filling the cobbled lanes beneath red-tiled roofs, reference character uneasy against a townhouse, the wall looming above"
    },
    {
      "narration": "[hesitates] Outside, gigantic human-like monsters called Titans roam... and eat people.",
      "location": "Shiganshina walled district",
      "image_prompt": "high-angle shot from atop the wall, a Titan from Attack on Titan, an enormous bald giant with an oversized grinning mouth, lumbers across green grassland below, reference character peering over the stone parapet, uneasy",
      "image_prompt_alt": "low-angle shot from the grass, an enormous bald giant with an oversized grinning mouth, pale smooth skin, bulging round eyes, lumbering past the wall base, reference character tiny and uneasy on the parapet above"
    },
    {
      "narration": "On a peaceful morning, a giant Titan kicks a hole in the outer wall.",
      "location": "Shiganshina walled district",
      "image_prompt": "the Colossal Titan from Attack on Titan, a skinless red giant towering over the wall, peers down as broken stone blasts inward from the gate, townsfolk in brown linen fleeing, reference character frozen in the street, wide shot",
      "image_prompt_alt": "low-angle shot from the cobbles, a skinless red giant towering over the wall, exposed muscle, white steam pouring from its body, a lipless jaw, broken stone blasting inward, townsfolk in brown linen fleeing past reference character, frozen"
    },
    {
      "narration": "[angry] After losing his mother, young Eren Yeager vows to destroy every *TITAN!*",
      "location": "Shiganshina walled district",
      "image_prompt": "Eren Yeager from Attack on Titan, a dark-haired boy with fierce green eyes, kneels in timber rubble with fists clenched as a Titan from Attack on Titan, an enormous bald giant with an oversized grinning mouth, walks away in the distance, reference character grieving behind, medium-wide shot",
      "image_prompt_alt": "close low shot, a dark-haired boy with fierce green eyes, lean build, messy shoulder-length hair, a brown leather strap harness over a white shirt, fists clenched in timber rubble, an enormous bald giant with an oversized grinning mouth, pale smooth skin, bulging round eyes, receding behind, reference character grieving at the frame edge"
    },
    {
      "narration": "[gasps] What begins as a simple survival story turns into a mind-blowing mystery.",
      "location": "Shiganshina walled district",
      "image_prompt": "extreme close-up of Eren Yeager from Attack on Titan, a dark-haired boy with fierce green eyes, staring at a small brass key hanging on a cord at his chest, reference character leaning in beside him, intrigued",
      "image_prompt_alt": "medium two-shot against a townhouse, a dark-haired boy with fierce green eyes, lean build, messy shoulder-length hair, a brown leather strap harness over a white shirt, studying a small brass key on a cord, reference character intrigued beside him"
    },
    {
      "narration": "Every season flips the world upside down with shocking plot twists.",
      "location": "Shiganshina walled district",
      "image_prompt": "the Attack Titan from Attack on Titan, a lean long-haired giant with bared teeth, roars mid-street among collapsing red-tiled roofs, reference character bracing against a townhouse, stunned, low-angle shot",
      "image_prompt_alt": "high-angle wide shot, a lean long-haired giant with bared teeth, sinewy muscular body, pointed ears, green eyes, roaring among collapsing red-tiled roofs, reference character stunned against a townhouse below"
    },
    {
      "narration": "The orchestral music during action scenes will give you chills.",
      "location": "Shiganshina walled district",
      "image_prompt": "Scout Regiment soldiers from Attack on Titan in green hooded cloaks swing between rooftops on taut steel cables, cloaks flaring, reference character on a chimney ledge watching, thrilled, wide shot",
      "image_prompt_alt": "low-angle shot from the cobbles, soldiers in green hooded cloaks with brown leather harnesses and steel blade canisters at their hips swinging overhead on taut cables, reference character thrilled on a chimney ledge"
    },
    {
      "narration": "[understated] It feels less like cartoon animation and more like high budget television.",
      "location": "Shiganshina walled district",
      "image_prompt": "extreme wide shot, the Colossal Titan from Attack on Titan, a skinless red giant towering over the wall, looms as Scout Regiment soldiers from Attack on Titan in green hooded cloaks fly toward it, reference character quietly impressed on the cobbles",
      "image_prompt_alt": "medium shot over the shoulder of reference character, quietly impressed, soldiers in green hooded cloaks with brown leather harnesses and steel blade canisters at their hips flying toward a skinless red giant towering over the wall, exposed muscle, white steam pouring from its body, a lipless jaw"
    },
    {
      "narration": "[awe] The absolute undisputed king of gateway anime.",
      "location": "Shiganshina walled district",
      "image_prompt": "Eren Yeager from Attack on Titan, a dark-haired boy with fierce green eyes, stands atop the wall in a green hooded cloak, reference character on the cobbles far below looking up in awe, low-angle wide shot",
      "image_prompt_alt": "high-angle shot past the shoulder of a dark-haired boy with fierce green eyes, lean build, messy shoulder-length hair, a brown leather strap harness over a white shirt, in a green hooded cloak atop the wall, reference character in awe on the cobbles below"
    },
    {
      "narration": "[calm] Pick one of these five today, hit play, and enjoy your new favorite addiction.",
      "location": "cozy apartment living room",
      "image_prompt": "reference character settles into the teal velvet couch with a contented smile, a bright orange blanket over his knees, the television showing a towering stone wall under blue sky, medium-wide shot",
      "image_prompt_alt": "over-the-shoulder shot from behind reference character wrapped in a bright orange blanket on the teal couch, shoulders relaxed, the television showing a towering stone wall under blue sky"
    }
  ],
  "music_prompt": "Warm, lightly adventurous instrumental bed around eighty-five BPM. Soft felt piano, gently plucked koto, low sustained strings and brushed snare. Flat consistent energy with no build, no swells, no drops. Sits far in the background under a spoken narrator with the mid range left clear. Purely instrumental with no vocals of any kind. Understated rather than comedic."
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
