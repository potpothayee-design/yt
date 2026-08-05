"""Curated early-childhood knowledge base.

This is the "research" layer of the pipeline. Each topic entry captures:
learning objectives, vocabulary with kid-friendly definitions, interesting
facts, teaching points, and visual scene seeds that downstream steps turn
into scripts, storyboards and illustrations.

Content here is original, written for this project in a style consistent
with common early-learning curricula (letter/number recognition, basic
science facts). For unknown topics the pipeline falls back to a generic
structured template engine, and when an external LLM provider is enabled the
knowledge base seeds its prompts with learning objectives and constraints.

To extend coverage, add entries to ``TOPIC_KNOWLEDGE`` below.
"""

from __future__ import annotations

from typing import Any

# Each scene seed: {"focus": item key, "object": drawable object,
#                   "text": on-screen text, "fact": narration-ready fact}
TOPIC_KNOWLEDGE: dict[str, dict[str, Any]] = {
    "abcs": {
        "aliases": ["abc", "alphabet", "letters", "abc's", "abcs"],
        "display_name": "The Alphabet",
        "learning_objectives": [
            "Recognize uppercase letters A to Z",
            "Match each letter to its beginning sound",
            "Connect letters with familiar everyday words",
        ],
        "vocabulary": [
            {"word": "letter", "definition": "A shape we use to write words"},
            {"word": "sound", "definition": "What a letter says when we speak it"},
            {"word": "alphabet", "definition": "All the letters from A to Z, in order"},
        ],
        "facts": [
            "The English alphabet has 26 letters — 5 vowels and 21 consonants.",
            "The word 'alphabet' comes from the first two Greek letters, alpha and beta.",
            "Every word you will ever read is built from these same 26 letters!",
        ],
        "teaching_points": [
            "Pair every letter with its most common sound.",
            "Anchor letters to concrete objects children already know.",
            "Encourage children to say the sound out loud with the narrator.",
        ],
        "scene_seeds": [
            {"focus": "A", "object": "apple", "text": "A is for Apple",
             "fact": "A makes the sound 'ah' — like the first bite of a crunchy apple!"},
            {"focus": "B", "object": "ball", "text": "B is for Ball",
             "fact": "B goes 'buh' — bouncy like a ball hopping down the street."},
            {"focus": "C", "object": "cat", "text": "C is for Cat",
             "fact": "C says 'kuh' — like a curious cat tiptoeing through the grass."},
            {"focus": "D", "object": "dog", "text": "D is for Dog",
             "fact": "D goes 'duh' — dogs dig, dash, and dreams start with D too!"},
            {"focus": "S", "object": "sun", "text": "S is for Sun",
             "fact": "S sounds like a tiny snake — sssun, sssmile, sssing!"},
            {"focus": "M", "object": "moon", "text": "M is for Moon",
             "fact": "M hums 'mmm' — the same sound you make for yummy moon-shaped cookies."},
        ],
        "quiz": "Can you find something in your room that starts with the letter B?",
    },
    "animals": {
        "aliases": ["animal", "zoo animals", "wild animals", "pets", "safari"],
        "display_name": "Amazing Animals",
        "learning_objectives": [
            "Name common animals and where they live",
            "Describe one special ability of each animal",
            "Understand that animals need food, water and care",
        ],
        "vocabulary": [
            {"word": "habitat", "definition": "The home where an animal lives"},
            {"word": "mammal", "definition": "An animal with fur whose babies drink milk"},
            {"word": "camouflage", "definition": "Colors that help an animal hide"},
        ],
        "facts": [
            "An octopus has three hearts and blue blood.",
            "Giraffes only sleep about 30 minutes a day — in tiny naps!",
            "A group of flamingos is called a 'flamboyance'.",
        ],
        "teaching_points": [
            "Connect each animal to its habitat and one 'superpower'.",
            "Use sounds and movement words to keep energy high.",
            "Model kindness: animals are living friends to protect.",
        ],
        "scene_seeds": [
            {"focus": "Lion", "object": "lion", "text": "Lion — King of the Savanna",
             "fact": "A lion's roar can be heard 8 kilometers away — that's 80 football fields!"},
            {"focus": "Elephant", "object": "elephant", "text": "Elephant — Gentle Giant",
             "fact": "Elephants use their trunks like a hand, a nose, AND a shower hose."},
            {"focus": "Penguin", "object": "penguin", "text": "Penguin — Waddle Champion",
             "fact": "Penguins can't fly, but they 'fly' underwater as fast as a car in the city."},
            {"focus": "Frog", "object": "frog", "text": "Frog — Super Jumper",
             "fact": "Some frogs can jump 20 times their own body length — like you jumping over a house!"},
            {"focus": "Octopus", "object": "octopus", "text": "Octopus — 8 Clever Arms",
             "fact": "An octopus can taste with its arms and squeeze through any gap bigger than its beak."},
            {"focus": "Giraffe", "object": "giraffe", "text": "Giraffe — Tallest of All",
             "fact": "A giraffe's neck is taller than most doors, yet it has the same number of neck bones as you!"},
        ],
        "quiz": "Which animal would YOU visit first at the zoo, and what sound does it make?",
    },
    "colors": {
        "aliases": ["color", "colours", "rainbow"],
        "display_name": "Colors All Around",
        "learning_objectives": [
            "Name the primary and rainbow colors",
            "Match colors to familiar objects",
            "Discover that mixing colors makes new colors",
        ],
        "vocabulary": [
            {"word": "primary colors", "definition": "Red, yellow and blue — colors that make all others"},
            {"word": "rainbow", "definition": "Sunlight split into stripes of color after rain"},
            {"word": "shade", "definition": "How light or dark a color is"},
        ],
        "facts": [
            "Mixing blue and yellow paint makes green!",
            "A rainbow is actually a full circle — from the ground we just see half.",
            "Flamingos are pink because of the shrimp they eat.",
        ],
        "teaching_points": [
            "Show one color at a time with a strong real-world anchor.",
            "Turn color spotting into a game children can play anywhere.",
            "Introduce simple color mixing as 'color magic'.",
        ],
        "scene_seeds": [
            {"focus": "Red", "object": "apple", "text": "RED like an apple",
             "fact": "Red is the color of apples, fire trucks and brave little ladybugs!"},
            {"focus": "Blue", "object": "fish", "text": "BLUE like the ocean",
             "fact": "Blue is the sky on a sunny day and the deep ocean where whales sing."},
            {"focus": "Yellow", "object": "sun", "text": "YELLOW like sunshine",
             "fact": "Yellow is sunshine, bananas, and bushy baby chicks — the happiest color!"},
            {"focus": "Green", "object": "frog", "text": "GREEN like leaves",
             "fact": "Green is grass, leaves and jumping frogs — the color of growing things."},
            {"focus": "Purple", "object": "grapes", "text": "PURPLE like grapes",
             "fact": "Mix red and blue and — ta-da! — purple appears, like grapes and violets."},
            {"focus": "Orange", "object": "orange", "text": "ORANGE like an orange",
             "fact": "Orange shares its name with the fruit — the only color that does!"},
        ],
        "quiz": "What color do YOU get if you mix yellow and blue? Try it with paint!",
    },
    "numbers": {
        "aliases": ["number", "counting", "123", "123s", "math"],
        "display_name": "Counting Numbers",
        "learning_objectives": [
            "Count aloud from 1 to 10",
            "Match numbers with real quantities",
            "Recognize that counting works for anything, anywhere",
        ],
        "vocabulary": [
            {"word": "number", "definition": "A word or symbol that tells how many"},
            {"word": "count", "definition": "To say numbers in order, one by one"},
            {"word": "zero", "definition": "The number that means 'none at all'"},
        ],
        "facts": [
            "Zero was invented in India more than 1,500 years ago.",
            "You can count in any language — numbers mean the same everywhere!",
            "It would take about 31 years to count aloud to one billion.",
        ],
        "teaching_points": [
            "Pair each number with countable objects on screen.",
            "Use rhythm and repetition — counting is musical.",
            "Encourage children to count along with the narrator.",
        ],
        "scene_seeds": [
            {"focus": "1", "object": "sun", "text": "ONE sun in the sky",
             "fact": "Number 1! We have exactly ONE sun warming our whole planet."},
            {"focus": "2", "object": "ball", "text": "TWO bouncing balls",
             "fact": "Number 2 — two eyes, two ears, two hands to clap with!"},
            {"focus": "3", "object": "balloon", "text": "THREE balloons",
             "fact": "Number 3 — a triangle has 3 sides, and so does a slice of pizza!"},
            {"focus": "4", "object": "car", "text": "FOUR wheels",
             "fact": "Number 4 — cars roll on 4 wheels, and dogs run on 4 legs!"},
            {"focus": "5", "object": "star", "text": "FIVE shiny stars",
             "fact": "Number 5 — count the fingers on one hand: 1, 2, 3, 4, 5!"},
            {"focus": "10", "object": "balloon", "text": "TEN balloons!",
             "fact": "Number 10 — all your fingers together make 10. Wiggle them all!"},
        ],
        "quiz": "How many windows can YOU count in your home? Count them out loud!",
    },
    "solar system": {
        "aliases": ["solar system", "space", "planets", "the planets"],
        "display_name": "Our Solar System",
        "learning_objectives": [
            "Name the eight planets in order from the Sun",
            "Describe one special feature of each planet",
            "Understand that Earth is our home planet",
        ],
        "vocabulary": [
            {"word": "planet", "definition": "A big round world that travels around a star"},
            {"word": "orbit", "definition": "The path a planet takes around the Sun"},
            {"word": "asteroid", "definition": "A space rock smaller than a planet"},
        ],
        "facts": [
            "A day on Venus is longer than its whole year!",
            "Saturn's rings are made of billions of pieces of ice and rock.",
            "Jupiter is so big that 1,300 Earths could fit inside it.",
        ],
        "teaching_points": [
            "Travel outward from the Sun — order matters.",
            "Give each planet one memorable 'identity card'.",
            "End at Earth to make space feel connected to home.",
        ],
        "scene_seeds": [
            {"focus": "Sun", "object": "sun", "text": "The Sun — our star",
             "fact": "The Sun is a star! One million Earths could fit inside it."},
            {"focus": "Mercury", "object": "planet_gray", "text": "Mercury — the speedster",
             "fact": "Mercury sprints around the Sun in just 88 days — fastest planet ever!"},
            {"focus": "Mars", "object": "planet_mars", "text": "Mars — the red planet",
             "fact": "Mars is red because its dust is rusty — it has the tallest volcano we know!"},
            {"focus": "Jupiter", "object": "planet_jupiter", "text": "Jupiter — the giant",
             "fact": "Jupiter's Great Red Spot is a storm bigger than Earth, raging for 300 years."},
            {"focus": "Saturn", "object": "planet_saturn", "text": "Saturn — the ringed beauty",
             "fact": "Saturn is so light it would float in a giant bathtub — if you had one!"},
            {"focus": "Earth", "object": "planet_earth", "text": "Earth — our home",
             "fact": "Earth is the only planet we know with oceans, forests, and YOU!"},
        ],
        "quiz": "If you could visit any planet for one day, which would you choose — and why?",
    },
    "dinosaurs": {
        "aliases": ["dinosaur", "dino", "dinos", "prehistoric"],
        "display_name": "Dinosaur World",
        "learning_objectives": [
            "Name well-known dinosaurs and what they ate",
            "Compare dinosaur sizes with familiar objects",
            "Know that scientists learn about dinosaurs from fossils",
        ],
        "vocabulary": [
            {"word": "fossil", "definition": "Ancient bones turned to stone, found in the ground"},
            {"word": "herbivore", "definition": "An animal that eats only plants"},
            {"word": "carnivore", "definition": "An animal that eats other animals"},
        ],
        "facts": [
            "Birds are living dinosaurs — chickens are T-rex cousins!",
            "Some dinosaurs were as small as a house cat.",
            "Dinosaur fossils have been found on every continent, even Antarctica.",
        ],
        "teaching_points": [
            "Compare sizes to things kids know — buses, houses, chickens.",
            "Group by diet: plant-eaters vs meat-eaters.",
            "Celebrate scientists as detectives solving Earth's oldest mystery.",
        ],
        "scene_seeds": [
            {"focus": "T-Rex", "object": "trex", "text": "T-Rex — the mighty hunter",
             "fact": "T-Rex had banana-sized teeth, but arms too short to clap!"},
            {"focus": "Triceratops", "object": "triceratops", "text": "Triceratops — three horns",
             "fact": "Triceratops means 'three-horned face' — perfect for pushing through forests."},
            {"focus": "Brachiosaurus", "object": "brachiosaurus", "text": "Brachiosaurus — tall as a house",
             "fact": "Brachiosaurus could peek over a 4-story building while eating leaves!"},
            {"focus": "Stegosaurus", "object": "stegosaurus", "text": "Stegosaurus — plate back",
             "fact": "Stegosaurus wore roof-tile plates on its back and a spiky tail called a 'thagomizer'."},
            {"focus": "Velociraptor", "object": "raptor", "text": "Velociraptor — fast & feathered",
             "fact": "Real Velociraptors were turkey-sized and covered in feathers!"},
            {"focus": "Fossils", "object": "fossil", "text": "Fossils — clues in stone",
             "fact": "Fossils are dinosaur bones that turned to rock over millions of years."},
        ],
        "quiz": "Which dinosaur would you rather meet — the giant gentle Brachiosaurus or the speedy Velociraptor?",
    },
    "fruits": {
        "aliases": ["fruit", "healthy food", "food", "snacks"],
        "display_name": "Fantastic Fruits",
        "learning_objectives": [
            "Name common fruits and their colors",
            "Understand that fruit helps our bodies grow strong",
            "Describe tastes: sweet, sour, juicy, crunchy",
        ],
        "vocabulary": [
            {"word": "vitamin", "definition": "Tiny helpers in food that keep us healthy"},
            {"word": "juicy", "definition": "Full of sweet water — like a ripe peach"},
            {"word": "seed", "definition": "The tiny 'baby plant' hiding inside fruit"},
        ],
        "facts": [
            "Strawberries wear their seeds on the OUTSIDE — about 200 each!",
            "Bananas are berries, but strawberries are not — science is funny!",
            "Apples float because they are one quarter air.",
        ],
        "teaching_points": [
            "Pair fruits with colors and simple taste words.",
            "Frame healthy eating as a superpower, not a chore.",
            "Encourage trying one new fruit this week.",
        ],
        "scene_seeds": [
            {"focus": "Apple", "object": "apple", "text": "Apple — crunchy & red",
             "fact": "Apples float in water because one quarter of them is air!"},
            {"focus": "Banana", "object": "banana", "text": "Banana — nature's snack bar",
             "fact": "Bananas come in their own yellow wrapper — no plastic needed!"},
            {"focus": "Strawberry", "object": "strawberry", "text": "Strawberry — seed polka dots",
             "fact": "A strawberry's seeds are on the outside — about 200 tiny polka dots!"},
            {"focus": "Watermelon", "object": "watermelon", "text": "Watermelon — 92% water",
             "fact": "Watermelon is 92% water — a snack and a drink in one!"},
            {"focus": "Grapes", "object": "grapes", "text": "Grapes — tiny purple planets",
             "fact": "Grapes grow in bunches, like a family holding hands on the vine."},
            {"focus": "Orange", "object": "orange", "text": "Orange — vitamin C hero",
             "fact": "Oranges are color and fruit in one word — full of vitamin C superpower!"},
        ],
        "quiz": "Which fruit will YOU try on your next snack adventure?",
    },
    "vehicles": {
        "aliases": ["vehicle", "cars", "trucks", "transportation", "transport"],
        "display_name": "Vehicles That Go!",
        "learning_objectives": [
            "Name vehicles that travel on land, water and in the air",
            "Match vehicles with their jobs in the community",
            "Learn simple safety rules around vehicles",
        ],
        "vocabulary": [
            {"word": "vehicle", "definition": "A machine that carries people or things"},
            {"word": "engine", "definition": "The part that makes a vehicle go"},
            {"word": "runway", "definition": "The long road where airplanes take off"},
        ],
        "facts": [
            "A fire truck's ladder can stretch as high as a 10-story building.",
            "The first airplanes flew for just 12 seconds.",
            "A bullet train can go faster than a diving falcon!",
        ],
        "teaching_points": [
            "Sort vehicles by WHERE they travel: road, water, sky, space.",
            "Highlight community helpers: ambulance, fire truck, school bus.",
            "Always end with a safety message (seat belts, look both ways).",
        ],
        "scene_seeds": [
            {"focus": "Car", "object": "car", "text": "Car — vroom vroom!",
             "fact": "Cars take us to school, parks and grandma's house — seat belt first!"},
            {"focus": "Fire Truck", "object": "firetruck", "text": "Fire Truck — hero on wheels",
             "fact": "Fire trucks are red so everyone can see them coming to help, fast!"},
            {"focus": "Airplane", "object": "plane", "text": "Airplane — high in the sky",
             "fact": "Airplanes fly above the clouds — the first flight lasted only 12 seconds!"},
            {"focus": "Boat", "object": "boat", "text": "Boat — floating explorer",
             "fact": "Boats float because their shape pushes water aside — that's buoyancy!"},
            {"focus": "Train", "object": "train", "text": "Train — choo choo!",
             "fact": "Trains run on rails, so one engine can pull 100 heavy cars!"},
            {"focus": "Rocket", "object": "rocket", "text": "Rocket — blast off!",
             "fact": "Rockets go so fast — 40,000 km/h — that they escape Earth's gravity!"},
        ],
        "quiz": "If you could drive any vehicle for a day, which would it be?",
    },
}


def _norm(topic: str) -> str:
    return " ".join(topic.lower().replace("_", " ").split())


def lookup_topic(topic: str) -> dict[str, Any] | None:
    """Find curated knowledge for a topic (alias-tolerant)."""
    key = _norm(topic)
    for name, entry in TOPIC_KNOWLEDGE.items():
        if key == name or key in entry.get("aliases", []):
            return {"key": name, **entry}
    # substring match, e.g. "counting numbers 1-10"
    for name, entry in TOPIC_KNOWLEDGE.items():
        if name in key or any(a in key for a in entry.get("aliases", [])):
            return {"key": name, **entry}
    return None


def generic_knowledge(topic: str) -> dict[str, Any]:
    """Structured fallback for topics outside the curated base.

    The script engine combines this skeleton with the requested age band to
    produce an original educational arc (introduction → exploration →
    examples → fun facts → quiz → recap) for ANY topic.
    """
    display = topic.strip().title()
    return {
        "key": _norm(topic),
        "display_name": display,
        "learning_objectives": [
            f"Understand what {display} is and why it matters",
            f"Learn new words connected to {display}",
            f"See real examples of {display} in everyday life",
        ],
        "vocabulary": [
            {"word": display.lower(), "definition": "The amazing topic we are exploring today"},
            {"word": "discover", "definition": "To find out something new"},
            {"word": "explore", "definition": "To look around and learn"},
        ],
        "facts": [
            f"Every expert on {display} started by asking one small question.",
            f"There is always something new to discover about {display}.",
            f"Learning about {display} makes your brain grow stronger — like exercise for your mind!",
        ],
        "teaching_points": [
            "Start from what children already know, then stretch gently.",
            "Use concrete examples before abstract explanations.",
            "End with an invitation to keep exploring in the real world.",
        ],
        "scene_seeds": [
            {"focus": "Discover", "object": "star", "text": f"What is {display}?",
             "fact": f"Today we're going on an adventure to discover {display} together!"},
            {"focus": "Explore", "object": "magnifier", "text": "Let's explore!",
             "fact": f"When we explore {display}, we ask big questions and find clever answers."},
            {"focus": "Examples", "object": "lightbulb", "text": "Examples all around",
             "fact": f"Once you know about {display}, you'll start noticing it everywhere!"},
            {"focus": "Fun fact", "object": "lightbulb", "text": "Fun fact time!",
             "fact": ("Here's something surprising: everyone who learns about "
                      f"{display} starts exactly where you are now.")},
            {"focus": "Think", "object": "star", "text": "What do you think?",
             "fact": f"What is the most interesting thing about {display} so far?"},
            {"focus": "Hero", "object": "trophy", "text": "You're a star explorer!",
             "fact": f"You just learned so much about {display} — every question you ask makes you smarter."},
        ],
        "quiz": f"What was your favorite thing about {display} today?",
        "generic": True,
    }


def research(topic: str) -> dict[str, Any]:
    """Return a complete internal knowledge summary for the topic."""
    kb = lookup_topic(topic) or generic_knowledge(topic)
    return {
        "topic": topic,
        "display_name": kb["display_name"],
        "curated": not kb.get("generic", False),
        "learning_objectives": kb["learning_objectives"],
        "vocabulary": kb["vocabulary"],
        "facts": kb["facts"],
        "teaching_points": kb["teaching_points"],
        "scene_seeds": kb["scene_seeds"],
        "quiz": kb["quiz"],
        "summary": (
            f"{kb['display_name']}: targets {len(kb['learning_objectives'])} learning "
            f"objectives with {len(kb['vocabulary'])} key vocabulary items and "
            f"{len(kb['scene_seeds'])} visual anchors."
        ),
    }
