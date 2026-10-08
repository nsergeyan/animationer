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
  "topic": "roman-empire-explained",
  "format": "explainer",
  "plan": {
    "spine_question": "How did a small mud village build an empire that shaped the modern world, and why did it fall?",
    "deflations": [
      {
        "assumed": "The Roman Empire fell completely in 476 AD.",
        "actual": "Only the Western half collapsed in 476 AD, while the Eastern half survived for another thousand years as the Byzantine Empire.",
        "who_decided": "Modern historians created the term Byzantine, but citizens always called themselves Romans.",
        "build_beat": "Standard history books claim the Roman Empire ended right there.",
        "drop_beat": "The Eastern half survived and lasted one thousand years!"
      }
    ],
    "specifics": [
      {
        "fact": "Rome built over 50,000 miles of paved stone roads across its territories.",
        "source": "Oxford Classical Dictionary",
        "beat": "To move troops fast, engineers built fifty thousand MILES of roads."
      },
      {
        "fact": "Julius Caesar received 23 stab wounds during his assassination in 44 BC.",
        "source": "Suetonius, Life of Julius Caesar",
        "beat": "Twenty three separate times..."
      }
    ],
    "facts_to_check": [
      {
        "claim": "Suetonius reports Caligula was said to plan making his horse Incitatus consul.",
        "source": "Suetonius, Lives of the Twelve Caesars"
      }
    ],
    "locations": [
      {"name": "Tiber hut village", "visual_anchor": ""},
      {"name": "legion march route", "visual_anchor": ""},
      {"name": "Senate chamber", "visual_anchor": ""},
      {"name": "Pax Romana city", "visual_anchor": ""},
      {"name": "imperial throne room", "visual_anchor": ""},
      {"name": "Constantinople", "visual_anchor": ""},
      {"name": "sacked Rome", "visual_anchor": ""},
      {"name": "modern capital city", "visual_anchor": ""}
    ],
    "setting_anchor": ""
  },
  "beats": [
    {
      "location": "Tiber hut village",
      "narration": "[curious] How did a small mud village build a massive ancient empire?",
      "image_prompt": "reference character crouches curiously beside one tiny brown mud hut casting a long red shadow shaped like a domed city, wide shot",
      "image_prompt_alt": "reference character stands at frame right, head tilted curiously, above one small brown thatched mud hut whose long red shadow forms a sprawling domed city, high-angle shot"
    },
    {
      "location": "Tiber hut village",
      "narration": "Rome began as a tiny cluster of huts in central Italy.",
      "image_prompt": "three doodle villagers in rough brown tunics build round huts with yellow thatch while reference character watches attentively from the edge, long shot",
      "image_prompt_alt": "reference character leans at the far left edge, mildly interested, as three doodle villagers in rough brown tunics stack yellow thatch onto small round mud huts, medium-wide shot"
    },
    {
      "location": "Tiber hut village",
      "narration": "[understated] Nobody expected them to dominate.",
      "image_prompt": "reference character shrugs, unimpressed, beside one tiny brown mud hut dwarfed by one towering grey stone fortress at frame left, medium shot",
      "image_prompt_alt": "reference character stands between one small brown mud hut and one towering grey stone fortress, glancing down at the hut with a deadpan shrug, low-angle wide shot"
    },
    {
      "location": "Tiber hut village",
      "narration": "But they loved fighting.",
      "image_prompt": "two doodle villagers in brown tunics clash wooden sticks behind round red shields while reference character watches from the foreground, mildly surprised, medium shot",
      "image_prompt_alt": "reference character sits at the lower right edge, eyebrows raised, as two doodle villagers in brown tunics swing wooden sticks at each other behind round red shields, wide side angle"
    },
    {
      "location": "Tiber hut village",
      "narration": "And they never surrendered.",
      "image_prompt": "one doodle villager in a dented bronze helmet stands firm behind one red shield, a speech bubble reading \"NEVER\", reference character nodding slowly, close-up",
      "image_prompt_alt": "reference character stands at frame left, nodding slowly, beside one stubborn doodle villager in a dented bronze helmet planted firmly behind one red shield with his chin raised, low-angle medium shot"
    },
    {
      "location": "Tiber hut village",
      "narration": "[deadpan] If an enemy destroyed one army, Rome simply sent another.",
      "image_prompt": "two fresh doodle soldiers in red tunics march straight past one flattened red-tunic soldier, reference character deadpan at the edge, wide shot",
      "image_prompt_alt": "reference character stands in the foreground right, unimpressed, as two fresh doodle soldiers in red tunics step over one flattened red-tunic soldier and keep marching, low-angle shot"
    },
    {
      "location": "legion march route",
      "narration": "Soon they defeated Carthage and controlled the whole Mediterranean sea.",
      "image_prompt": "one Roman warship with a red sail rams one sinking purple-sailed Carthaginian ship while reference character watches from the lower frame edge, wide shot",
      "image_prompt_alt": "reference character stands at the left edge, eyebrows raised, as one long oared warship with a red sail splits one smaller purple-sailed ship in half, side-on long shot"
    },
    {
      "location": "legion march route",
      "narration": "Then they kept expanding.",
      "image_prompt": "reference character watches, mildly concerned, as one red ink stain spreads outward across one giant outline map at his feet, overhead shot",
      "image_prompt_alt": "reference character stands at the corner of one giant outline map, staring down with mild concern, as one red ink stain creeps steadily toward his shoes, low three-quarter view"
    },
    {
      "location": "legion march route",
      "narration": "Roman legions marched thousands of miles.",
      "image_prompt": "three doodle legionaries in red cloaks and plumed bronze helmets march in step while reference character trudges tiredly behind them, side-on long shot",
      "image_prompt_alt": "reference character, seen from behind showing the back of his plain white head with no face, trails three doodle legionaries in red cloaks and plumed bronze helmets marching toward frame right, rear wide shot"
    },
    {
      "location": "legion march route",
      "narration": "[flatly] To move troops fast, engineers built fifty thousand MILES of roads.",
      "image_prompt": "two doodle engineers in brown tunics lay grey paving stones on one road unrolling past the frame edge, reference character looking tired, medium-wide shot",
      "image_prompt_alt": "reference character sits wearily at frame left as two doodle engineers in brown tunics fit square grey paving stones onto one road stretching far past the frame edge, high-angle shot"
    },
    {
      "location": "legion march route",
      "narration": "These stone highways connected distant towns and made trade very simple.",
      "image_prompt": "one doodle merchant pulls one wooden cart of red clay jars along a grey stone road while reference character nods, mildly impressed, medium shot",
      "image_prompt_alt": "reference character stands at frame left, mildly impressed, as one doodle merchant in a brown tunic leads one wooden cart stacked with red clay jars along a straight grey stone road, three-quarter view"
    },
    {
      "location": "Senate chamber",
      "narration": "At first, Rome was a republic.",
      "image_prompt": "three doodle senators in white togas with red borders debate beneath a small banner reading \"SPQR\", reference character watching attentively at frame right, medium-wide shot",
      "image_prompt_alt": "reference character sits at the lower left edge, attentive, as three doodle senators in white togas with red borders argue and gesture beneath one long red banner, low-angle shot"
    },
    {
      "location": "Senate chamber",
      "narration": "Citizens elected their main leaders.",
      "image_prompt": "two doodle citizens in brown tunics drop small white pebbles into one tall red clay urn while reference character looks curious, close-up",
      "image_prompt_alt": "reference character crouches beside one tall red clay urn, curious, as two doodle citizens in brown tunics drop small white pebbles into its narrow mouth, low side angle"
    },
    {
      "location": "Senate chamber",
      "narration": "[sarcastic] Rich politicians hated sharing power.",
      "image_prompt": "one plump doodle senator in a red-bordered white toga clutches one bulging gold cloth sack away from reference character, who looks unimpressed, medium shot",
      "image_prompt_alt": "reference character stands at frame right, arms folded, unimpressed, as one plump doodle senator in a red-bordered white toga hugs one bulging gold cloth sack and turns his back, wide shot"
    },
    {
      "location": "Senate chamber",
      "narration": "Successful military generals became more popular than elected government officials.",
      "image_prompt": "two cheering doodle soldiers lift one doodle general in a red cloak onto their shoulders while reference character looks skeptical at the edge, medium-wide shot",
      "image_prompt_alt": "reference character leans at frame left with a skeptical squint as one doodle general in a red cloak rides high on the shoulders of two cheering doodle soldiers, low-angle shot"
    },
    {
      "location": "Senate chamber",
      "narration": "General Julius Caesar marched his army into Rome and took power.",
      "image_prompt": "Julius Caesar in a white toga with a green laurel wreath leads two red-cloaked legionaries forward while reference character steps aside warily, low-angle medium shot",
      "image_prompt_alt": "reference character steps aside at frame left, wary, as a tall lean balding man with short grey hair, clean-shaven, in a white toga with a green laurel wreath leads two red-cloaked legionaries straight toward the viewer, frontal wide shot"
    },
    {
      "location": "Senate chamber",
      "narration": "Senators felt threatened by him.",
      "image_prompt": "three doodle senators in red-bordered white togas whisper nervously behind Julius Caesar in a white toga with a green laurel wreath, reference character eavesdropping skeptically, medium shot",
      "image_prompt_alt": "reference character leans in at the right edge, skeptical, as three doodle senators in red-bordered white togas huddle and whisper behind a tall lean balding man with short grey hair, clean-shaven, in a white toga with a green laurel wreath, wide side angle"
    },
    {
      "location": "Senate chamber",
      "narration": "[sighs] So they stabbed him.",
      "image_prompt": "three doodle senators in red-bordered white togas close in on Julius Caesar in a white toga with a green laurel wreath with small daggers, reference character wincing at the edge, wide shot",
      "image_prompt_alt": "reference character covers his eyes at the far right edge as three doodle senators in red-bordered white togas close in with small daggers around a tall lean balding man with short grey hair, clean-shaven, in a white toga with a green laurel wreath, high-angle shot"
    },
    {
      "location": "Senate chamber",
      "narration": "Twenty three separate times...",
      "image_prompt": "reference character stares, weary and wincing, at one torn white toga full of small holes beside one fallen green laurel wreath, close-up",
      "image_prompt_alt": "reference character crouches at frame left with a pained, tired expression beside one crumpled white toga riddled with small tears and one dropped green laurel wreath, overhead shot"
    },
    {
      "location": "Senate chamber",
      "narration": "Killing Caesar did not restore freedom to the broken republic.",
      "image_prompt": "reference character sighs, disappointed, beside one white marble bench cracked clean in half with one torn red banner draped across it, medium shot",
      "image_prompt_alt": "reference character sits slumped on the end of one white marble bench split down the middle, one torn red banner hanging beside him, low wide angle"
    },
    {
      "location": "Senate chamber",
      "narration": "A brutal civil war broke out across the Roman lands.",
      "image_prompt": "one doodle soldier in a red cloak slams shields with one doodle soldier in a blue cloak while reference character ducks at the edge, wide shot",
      "image_prompt_alt": "reference character crouches low at the right edge, alarmed, as one doodle soldier in a red cloak and one in a blue cloak crash round shields together, side angle medium shot"
    },
    {
      "location": "Senate chamber",
      "narration": "[understated] Caesar's adopted son won.",
      "image_prompt": "Augustus in a white toga and a purple cloak with a gold wreath stands calmly over one dropped blue shield, reference character mildly surprised nearby, medium shot",
      "image_prompt_alt": "reference character at frame left, eyebrows raised, watches a slim young man with short curly fair hair, clean-shaven, in a white toga and a purple cloak with a gold wreath stand calmly over one dropped blue shield, low-angle wide shot"
    },
    {
      "location": "Senate chamber",
      "narration": "His name was Augustus.",
      "image_prompt": "Augustus in a white toga and a purple cloak with a gold wreath poses proudly beside a small sign reading \"AUGUSTUS\", reference character looking curious, medium two-shot",
      "image_prompt_alt": "reference character stands close at frame right, curious, studying a slim young man with short curly fair hair, clean-shaven, in a white toga and a purple cloak with a gold wreath who poses proudly beside one small wooden sign, close two-shot"
    },
    {
      "location": "Pax Romana city",
      "narration": "Augustus became the very first official emperor of Rome.",
      "image_prompt": "Augustus in a white toga and a purple cloak with a gold wreath raises one hand to a cheering doodle crowd, reference character skeptical at the edge, low-angle shot",
      "image_prompt_alt": "reference character stands in the foreground left with arms folded, skeptical, as a slim young man with short curly fair hair, clean-shaven, in a white toga and a purple cloak with a gold wreath raises one hand to a cheering doodle crowd, medium-wide shot"
    },
    {
      "location": "Pax Romana city",
      "narration": "He launched a famous two-hundred-year golden age called Pax Romana.",
      "image_prompt": "Augustus in a white toga and a purple cloak with a gold wreath unrolls one long gold banner reading \"PAX ROMANA\" while reference character looks quietly interested, wide shot",
      "image_prompt_alt": "reference character sits at frame right, quietly interested, as a slim young man with short curly fair hair, clean-shaven, in a white toga and a purple cloak with a gold wreath unrolls one long gold banner across the frame, high-angle shot"
    },
    {
      "location": "Pax Romana city",
      "narration": "[thoughtful] Trade flourished everywhere.",
      "image_prompt": "two doodle merchants in brown tunics swap one red clay jar for one bolt of purple cloth while reference character looks interested, medium two-shot",
      "image_prompt_alt": "reference character leans in at the left edge, interested, as two doodle merchants in brown tunics hand over one red clay jar and one rolled bolt of purple cloth, close side angle"
    },
    {
      "location": "Pax Romana city",
      "narration": "Cities expanded very quickly.",
      "image_prompt": "reference character looks up, impressed, as one white marble temple and one red-roofed apartment block sprout tall around him, low-angle wide shot",
      "image_prompt_alt": "reference character stands small between one rising white marble temple and one fast-growing red-roofed apartment block, turning his head in surprise, high-angle long shot"
    },
    {
      "location": "Pax Romana city",
      "narration": "Life seemed quite good.",
      "image_prompt": "reference character lounges contentedly on one white marble bench while one smiling doodle Roman offers him one bowl of purple grapes, medium shot",
      "image_prompt_alt": "reference character sits back on one white marble bench, one arm along its edge, content, beside one smiling doodle Roman in a tunic holding out one bowl of purple grapes, three-quarter view"
    },
    {
      "location": "Pax Romana city",
      "narration": "Massive stone arenas were constructed to entertain millions of citizens.",
      "image_prompt": "reference character stands tiny beside the towering curved wall of the Colosseum in pale yellow stone, looking up in awe, low-angle long shot",
      "image_prompt_alt": "reference character stands at the lower right corner, awed, gazing up at one towering round arena of pale yellow stone ringed with stacked rows of arches, wide eye-level shot"
    },
    {
      "location": "Pax Romana city",
      "narration": "Gladiators fought wild animals and each other inside the Colosseum.",
      "image_prompt": "one doodle gladiator in a bronze helmet faces one roaring orange lion while reference character peeks from the frame edge, alarmed, medium-wide shot",
      "image_prompt_alt": "reference character crouches in the foreground left, alarmed, as one doodle gladiator with a bronze helmet and round shield squares off against one roaring orange lion, low side angle"
    },
    {
      "location": "Pax Romana city",
      "narration": "[deadpan] Free games kept people calm.",
      "image_prompt": "three cheerful doodle spectators in brown tunics sit beneath a small sign reading \"FREE SHOWS\", reference character seated beside them looking unimpressed, medium shot",
      "image_prompt_alt": "reference character sits at the end of a row of three cheerful doodle spectators in brown tunics, arms folded and unimpressed, all of them facing one yellow stone arena arch, side angle"
    },
    {
      "location": "Pax Romana city",
      "narration": "Free bread kept them full.",
      "image_prompt": "reference character stares deadpan at a real photo cutout of a round carbonized Roman bread loaf, roughly pasted onto the drawing, close-up",
      "image_prompt_alt": "reference character stands at frame right with a deadpan look as one plump doodle citizen in a brown tunic chews happily beside one round brown bread loaf scored into wedges, medium shot"
    },
    {
      "location": "Pax Romana city",
      "narration": "Giant arch bridges called aqueducts brought clean mountain water inside.",
      "image_prompt": "reference character looks impressed beneath one towering stone aqueduct of stacked arches carrying one blue stream of water, low-angle long shot",
      "image_prompt_alt": "reference character stands at frame left, impressed, beside one tall grey stone bridge of stacked arches with one blue channel of water running along its top, wide side view"
    },
    {
      "location": "Pax Romana city",
      "narration": "Wealthy Romans enjoyed warm public bathhouses and luxury indoor toilets.",
      "image_prompt": "reference character stares, puzzled, at a real photo cutout of a long marble Roman toilet bench with keyhole openings, roughly pasted onto the drawing, wide shot",
      "image_prompt_alt": "reference character stands at frame left, puzzled, beside one long white marble bench with a row of keyhole-shaped openings while one plump doodle Roman relaxes in one blue steaming pool, wide side angle"
    },
    {
      "location": "Pax Romana city",
      "narration": "[clears throat] Well... wealthy citizens did.",
      "image_prompt": "reference character raises an eyebrow beside one plump doodle Roman in a purple-trimmed toga relaxing in one blue pool under a small sign reading \"RICH ONLY\", medium shot",
      "image_prompt_alt": "reference character stands at the right edge with one raised eyebrow as one plump doodle Roman with a purple-trimmed toga folded beside him lounges in one blue marble pool, high-angle shot"
    },
    {
      "location": "Pax Romana city",
      "narration": "Millions of enslaved workers worked.",
      "image_prompt": "three doodle enslaved workers in plain grey tunics haul one heavy white marble block on ropes while reference character watches soberly from the edge, wide shot",
      "image_prompt_alt": "reference character stands quietly in the foreground right, somber, as three doodle workers in plain grey tunics strain to drag one heavy white marble block on thick ropes, low side angle"
    },
    {
      "location": "Pax Romana city",
      "narration": "They had zero rights.",
      "image_prompt": "reference character stands soberly beside one tired doodle worker in a grey tunic sitting hunched, one iron chain loose at his feet, close-up",
      "image_prompt_alt": "reference character crouches at frame left with a sorrowful expression near one exhausted doodle worker in a plain grey tunic hugging his knees, one heavy iron chain coiled beside him, medium shot"
    },
    {
      "location": "imperial throne room",
      "narration": "[flatly] Governing fifty million people created gigantic administrative and logistical challenges.",
      "image_prompt": "reference character looks tired beside one towering heap of paper scrolls toppling over one tiny brown wooden desk, medium shot",
      "image_prompt_alt": "reference character sits slumped at one tiny brown wooden desk, exhausted, as one enormous leaning pile of rolled paper scrolls looms over him, low-angle shot"
    },
    {
      "location": "imperial throne room",
      "narration": "The border spanned from rainy Britain all the way to Egypt.",
      "image_prompt": "reference character stretches his arms wide across one giant outline map with one grey rain cloud at its top and one yellow pyramid at its far end, overhead shot",
      "image_prompt_alt": "reference character lies flat across one huge outline map, arms outstretched and still falling short, one grey rain cloud at one corner and one yellow pyramid at the other, high-angle wide shot"
    },
    {
      "location": "imperial throne room",
      "narration": "From Atlantic Spain to Syria.",
      "image_prompt": "reference character walks wearily along one long outline map stretching past both frame edges, one blue wave curling at its start, wide shot",
      "image_prompt_alt": "reference character trudges across one endless outline map toward frame right, shoulders sagging, one small blue wave splashing at the map's left end, low side view"
    },
    {
      "location": "imperial throne room",
      "narration": "It was too huge.",
      "image_prompt": "reference character strains, mildly annoyed, to fold one enormous red-bordered map billowing far beyond the frame edges, low-angle shot",
      "image_prompt_alt": "reference character stands buried to the waist in folds of one gigantic red-bordered map spilling past every frame edge, looking fed up, high-angle medium shot"
    },
    {
      "location": "imperial throne room",
      "narration": "[thoughtful] Then incompetent leaders started making terrible decisions for the country.",
      "image_prompt": "one lazy doodle emperor in a purple cloak flips one gold coin to decide while reference character watches, skeptical, medium two-shot",
      "image_prompt_alt": "reference character stands at the right edge with a doubtful frown as one slouching doodle emperor in a purple cloak tosses one gold coin into the air, low three-quarter view"
    },
    {
      "location": "imperial throne room",
      "narration": "Caligula reportedly planned to make his horse a consul.",
      "image_prompt": "Caligula with a sneering grin and a purple cloak drapes one red-bordered white toga over one white horse while reference character stares, incredulous, medium shot",
      "image_prompt_alt": "reference character stands at frame left, jaw dropped in disbelief, as a thin pale young man with short dark hair, clean-shaven, with a sneering grin and a purple cloak drapes one red-bordered white toga over one white horse, wide side angle"
    },
    {
      "location": "imperial throne room",
      "narration": "[sarcastic] True political genius right there.",
      "image_prompt": "one white horse in a red-bordered white toga sits beside reference character behind a small plaque reading \"CONSUL\", reference character deadpan, medium two-shot",
      "image_prompt_alt": "reference character sits on one white marble bench, flatly annoyed, shoulder to shoulder with one white horse wearing a red-bordered white toga, both facing the viewer, frontal close two-shot"
    },
    {
      "location": "imperial throne room",
      "narration": "Rumors said Nero sang while Rome burned.",
      "image_prompt": "Nero, in a purple robe, plucking a small golden lyre beside one row of red-roofed houses in orange flames, reference character horrified at the edge, wide shot",
      "image_prompt_alt": "reference character stands in the foreground right, horrified, as a stocky man with curly reddish hair and a short neck beard, in a purple robe, plucking a small golden lyre ignores one row of red-roofed houses in orange flames, low-angle shot"
    },
    {
      "location": "imperial throne room",
      "narration": "Greed infected the leadership.",
      "image_prompt": "one doodle emperor in a purple cloak hugs one open wooden chest heaped with gold coins while reference character looks disgusted at the edge, medium shot",
      "image_prompt_alt": "reference character stands at frame left, lip curled in disgust, as one grinning doodle emperor in a purple cloak sprawls over one open wooden chest piled with gold coins, high-angle shot"
    },
    {
      "location": "imperial throne room",
      "narration": "Greedy army generals fought continuous battles against each other for power.",
      "image_prompt": "two doodle generals in red and blue plumed helmets tug one gold crown between them while reference character looks exasperated nearby, medium-wide shot",
      "image_prompt_alt": "reference character stands between two doodle generals, one in a red plumed helmet and one in a blue plumed helmet, rolling his eyes as they yank one gold crown back and forth, low-angle shot"
    },
    {
      "location": "imperial throne room",
      "narration": "In one single year, Rome had four different emperors.",
      "image_prompt": "reference character stares in disbelief at four gold crowns toppling in a row like dominoes, close-up",
      "image_prompt_alt": "reference character crouches at frame right, wide-eyed, watching four gold crowns tip over one after another in a neat line across the frame, low side angle"
    },
    {
      "location": "imperial throne room",
      "narration": "[light chuckle] Politics became complete chaos.",
      "image_prompt": "three doodle men in purple cloaks scramble over one gold throne, pulling each other off, while reference character smirks from the side, wide shot",
      "image_prompt_alt": "reference character sits at the lower left edge with an amused smirk as three doodle men in purple cloaks climb over and shove each other off one gold throne, high-angle medium shot"
    },
    {
      "location": "imperial throne room",
      "narration": "Unpaid soldiers demanded money.",
      "image_prompt": "two doodle legionaries in red cloaks hold out empty palms with a speech bubble reading \"PAY US\", reference character shrugging awkwardly, medium shot",
      "image_prompt_alt": "reference character shrugs awkwardly at frame right as two frowning doodle legionaries in red cloaks lean toward him with empty open palms, low-angle close two-shot"
    },
    {
      "location": "imperial throne room",
      "narration": "High taxes crushed farmers.",
      "image_prompt": "one thin doodle farmer in a brown tunic bends double beneath one enormous red cloth sack, reference character wincing sympathetically beside him, medium shot",
      "image_prompt_alt": "reference character stands at frame left, wincing, as one thin doodle farmer in a brown tunic staggers under one gigantic red cloth sack many times his size, wide side angle"
    },
    {
      "location": "imperial throne room",
      "narration": "Emperor Diocletian realized that one single man could not rule everything.",
      "image_prompt": "Diocletian in a stiff purple robe with a gold jeweled crown sits overwhelmed beneath one towering stack of scrolls, reference character nodding in agreement, medium shot",
      "image_prompt_alt": "reference character stands at the right edge, nodding knowingly, as a heavy-set older man with a short grey beard and cropped hair, in a stiff purple robe with a gold jeweled crown sits buried under one towering stack of scrolls, high-angle shot"
    },
    {
      "location": "imperial throne room",
      "narration": "[understated] So he split the entire empire into two distinct halves.",
      "image_prompt": "Diocletian in a stiff purple robe with a gold jeweled crown tears one giant outline map cleanly in half while reference character watches, mildly surprised, wide shot",
      "image_prompt_alt": "reference character stands in the foreground left, eyebrows raised, as a heavy-set older man with a short grey beard and cropped hair, in a stiff purple robe with a gold jeweled crown rips one huge outline map down the middle, low-angle medium shot"
    },
    {
      "location": "imperial throne room",
      "narration": "Western region and Eastern region.",
      "image_prompt": "reference character stands between two torn map halves, one painted red and one painted blue, looking from one to the other, wide shot",
      "image_prompt_alt": "reference character sits cross-legged in the gap between one red map half at frame left and one blue map half at frame right, glancing curiously at each, overhead shot"
    },
    {
      "location": "imperial throne room",
      "narration": "Each side got leaders.",
      "image_prompt": "two doodle emperors in purple cloaks, one with a red sash and one with a blue sash, sit back to back beside reference character, bored, medium shot",
      "image_prompt_alt": "reference character sits wedged between two doodle emperors in purple cloaks who face opposite directions, one wearing a red sash and the other a blue sash, looking bored, frontal wide shot"
    },
    {
      "location": "Constantinople",
      "narration": "Emperor Constantine relocated the main capital city to wealthy Byzantium.",
      "image_prompt": "Constantine with a square jaw and a gold diadem drives one oxcart heaped with white marble columns eastward while reference character trudges behind, tired, wide side shot",
      "image_prompt_alt": "reference character walks wearily at the front right edge as a broad muscular man with short brown hair, clean-shaven, in a red military cloak, with a square jaw and a gold diadem drives one oxcart heaped with white marble columns toward him, frontal long shot"
    },
    {
      "location": "Constantinople",
      "narration": "He renamed this magnificent eastern trade hub to Constantinople.",
      "image_prompt": "Constantine with a square jaw and a gold diadem hangs one big sign reading \"CONSTANTINOPLE\" above one gold-domed building, reference character unimpressed, medium shot",
      "image_prompt_alt": "reference character stands at the lower left edge, unimpressed, as a broad muscular man with short brown hair, clean-shaven, in a red military cloak, with a square jaw and a gold diadem proudly hangs one large wooden sign over one gold-domed building, low-angle wide shot"
    },
    {
      "location": "Constantinople",
      "narration": "[curious] Constantine legalized Christianity as well.",
      "image_prompt": "Constantine with a square jaw and a gold diadem raises one round shield painted with a red chi-rho symbol while reference character looks curious, low-angle medium shot",
      "image_prompt_alt": "reference character leans in from frame right, curious, as a broad muscular man with short brown hair, clean-shaven, in a red military cloak, with a square jaw and a gold diadem lifts one round shield bearing a red chi-rho symbol, eye-level wide shot"
    },
    {
      "location": "Constantinople",
      "narration": "Religion transformed European history.",
      "image_prompt": "reference character looks thoughtful beneath one towering domed church topped with one gold cross, low-angle long shot",
      "image_prompt_alt": "reference character sits on one stone step at frame right, chin resting on his knee, thoughtful, beside one huge domed church with one gold cross at its peak, wide side view"
    },
    {
      "location": "sacked Rome",
      "narration": "Meanwhile problems worsened west.",
      "image_prompt": "reference character frowns at one red map half crumbling at its edges like dry paper, close-up",
      "image_prompt_alt": "reference character kneels beside one red map half, worried, as large flakes break off its edges and drift away, high-angle medium shot"
    },
    {
      "location": "sacked Rome",
      "narration": "[flatly] Migrating Germanic tribes pushed across weak borders seeking safety and land.",
      "image_prompt": "three doodle travelers in brown fur cloaks step over one thin broken wooden fence while reference character watches neutrally from the edge, wide shot",
      "image_prompt_alt": "reference character stands in the foreground left, attentive, as three doodle travelers in brown fur cloaks with bundles on their backs climb across one sagging broken wooden fence, low side angle"
    },
    {
      "location": "sacked Rome",
      "narration": "The Western Roman government went BROKE and could not pay soldiers.",
      "image_prompt": "reference character offers a real photo cutout of a single worn silver Roman coin, roughly pasted onto the drawing, to one frowning red-cloaked legionary, close-up",
      "image_prompt_alt": "reference character at frame right, embarrassed, holds out one tiny silver coin toward one frowning doodle legionary in a red cloak with his arms folded, medium shot"
    },
    {
      "location": "sacked Rome",
      "narration": "Outer defenses collapsed completely.",
      "image_prompt": "one long wooden palisade topples like dominoes past reference character, who stands resigned at frame left, wide shot",
      "image_prompt_alt": "reference character sits at the lower right corner with a resigned sigh as one long line of sharpened brown wooden stakes falls over plank by plank toward him, low-angle shot"
    },
    {
      "location": "sacked Rome",
      "narration": "Invaders looted Rome itself.",
      "image_prompt": "two doodle raiders in brown fur cloaks carry off one gold statue while reference character stares, stunned, from the frame edge, medium-wide shot",
      "image_prompt_alt": "reference character stands in the foreground right, frozen in shock, as two doodle raiders in brown fur cloaks haul one heavy gold statue away toward frame left, high-angle shot"
    },
    {
      "location": "sacked Rome",
      "narration": "[deadpan] In four hundred seventy-six, the last western emperor resigned.",
      "image_prompt": "one small doodle boy emperor in an oversized purple cloak sets down one gold crown and walks away, reference character deadpan, medium shot",
      "image_prompt_alt": "reference character stands at frame left, expressionless, beside one abandoned gold crown as one small doodle boy in a trailing oversized purple cloak shuffles off toward frame right, wide side view"
    },
    {
      "location": "sacked Rome",
      "narration": "Standard history books claim the Roman Empire ended right there.",
      "image_prompt": "reference character looks skeptical beside one thick red book open to a page reading \"THE END\", medium close-up",
      "image_prompt_alt": "reference character leans over one thick open red book at frame left, one eyebrow raised in doubt, low three-quarter view"
    },
    {
      "location": "sacked Rome",
      "narration": "[sighs] But that is FALSE.",
      "image_prompt": "reference character rolls his eyes and shoves one thick red book off the frame edge, medium shot",
      "image_prompt_alt": "reference character turns away with an exasperated sigh, pushing one thick red book aside with his foot, wide shot from slightly above"
    },
    {
      "location": "Constantinople",
      "narration": "The Eastern half survived.",
      "image_prompt": "reference character looks surprised as one gold-domed city rises whole from one blue map half, wide shot",
      "image_prompt_alt": "reference character steps back at frame left, eyes wide, as one intact gold-domed city stands tall on one blue map half, low-angle medium shot"
    },
    {
      "location": "Constantinople",
      "narration": "It lasted one thousand years!",
      "image_prompt": "one gold-domed city stands unshaken beside one giant hourglass whose sand has fully run out, reference character amazed, wide shot",
      "image_prompt_alt": "reference character looks up in amazement from the lower right corner at one towering hourglass emptied to the last grain beside one sturdy gold-domed city, low-angle long shot"
    },
    {
      "location": "Constantinople",
      "narration": "Modern historians call that surviving rich region the Byzantine Empire.",
      "image_prompt": "two doodle professors in tweed jackets and round glasses stick a tag reading \"BYZANTINE\" onto one gold-domed city, reference character doubtful, medium-wide shot",
      "image_prompt_alt": "reference character stands at frame left, doubtful, as two doodle professors in tweed jackets and round glasses press one large paper tag onto one gold-domed city, high-angle shot"
    },
    {
      "location": "Constantinople",
      "narration": "Yet citizens living there called themselves proud Romans the whole time.",
      "image_prompt": "two doodle citizens in blue robes peel the paper tag off one gold-domed city, thumping their chests proudly, reference character amused, medium shot",
      "image_prompt_alt": "reference character grins at the right edge as two doodle citizens in blue robes tear one paper tag from one gold-domed city and puff out their chests, low side angle"
    },
    {
      "location": "modern capital city",
      "narration": "[thoughtful] Why does this matter?",
      "image_prompt": "reference character sits thoughtfully on one white marble column stump, chin on hand, medium close-up",
      "image_prompt_alt": "reference character sits on one short white marble column stump at frame left, gazing upward in thought, wide shot from slightly below"
    },
    {
      "location": "modern capital city",
      "narration": "Western laws mirror Roman laws.",
      "image_prompt": "one doodle judge in a black robe and one doodle magistrate in a white toga hold up matching bronze tablets, reference character interested between them, medium shot",
      "image_prompt_alt": "reference character stands at frame right, interested, watching one doodle judge in a black robe and one doodle magistrate in a white toga compare two identical bronze tablets face to face, wide side view"
    },
    {
      "location": "modern capital city",
      "narration": "Languages like French, Spanish, and Italian directly evolved from Latin.",
      "image_prompt": "reference character looks up, fascinated, at one big green oak tree with a trunk sign reading \"LATIN\" splitting into three thick branches, low-angle shot",
      "image_prompt_alt": "reference character sits against the base of one big green oak tree at frame left, fascinated, as its single trunk divides into three thick spreading branches, wide eye-level shot"
    },
    {
      "location": "modern capital city",
      "narration": "[calm] Even modern government buildings across the globe copy ancient Roman architecture.",
      "image_prompt": "reference character compares one white columned government building with a gold dome to one small marble temple of the same shape, impressed, wide shot",
      "image_prompt_alt": "reference character stands between one small white marble temple and one large columned government building with a gold dome, glancing back and forth, impressed, low-angle long shot"
    },
    {
      "location": "modern capital city",
      "narration": "Rome fell long ago.",
      "image_prompt": "reference character sits calmly beside one fallen white marble column with one green vine curling over it, medium shot",
      "image_prompt_alt": "reference character rests one arm on one cracked white marble column lying on its side, one green vine winding along it, calm, high-angle wide shot"
    },
    {
      "location": "modern capital city",
      "narration": "[content] Its world still remains.",
      "image_prompt": "reference character smiles contentedly beside one tall white marble column topped by one green laurel wreath, wide shot",
      "image_prompt_alt": "reference character leans back against one tall standing white marble column at frame right, a contented smile on his face, one green laurel wreath resting on its top, low-angle medium shot"
    }
  ],
  "music_prompt": "Sparse instrumental bed with a steady, stately mood, around seventy-five BPM. Soft low brass, a gently plucked harp, warm muted frame drum, and low sustained cellos. Flat consistent energy with no build, no swells, no drops. Sits far in the background under a spoken narrator with the mid range left clear. Purely instrumental with no vocals of any kind. Understated rather than comedic."
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
#   SHORT beat   3-6 words   ~1.5s   a consequence, a reaction, one hard image
#   LONG beat    8-12 words  ~3.4s   the information, the number, the turn
#
# Half and half averages ~7 words a beat, ~2.4s per image: about 75 beats for
# a 3 minute video. Was 4-8 / 10-15 (~9 words, ~3.0s, 60 beats) until
# 2026-10-07, when the channel moved to one picture per short sentence.
#
# The MIX is the rule, not the shortness. Uniformly short beats are not a
# faster video, they are a faster metronome - and a metronome was the original
# complaint. So the checks below police the ratio and the runs, and only flag
# an individual beat when it is too long to sit under one still image.
RHYTHM_FORMATS = {"explainer"}
SHORT_MAX_WORDS = 6       # at or under this, a beat counts as SHORT
LONG_MAX_WORDS = 12       # over this, the image freezes while narration runs
MIN_WORDS = 3             # under this it does not register as a beat at all
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
    # "photo cutout" is the one sanctioned photo phrase (see the photo checks
    # below), so it is taken out before looking for stray photo words.
    cutout = _re.compile(r"\bphoto cutout\b", _re.I)
    risky = [(i, sorted(set(w.lower() for w in render_words.findall(
                 cutout.sub(" ", b["image_prompt"])))))
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
              if cutout.search(b["image_prompt"])]
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
              if _re.search(r'"[^"]+"', b["image_prompt"])]
    if len(labels) > n / 4:
        print(f"[warn] {len(labels)} beats with quoted labels in {n} "
              f"(max ~{n // 4}, 1 in 4)")
        print("       labels only where the words ARE the joke")

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
