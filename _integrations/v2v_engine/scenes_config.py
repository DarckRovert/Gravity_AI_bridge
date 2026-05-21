"""
Configuracion de escenas para V2V Be-Anything Engine.

Cada escena define:
  - face_prompt:    Descripcion del personaje/criatura a generar (cuerpo completo)
  - face_negative:  Negative prompt para la transformacion
  - bg_prompt:      Prompt para generar el fondo de la escena
  - bg_negative:    Negative prompt para el fondo
  - bg_color:       Color BGR de fallback si la generacion falla
"""

SCENES: dict[str, dict] = {

    # ─── HUMANOS / ESTILOS ────────────────────────────────────────────────────
    "cyberpunk_commander": {
        "name": "Comandante Cyberpunk",
        "face_prompt": "a cyberpunk space commander, glowing visor, neon tattoos, sci-fi armor, detailed, dramatic rim lighting, photorealistic",
        "face_negative": "cartoon, blurry, low quality, deformed, extra limbs",
        "bg_prompt": "futuristic spaceship command bridge, holographic displays, space stars, neon blue purple lights, no people, cinematic 4k",
        "bg_negative": "person, face, hands, body, cartoon, blurry, simple",
        "bg_color": (40, 5, 10),
    },
    "mujer": {
        "name": "Mujer Elegante",
        "face_prompt": "a beautiful elegant woman, feminine features, soft smooth skin, long flowing hair, gentle makeup, soft studio lighting, photorealistic portrait",
        "face_negative": "man, male, masculine, cartoon, blurry, low quality, deformed, rough skin, beard, stubble",
        "bg_prompt": "luxurious elegant boudoir interior, velvet curtains, soft warm sunlight, vanity mirror, no people",
        "bg_negative": "person, face, hands, body, dark, scary, sci-fi, blurry",
        "bg_color": (200, 220, 240),
    },
    "anime": {
        "name": "Personaje Anime",
        "face_prompt": "anime character full body, cel shaded illustration, studio ghibli art style, large expressive eyes, colorful outfit, soft dramatic lighting",
        "face_negative": "realistic, photo, blurry, low quality, deformed, 3d, western cartoon",
        "bg_prompt": "anime background painting, magical forest academy, cherry blossom trees, soft pastel sunset, ghibli style, no characters",
        "bg_negative": "person, face, hands, body, realistic, photo, blurry",
        "bg_color": (230, 200, 180),
    },
    "watercolor": {
        "name": "Acuarela",
        "face_prompt": "beautiful flowing watercolor painting of a person, vibrant splashes of color, artistic brushstrokes, dreamlike, impressionist",
        "face_negative": "photo, realistic, 3d, sharp edges, digital, blurry",
        "bg_prompt": "abstract watercolor painting, dreamy landscape, vibrant paint splashes, wet on wet technique, artistic, no people",
        "bg_negative": "person, face, hands, body, photo, realistic, 3d",
        "bg_color": (250, 240, 230),
    },
    "claymation": {
        "name": "Claymation",
        "face_prompt": "claymation style character, stop motion animation, plasticine texture, cute miniature, warm studio lighting, handmade look",
        "face_negative": "realistic, photo, 2d, anime, blurry, smooth, digital",
        "bg_prompt": "miniature diorama room, modeling clay, plasticine furniture, stop motion animation set, colorful, no people",
        "bg_negative": "person, face, hands, body, realistic, photo, 2d, anime",
        "bg_color": (150, 150, 180),
    },
    "samurai": {
        "name": "Guerrero Samurai",
        "face_prompt": "samurai warrior in traditional kabuto helmet, fierce stoic expression, face paint, dramatic sidelight, full armor, feudal japan",
        "face_negative": "modern, sci-fi, cartoon, blurry, low quality",
        "bg_prompt": "feudal japanese temple courtyard at dusk, cherry blossom petals, stone lanterns, misty mountains, no people, cinematic",
        "bg_negative": "person, face, hands, body, modern, sci-fi, cartoon",
        "bg_color": (20, 30, 50),
    },
    "pirate_captain": {
        "name": "Capitan Pirata",
        "face_prompt": "rugged pirate captain, tricorn hat, eye patch, weathered skin, gold earring, full body, dramatic warm lighting",
        "face_negative": "modern, sci-fi, cartoon, blurry, low quality",
        "bg_prompt": "wooden tall ship captain quarters, maps compass, treasure chest, cannon ports, stormy ocean, dramatic lantern lighting, no people",
        "bg_negative": "person, face, hands, body, modern, sci-fi, cartoon",
        "bg_color": (20, 40, 80),
    },

    # ─── FANTASÍA / MAGIA ─────────────────────────────────────────────────────
    "zombie": {
        "name": "Zombie Apocalipsis",
        "face_prompt": "zombie creature, decaying skin, pale grey face, dried blood, sunken eyes, horror, dramatic lighting",
        "face_negative": "cartoon, anime, blurry, low quality, colorful, alive",
        "bg_prompt": "post-apocalyptic ruined city at night, burning vehicles, crumbling buildings, smoke ash, red orange sky, no people",
        "bg_negative": "person, face, hands, body, cartoon, anime, colorful",
        "bg_color": (10, 20, 5),
    },
    "dark_mage": {
        "name": "Brujo Oscuro",
        "face_prompt": "powerful dark warlock, mystical glowing rune markings on face, staff raised, crackling purple magic energy, dramatic backlight, full robes",
        "face_negative": "cartoon, blurry, low quality, deformed, sci-fi",
        "bg_prompt": "dark enchanted stone circle, ancient forest at night, glowing magical runes, swirling purple green energy, fog, no people",
        "bg_negative": "person, face, hands, body, cartoon, blurry, modern",
        "bg_color": (30, 0, 40),
    },
    "dragon": {
        "name": "Dragon Humanoide",
        "face_prompt": "anthropomorphic dragon humanoid, scaly reptilian skin, horns, glowing dragon eyes, fierce expression, wings folded, detailed scales",
        "face_negative": "human, cartoon, blurry, low quality, deformed",
        "bg_prompt": "dragon lair with gold treasure mountains, lava pools, dramatic volcanic lighting, smoke and embers, no people",
        "bg_negative": "person, face, hands, body, cartoon, blurry",
        "bg_color": (5, 20, 60),
    },
    "medieval_king": {
        "name": "Rey Medieval",
        "face_prompt": "noble medieval king, ornate golden crown, royal robes fur trim, authoritative expression, dramatic window light",
        "face_negative": "modern, sci-fi, cartoon, blurry, low quality",
        "bg_prompt": "grand medieval castle great hall, stone arches, stained glass windows sunlight beams, royal banners, no people",
        "bg_negative": "person, face, hands, body, modern, sci-fi, cartoon",
        "bg_color": (15, 20, 40),
    },

    # ─── SCI-FI / ROBOTS ─────────────────────────────────────────────────────
    "robot_mecha": {
        "name": "Cyborg Mecha",
        "face_prompt": "futuristic cyborg full body, polished metal face plates, glowing cyan eyes, mechanical joints, circuit patterns, sci-fi armor",
        "face_negative": "cartoon, blurry, low quality, deformed, organic, soft",
        "bg_prompt": "futuristic megacity at night, massive mecha robots silhouette, neon lights rain reflections, cyberpunk dystopia, no people",
        "bg_negative": "person, face, hands, body, cartoon, blurry, daytime",
        "bg_color": (30, 5, 5),
    },
    "space_alien": {
        "name": "Alien Espacial",
        "face_prompt": "humanoid alien full body, iridescent skin with bioluminescent patterns, large dark eyes, elongated skull, alien clothing",
        "face_negative": "human, cartoon, blurry, low quality, deformed, earth",
        "bg_prompt": "alien planet surface, two moons in colorful nebula sky, crystalline rock formations glowing purple, exotic flora, no people",
        "bg_negative": "person, face, hands, body, cartoon, blurry, earth-like",
        "bg_color": (60, 10, 30),
    },
    "underwater": {
        "name": "Explorador Submarino",
        "face_prompt": "deep sea explorer full body, diving suit with HUD display, bioluminescent markings, dramatic underwater caustic lighting",
        "face_negative": "cartoon, blurry, low quality, deformed, dry, land",
        "bg_prompt": "deep ocean, bioluminescent coral reef, exotic colorful fish, sunlight caustic beams, mysterious dark depth, no people",
        "bg_negative": "person, face, hands, body, cartoon, blurry, land, sky",
        "bg_color": (80, 40, 0),
    },

    # ─── ANIMALES / FURRY ─────────────────────────────────────────────────────
    "bear": {
        "name": "Oso Pardo",
        "face_prompt": "anthropomorphic brown bear standing upright, thick fur, bear face with human posture, detailed realistic fur texture, warm forest lighting",
        "face_negative": "human face, cartoon, anime, blurry, low quality, deformed",
        "bg_prompt": "lush forest clearing at golden hour, ancient trees, wildflowers, misty mountains background, no people, cinematic",
        "bg_negative": "person, face, hands, body, cartoon, blurry, city",
        "bg_color": (20, 60, 30),
    },
    "dog": {
        "name": "Perro Animado",
        "face_prompt": "anthropomorphic golden retriever dog, standing upright, friendly expression, detailed fur, dog face human posture, warm lighting",
        "face_negative": "human face, cartoon, anime, blurry, low quality, deformed, cat",
        "bg_prompt": "cozy living room with fireplace, warm golden light, dog toys, fluffy carpet, no people, bokeh",
        "bg_negative": "person, face, hands, body, cartoon, blurry",
        "bg_color": (100, 150, 200),
    },
    "cat_person": {
        "name": "Persona Gato",
        "face_prompt": "anthropomorphic cat person full body, tabby fur pattern, pointed ears, bright amber cat eyes, gentle expression, nekopara style",
        "face_negative": "cartoon, blurry, low quality, deformed, dog, wolf, human",
        "bg_prompt": "cozy japanese neko cafe, warm golden hour, soft cushions, potted plants, bookshelves, bokeh, no people",
        "bg_negative": "person, face, hands, body, blurry, dark, outdoors",
        "bg_color": (120, 160, 200),
    },
    "horse": {
        "name": "Centauro",
        "face_prompt": "centaur creature, half human half horse, muscular upper body warrior, equine lower body, dramatic fantasy lighting, mythological",
        "face_negative": "cartoon, anime, blurry, low quality, deformed, full human",
        "bg_prompt": "open greek mythological landscape, marble columns ruins, dramatic sky, clouds, sunbeams, no people, epic fantasy",
        "bg_negative": "person, face, hands, body, cartoon, anime, blurry, modern",
        "bg_color": (40, 80, 120),
    },
    "wolf": {
        "name": "Hombre Lobo",
        "face_prompt": "werewolf creature, muscular humanoid wolf, grey fur, piercing yellow eyes, fangs, dramatic horror lighting, gothic atmosphere",
        "face_negative": "cartoon, anime, blurry, low quality, cute, friendly, tame",
        "bg_prompt": "dark gothic forest at full moon, foggy atmosphere, ancient gnarled trees, moonlight beams, no people, horror cinematic",
        "bg_negative": "person, face, hands, body, cartoon, anime, blurry, daylight",
        "bg_color": (5, 5, 15),
    },
    "fox": {
        "name": "Zorro Kitsune",
        "face_prompt": "anthropomorphic kitsune fox spirit, elegant orange fur with white markings, nine tails visible, japanese mythology, detailed fur, ethereal glow",
        "face_negative": "cartoon, blurry, low quality, deformed, western style",
        "bg_prompt": "japanese shrine at cherry blossom season, torii gates, magical fireflies, moonlit night, ancient trees, no people",
        "bg_negative": "person, face, hands, body, blurry, modern, city",
        "bg_color": (30, 60, 120),
    },

    # ─── CRIATURAS EXTREMAS ───────────────────────────────────────────────────
    "amorphous": {
        "name": "Figura Amorfa",
        "face_prompt": "abstract amorphous entity, shifting liquid form, iridescent void creature, multiple eyes, tendrils of light, cosmic horror beauty, non-euclidean",
        "face_negative": "human, realistic, photo, blurry, low quality, simple",
        "bg_prompt": "cosmic void with swirling galaxies, abstract dimensions, impossible geometry, liquid light, no people",
        "bg_negative": "person, face, hands, body, normal, realistic, blurry",
        "bg_color": (0, 0, 30),
    },
    "demon": {
        "name": "Demonio Oscuro",
        "face_prompt": "powerful demon creature, dark red skin, curved horns, glowing infernal eyes, wings spread, gothic armor, dramatic hellfire lighting",
        "face_negative": "cute, cartoon, anime, blurry, low quality, friendly",
        "bg_prompt": "hellscape environment, rivers of lava, burning ruins, dramatic red orange sky, dark stone citadel, no people, epic scale",
        "bg_negative": "person, face, hands, body, cartoon, anime, blurry, heaven",
        "bg_color": (0, 0, 50),
    },
    "slime": {
        "name": "Criatura Slime",
        "face_prompt": "translucent slime creature with humanoid shape, glowing bioluminescent core, gelatinous texture, floating particles inside, soft ambient lighting",
        "face_negative": "solid, opaque, human, cartoon, blurry, low quality",
        "bg_prompt": "fantasy underground cave, glowing crystals, bioluminescent plants, magical underground lake, no people",
        "bg_negative": "person, face, hands, body, blurry, normal, outdoor",
        "bg_color": (40, 100, 40),
    },
    "skeleton": {
        "name": "Esqueleto Viviente",
        "face_prompt": "animated skeleton warrior, ancient bones with magical runes glowing blue, empty eye sockets with soul fire, tattered cloak, undead",
        "face_negative": "flesh, skin, muscle, cartoon, blurry, low quality, alive",
        "bg_prompt": "haunted graveyard at midnight, fog rolling over tombstones, dead twisted trees, full moon, no people",
        "bg_negative": "person, face, hands, body, cartoon, blurry, daylight, colorful",
        "bg_color": (5, 10, 5),
    },
}


def get_scene(preset_name: str) -> dict:
    """Retorna la config de escena por nombre (case-insensitive, partial match).
    Fallback a cyberpunk_commander si no hay match."""
    if not preset_name:
        return SCENES["cyberpunk_commander"]

    p = preset_name.lower().strip().replace(" ", "_")

    # Match exacto
    if p in SCENES:
        return SCENES[p]

    # Match parcial en key
    for key, scene in SCENES.items():
        if p in key or key in p:
            return SCENES[key]

    # Match parcial en nombre legible
    for key, scene in SCENES.items():
        if p in scene["name"].lower():
            return scene

    # Match en tokens del key
    for key, scene in SCENES.items():
        tokens = key.split("_")
        if any(p == tok for tok in tokens):
            return scene

    # Ultimo recurso: no hay fallback silencioso, log y retorna default
    import logging
    logging.warning(f"Preset '{preset_name}' no encontrado. Usando cyberpunk_commander.")
    return SCENES["cyberpunk_commander"]


def list_scenes() -> list[dict]:
    """Retorna lista de escenas con su key y nombre para el panel de control."""
    return [{"key": k, "name": v["name"]} for k, v in SCENES.items()]
