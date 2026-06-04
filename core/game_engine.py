import random
from typing import List, Dict, Tuple, Optional


CATEGORIES: Dict[str, List[str]] = {
    "fantasy": ["🧙 Wizard", "🧛 Vampire", "🧟 Zombie", "🧚 Fairy", "🐉 Dragon"],
    "space": ["🚀 Rocket", "🛸 UFO", "👾 Alien", "🪐 Saturn", "🌌 Galaxy"],
    "food": ["🍕 Pizza", "🍔 Burger", "🌮 Taco", "🍣 Sushi", "🎂 Cake"],
    "animals": ["🐶 Dog", "🐱 Cat", "🦊 Fox", "🐸 Frog", "🦁 Lion"],
    "sports": ["⚽ Soccer", "🏀 Basketball", "🎾 Tennis", "🏈 Football", "🥊 Boxing"],
    "music": ["🎸 Guitar", "🎹 Piano", "🥁 Drums", "🎻 Violin", "🎤 Microphone"],
    "tech": ["💻 Laptop", "📱 Smartphone", "🖥️ Desktop", "🎮 Controller", "⌚ Smartwatch"],
    "mythology": ["⚡ Zeus", "🔱 Poseidon", "🌩️ Thor", "🐍 Medusa", "🧝‍♂️ Odin"],
    "movies": ["🦇 Batman", "🕷️ Spider-Man", "🧙‍♂️ Harry Potter", "🤖 Terminator", "👽 E.T."],
    "vehicles": ["🚗 Car", "✈️ Airplane", "🚢 Ship", "🚲 Bicycle", "🚁 Helicopter"],
    "nature": ["🌳 Tree", "🌸 Flower", "🍄 Mushroom", "🌊 Wave", "🌋 Volcano"],
    "clothes": ["👕 T-Shirt", "👖 Jeans", "👗 Dress", "🧥 Coat", "👠 High Heels"],
    "emotions": ["😀 Happy", "😢 Sad", "😡 Angry", "🤩 Excited", "😴 Sleepy"],
    "professions": ["👨‍⚕️ Doctor", "👩‍🏫 Teacher", "👨‍🚒 Firefighter", "👩‍🍳 Chef", "👨‍🔬 Scientist"],
    "furniture": ["🪑 Chair", "🛏️ Bed", "📚 Bookshelf", "🛋️ Sofa", "🚪 Door"],
    "fruit": ["🍎 Apple", "🍌 Banana", "🍇 Grapes", "🍊 Orange", "🍓 Strawberry"],
    "drinks": ["☕ Coffee", "🍵 Tea", "🥤 Soda", "🍺 Beer", "🍷 Wine"],
    "body_parts": ["👀 Eyes", "👃 Nose", "👂 Ear", "🦶 Foot", "🦷 Tooth"],
    "shapes": ["🔵 Circle", "🔺 Triangle", "🟦 Square", "⭐ Star", "❤️ Heart"],
    "weather": ["☀️ Sunny", "🌧️ Rain", "❄️ Snow", "🌪️ Tornado", "🌈 Rainbow"],
    "ocean": ["🐟 Fish", "🐙 Octopus", "🦈 Shark", "🐳 Whale", "🦀 Crab"],
    "insects": ["🐝 Bee", "🐞 Ladybug", "🦋 Butterfly", "🐜 Ant", "🦗 Cricket"],
    "reptiles": ["🐍 Snake", "🦎 Lizard", "🐢 Turtle", "🐊 Crocodile", "🦖 Dinosaur"],
    "birds": ["🦅 Eagle", "🦉 Owl", "🐧 Penguin", "🦜 Parrot", "🕊️ Dove"],
    "tools": ["🔨 Hammer", "🔧 Wrench", "🪚 Saw", "🔩 Screwdriver", "⛏️ Pickaxe"],
    "holidays": ["🎄 Christmas", "🎃 Halloween", "🐣 Easter", "🎆 New Year", "🦃 Thanksgiving"],
    "astronomy": ["🌞 Sun", "🌙 Moon", "🌟 Star", "☄️ Comet", "🪐 Saturn"],

    # EXTRA CATEGORIES
    "school": ["📚 Book", "✏️ Pencil", "🖍️ Crayon", "📐 Ruler", "🎒 Backpack"],
    "office": ["🖨️ Printer", "📎 Paperclip", "📁 Folder", "🗂️ Cabinet", "🖊️ Pen"],
    "kitchen": ["🍳 Frying Pan", "🔪 Knife", "🥄 Spoon", "🍴 Fork", "🫖 Teapot"],
    "bathroom": ["🪥 Toothbrush", "🧼 Soap", "🚿 Shower", "🧻 Toilet Paper", "🪞 Mirror"],
    "bedroom": ["🛌 Bed", "🕯️ Lamp", "🪟 Window", "⏰ Alarm Clock", "🧸 Teddy Bear"],
    "farm": ["🐄 Cow", "🐖 Pig", "🐑 Sheep", "🚜 Tractor", "🌾 Wheat"],
    "jungle": ["🐒 Monkey", "🐅 Tiger", "🦜 Macaw", "🐍 Python", "🌴 Palm Tree"],
    "desert": ["🐪 Camel", "🏜️ Sand Dune", "🌵 Cactus", "🦂 Scorpion", "☀️ Heat"],
    "winter": ["⛄ Snowman", "🧤 Gloves", "🧣 Scarf", "🎿 Skis", "❄️ Ice"],
    "summer": ["🏖️ Beach", "🕶️ Sunglasses", "🍦 Ice Cream", "🏄 Surfboard", "☀️ Sun"],
    "magic": ["🪄 Wand", "📜 Spellbook", "🔮 Crystal Ball", "🧪 Potion", "✨ Sparkles"],
    "pirates": ["🏴‍☠️ Pirate", "🪙 Gold Coin", "🦜 Parrot", "⚓ Anchor", "🗺️ Treasure Map"],
    "robots": ["🤖 Android", "🦾 Robot Arm", "⚙️ Gear", "🔋 Battery", "🛰️ Drone"],
    "superheroes": ["🦸 Superman", "🛡️ Captain America", "⚡ Flash", "🕸️ Spider-Man", "🦇 Batman"],
    "villains": ["😈 Devil", "🃏 Joker", "👹 Ogre", "☠️ Skull", "👺 Goblin"],
    "gaming": ["🎮 Console", "🕹️ Joystick", "💾 Save File", "👾 Pixel Alien", "🏆 Trophy"],
    "board_games": ["♟️ Chess", "🎲 Dice", "🃏 Cards", "🧩 Puzzle", "🎯 Dart"],
    "currencies": ["💵 Dollar", "💶 Euro", "💷 Pound", "💴 Yen", "🪙 Coin"],
    "time": ["⌚ Watch", "⏳ Hourglass", "🕰️ Clock", "📅 Calendar", "🌅 Sunrise"],
    "transport": ["🚇 Metro", "🚌 Bus", "🚕 Taxi", "🚂 Train", "🛴 Scooter"],
    "construction": ["🏗️ Crane", "🧱 Brick", "🪚 Saw", "👷 Worker", "🏠 House"],
    "medical": ["💊 Pill", "🩺 Stethoscope", "🩹 Bandage", "💉 Syringe", "🧬 DNA"],
    "science": ["🔬 Microscope", "🧪 Beaker", "⚛️ Atom", "🧫 Petri Dish", "📡 Satellite"],
    "chemistry": ["🧪 Acid", "⚗️ Flask", "💨 Gas", "🔥 Reaction", "🧬 Molecule"],
    "physics": ["🧲 Magnet", "⚡ Electricity", "🌌 Gravity", "🔭 Telescope", "💥 Explosion"],
    "math": ["➕ Plus", "➗ Divide", "📏 Geometry", "📊 Graph", "🧮 Calculator"],
    "history": ["🏺 Vase", "⚔️ Sword", "👑 Crown", "🏛️ Temple", "📜 Scroll"],
    "kingdom": ["👑 King", "👸 Queen", "🏰 Castle", "⚔️ Knight", "🐎 Horse"],
    "army": ["🪖 Helmet", "🎖️ Medal", "🚁 Helicopter", "⚔️ Sword", "🛡️ Shield"],
    "police": ["🚓 Police Car", "👮 Officer", "🚨 Siren", "🔫 Pistol", "🧤 Handcuffs"],
    "fire": ["🔥 Flame", "🚒 Fire Truck", "🧯 Extinguisher", "💥 Blast", "🌋 Lava"],
    "water": ["💧 Droplet", "🌊 Ocean", "🚰 Tap", "⛲ Fountain", "🐟 Fish"],
    "earth": ["⛰️ Mountain", "🌍 Globe", "🪨 Rock", "🌱 Plant", "🏕️ Camp"],
    "air": ["🌬️ Wind", "🪂 Parachute", "🦅 Eagle", "☁️ Cloud", "🛩️ Jet"],
    "elements": ["🔥 Fire", "💧 Water", "🌪️ Air", "🪨 Earth", "⚡ Lightning"],
    "zodiac": ["♈ Aries", "♉ Taurus", "♊ Gemini", "♋ Cancer", "♌ Leo"],
    "religion": ["⛪ Church", "🕌 Mosque", "🛕 Temple", "✝️ Cross", "🕉️ Om"],
    "festival": ["🎊 Party", "🎉 Confetti", "🥳 Celebration", "🎵 Music", "💃 Dance"],
    "social_media": ["📸 Instagram", "🐦 Twitter", "▶️ YouTube", "🎵 TikTok", "💼 LinkedIn"],
    "internet": ["🌐 Website", "📡 WiFi", "💾 Server", "🖱️ Mouse", "⌨️ Keyboard"],
    "coding": ["🐍 Python", "☕ Java", "🌐 HTML", "⚙️ C++", "💻 VS Code"],
    "ai": ["🧠 Neural Net", "🤖 AI Bot", "📈 Machine Learning", "💬 Chatbot", "🔍 Data"],
    "cyberpunk": ["🌃 Neon City", "🤖 Cyborg", "💾 Chip", "🕶️ Hacker", "⚡ Neon Blade"],
    "horror": ["👻 Ghost", "🩸 Blood", "🪦 Grave", "🕷️ Spider", "🧟 Monster"],
    "fairytale": ["👸 Princess", "🐉 Dragon", "🏰 Castle", "🪄 Magic Wand", "🧚 Fairy"],
    "cartoons": ["🐭 Mickey", "🧽 SpongeBob", "🐰 Bugs Bunny", "🦆 Donald Duck", "🐱 Tom"],
    "anime": ["🍥 Naruto", "⚔️ Zoro", "🐉 Goku", "👒 Luffy", "🔥 Tanjiro"],
    "martial_arts": ["🥋 Karate", "🥊 Boxing", "🗡️ Katana", "🐉 Kung Fu", "🦶 Kick"],
    "music_genres": ["🎸 Rock", "🎤 Pop", "🎧 EDM", "🎻 Classical", "🎷 Jazz"],
    "instruments": ["🎹 Piano", "🎸 Guitar", "🥁 Drum", "🎺 Trumpet", "🎻 Violin"],
    "dance": ["💃 Salsa", "🕺 Hip Hop", "🎶 Ballet", "🔥 Breakdance", "🎵 Tango"],
    "photography": ["📷 Camera", "🎞️ Film", "🔦 Flash", "🖼️ Portrait", "🌄 Landscape"],
    "art": ["🎨 Paint", "🖌️ Brush", "🗿 Sculpture", "✏️ Sketch", "🖼️ Canvas"],
    "colors": ["🔴 Red", "🔵 Blue", "🟢 Green", "🟡 Yellow", "🟣 Purple"],
    "metals": ["🥇 Gold", "🥈 Silver", "🪙 Bronze", "⚙️ Iron", "🔩 Steel"],
    "gems": ["💎 Diamond", "🟢 Emerald", "🔴 Ruby", "🔵 Sapphire", "🟣 Amethyst"],
    "luxury": ["⌚ Rolex", "🚘 Ferrari", "💎 Diamond", "🛥️ Yacht", "🏰 Mansion"],
    "cities": ["🗼 Paris", "🗽 New York", "🎡 London", "🏯 Tokyo", "🌉 San Francisco"],
    "countries": ["🇺🇸 USA", "🇯🇵 Japan", "🇮🇳 India", "🇧🇷 Brazil", "🇫🇷 France"],
    "flags": ["🇨🇦 Canada", "🇩🇪 Germany", "🇮🇹 Italy", "🇰🇷 Korea", "🇦🇺 Australia"],
    "mountains": ["🏔️ Everest", "⛰️ Alps", "🌋 Fuji", "🏕️ Camp", "🧗 Climber"],
    "forest": ["🌲 Pine", "🦌 Deer", "🍄 Mushroom", "🦉 Owl", "🐻 Bear"],
    "islands": ["🏝️ Palm Island", "🌊 Lagoon", "⛵ Boat", "🐚 Shell", "🦜 Tropical Bird"],
    "camping": ["⛺ Tent", "🔥 Campfire", "🧭 Compass", "🥾 Boots", "🌲 Forest"],
    "adventure": ["🧗 Climbing", "🏕️ Camping", "🪂 Skydiving", "🚵 Mountain Bike", "🌋 Volcano"],
    "shopping": ["🛒 Cart", "💳 Credit Card", "🏬 Mall", "🛍️ Bag", "🏷️ Tag"],
    "money": ["💰 Cash", "🏦 Bank", "🪙 Coin", "💳 Card", "📈 Stocks"],
    "business": ["📊 Chart", "💼 Briefcase", "🏢 Office", "📞 Call", "🤝 Deal"],
    "education": ["🎓 Graduation", "📚 Library", "📝 Exam", "🏫 School", "🧠 Learning"],
    "library": ["📖 Novel", "📚 Shelf", "🪑 Reading Chair", "🕯️ Lamp", "📜 Manuscript"],
    "space_missions": ["🚀 Apollo", "🛰️ Satellite", "👨‍🚀 Astronaut", "🌕 Moon", "🪐 Orbit"],
    "dinosaurs": ["🦖 T-Rex", "🦕 Brachiosaurus", "🥚 Dino Egg", "🌋 Volcano", "🦴 Fossil"],
    "prehistoric": ["🪨 Cave", "🔥 Fire", "🦣 Mammoth", "🏹 Spear", "🦴 Bone"],
    "detective": ["🕵️ Detective", "🔎 Magnifying Glass", "📜 Clue", "🧤 Gloves", "🚔 Crime Scene"],
    "circus": ["🎪 Tent", "🤹 Juggler", "🦁 Lion", "🎭 Clown", "🎟️ Ticket"],
    "magic_school": ["🧙 Apprentice", "📖 Spellbook", "🪄 Wand", "🧪 Potion", "🏰 Academy"],
    "toys": ["🧸 Teddy", "🚂 Toy Train", "🪀 Yo-Yo", "🎲 Dice", "🪁 Kite"],
    "baby": ["🍼 Milk Bottle", "👶 Baby", "🧸 Teddy", "🚼 Stroller", "🛁 Bathtub"],
    "pets": ["🐕 Puppy", "🐈 Kitten", "🐹 Hamster", "🐠 Goldfish", "🦜 Bird"],
    "bakery": ["🥐 Croissant", "🍞 Bread", "🧁 Cupcake", "🥖 Baguette", "🍪 Cookie"],
    "breakfast": ["🥞 Pancakes", "🍳 Eggs", "🥓 Bacon", "☕ Coffee", "🍞 Toast"],
    "desserts": ["🍩 Donut", "🍰 Cake", "🍫 Chocolate", "🍨 Ice Cream", "🧁 Muffin"],
    "street_food": ["🌭 Hotdog", "🥙 Wrap", "🍜 Noodles", "🍢 Skewer", "🥟 Dumpling"],
    "weapons": ["🗡️ Sword", "🏹 Bow", "🔫 Gun", "🪓 Axe", "⚔️ Dual Blades"],
    "survival": ["🪓 Axe", "🔥 Fire", "🥫 Canned Food", "🧭 Compass", "🏕️ Tent"],
    "treasure": ["💰 Gold", "🪙 Coin", "💎 Gem", "🗺️ Map", "🏴‍☠️ Pirate Chest"],
    "underworld": ["💀 Skeleton", "🔥 Hellfire", "👹 Demon", "🪦 Tombstone", "⚰️ Coffin"],
    "aliens": ["👽 Alien", "🛸 UFO", "🧬 Mutation", "🌌 Space Portal", "🚀 Spaceship"],
    "future": ["🤖 Robot", "🚄 Hyperloop", "🛸 Hovercar", "🌐 Metaverse", "🧠 AI Brain"],
    "retro": ["📼 VHS", "☎️ Telephone", "🎞️ Cassette", "🕹️ Arcade", "📺 CRT TV"],
    "memes": ["😂 Laugh", "🗿 Moai", "🐸 Pepe", "🔥 Roast", "💀 Dead Meme"],
    "streaming": ["🎥 Stream", "🎧 Headset", "💬 Chat", "📺 Live", "🎮 Gamer"],
    "fitness": ["🏋️ Dumbbell", "🏃 Running", "🚴 Cycling", "🥗 Diet", "🧘 Yoga"],
    "yoga": ["🧘 Meditation", "🌅 Sunrise", "🕯️ Candle", "🍃 Peace", "🪷 Lotus"],
    "travel": ["🧳 Suitcase", "✈️ Flight", "🗺️ Map", "📍Location", "🏨 Hotel"],
    "hotels": ["🏨 Resort", "🛎️ Bell", "🛏️ Room", "🍽️ Buffet", "🏊 Pool"],
    "restaurants": ["🍽️ Table", "👨‍🍳 Chef", "🥘 Meal", "🍷 Wine", "🧾 Bill"],
    "wedding": ["💍 Ring", "👰 Bride", "🤵 Groom", "🎂 Cake", "💐 Bouquet"],
    "love": ["❤️ Heart", "💌 Letter", "🌹 Rose", "😘 Kiss", "💍 Ring"],
    "friendship": ["🤝 Handshake", "😊 Smile", "🎉 Party", "📸 Selfie", "💬 Chat"],
    "dreams": ["🌙 Moon", "☁️ Cloud", "✨ Stars", "🛌 Sleep", "🦄 Unicorn"]
}


MIXED_CATEGORIES: Dict[str, List[str]] = {
    "cyber_fantasy": [
        "🤖 Dragon AI",
        "⚡ Cyber Wizard",
        "🧠 Neural Mage",
        "💾 Spell Chip",
        "🐉 Hologram Beast"
    ],

    "space_animals": [
        "🐶 Astro Dog",
        "🦊 Galaxy Fox",
        "🐸 Moon Frog",
        "🦁 Solar Lion",
        "👾 Alien Cat"
    ],

    "mythic_technology": [
        "🔱 Quantum Trident",
        "⚡ Thunder Core",
        "🧠 AI Odin",
        "💻 Rune Computer",
        "🪄 Plasma Staff"
    ],

    "dream_horror": [
        "🌙 Nightmare Moon",
        "👁️ Watching Shadow",
        "🩸 Dream Eater",
        "☁️ Whisper Cloud",
        "🕷️ Sleep Spider"
    ],

    "retro_future": [
        "📼 AI VHS",
        "🕹️ Neon Arcade",
        "🤖 Pixel Android",
        "📺 Quantum TV",
        "🚀 Retro Spaceship"
    ]
}


FAKE_INTRUDERS: Dict[str, List[str]] = {

    "animals": [
        "🐺 Wolf",
        "🦝 Raccoon",
        "🐕 Wolfdog"
    ],

    "space": [
        "🚁 Helicopter",
        "✈️ Airplane",
        "🌍 Earth"
    ],

    "fantasy": [
        "🧑 Scientist",
        "👨‍🚀 Astronaut",
        "🤖 Android"
    ],

    "tech": [
        "📖 Book",
        "🪓 Axe",
        "🍎 Apple Fruit"
    ],

    "food": [
        "🧼 Soap",
        "🎈 Balloon",
        "⚽ Soccer Ball"
    ],

    "sports": [
        "🏹 Arrow",
        "🎮 Gaming",
        "🚗 Racing Car"
    ],

    "mythology": [
        "🧑 Teacher",
        "🚒 Fire Truck",
        "🛰️ Satellite"
    ]
}


NIGHTMARE_INTRUDERS: List[str] = [
    "🪞 Reflection",
    "🫥 Invisible Man",
    "♾️ Infinity",
    "🧠 Consciousness",
    "🌌 Void",
    "🕳️ Singularity",
    "⌛ Time Collapse",
    "🔮 False Memory"
]



def generate_puzzle(difficulty: int = 1,
                    theme: Optional[str] = None) -> Dict:


    if difficulty <= 1:
        num_options = 4

    elif difficulty == 2:
        num_options = 5

    elif difficulty == 3:
        num_options = 6

    else:
        num_options = 7

    use_mixed = difficulty >= 4 and random.random() < 0.60

    if use_mixed:

        if theme and theme in MIXED_CATEGORIES:
            main_cat = theme
        else:
            main_cat = random.choice(list(MIXED_CATEGORIES.keys()))

        pool = MIXED_CATEGORIES[main_cat]

    else:

        if theme and theme in CATEGORIES:
            main_cat = theme
        else:
            main_cat = random.choice(list(CATEGORIES.keys()))

        pool = CATEGORIES[main_cat]


    main_items = random.sample(
        pool,
        min(num_options - 1, len(pool))
    )

 
    if difficulty == 1:

        intruder_cat = random.choice(
            [c for c in CATEGORIES.keys() if c != main_cat]
        )

        intruder_item = random.choice(
            CATEGORIES[intruder_cat]
        )


    elif difficulty in [2, 3]:

        if main_cat in FAKE_INTRUDERS and random.random() < 0.75:

            intruder_item = random.choice(
                FAKE_INTRUDERS[main_cat]
            )

            intruder_cat = "fake_intruder"

        else:

            intruder_cat = random.choice(
                [c for c in CATEGORIES.keys() if c != main_cat]
            )

            intruder_item = random.choice(
                CATEGORIES[intruder_cat]
            )

    else:

        if random.random() < 0.50:

            intruder_item = random.choice(
                NIGHTMARE_INTRUDERS
            )

            intruder_cat = "abstract"

        else:

            available = [
                c for c in CATEGORIES.keys()
                if c != main_cat
            ]

            intruder_cat = random.choice(available)

            intruder_item = random.choice(
                CATEGORIES[intruder_cat]
            )

    options = main_items + [intruder_item]

    random.shuffle(options)

    return {
        "options": options,
        "intruder_index": options.index(intruder_item),
        "main_category": main_cat,
        "intruder_category": intruder_cat,
        "difficulty": difficulty,
        "mixed_mode": use_mixed
    }