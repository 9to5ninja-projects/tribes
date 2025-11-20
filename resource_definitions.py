"""
Resource definitions for ecosystem elements.
This defines WHAT resources exist and WHERE they come from.
Implementation of gathering/using resources comes later with tribes.
"""

class ResourceType:
    """Base resource type"""
    def __init__(self, name, category, icon):
        self.name = name
        self.category = category  # 'food', 'material', 'luxury'
        self.icon = icon  # For UI display


# Define all resource types
RESOURCES = {
    # Food resources
    'meat': ResourceType('Meat', 'food', '🥩'),
    'fish': ResourceType('Fish', 'food', '🐟'),
    'grain': ResourceType('Grain', 'food', '🌾'),
    'fruit': ResourceType('Fruit', 'food', '🍎'),
    'vegetables': ResourceType('Vegetables', 'food', '🥬'),
    
    # Material resources
    'wood': ResourceType('Wood', 'material', '🪵'),
    'stone': ResourceType('Stone', 'material', '🪨'),
    'hide': ResourceType('Hide', 'material', '🦌'),
    'fur': ResourceType('Fur', 'material', '🦊'),
    'bone': ResourceType('Bone', 'material', '🦴'),
    'fiber': ResourceType('Fiber', 'material', '🌿'),
    
    # Luxury/special resources
    'feathers': ResourceType('Feathers', 'luxury', '🪶'),
    'ivory': ResourceType('Ivory', 'luxury', '🐘'),
    'pearls': ResourceType('Pearls', 'luxury', '🦪'),
}


# Biome resource yields (what you can gather/harvest)
BIOME_RESOURCES = {
    0: {},  # Deep Ocean - requires fishing technology
    1: {'fish': 2},  # Shallow Ocean - basic fishing
    2: {'stone': 1, 'fish': 1},  # Beach
    3: {'stone': 2},  # Desert - sparse
    4: {'wood': 1, 'grain': 1, 'meat': 2},  # Savanna
    5: {'grain': 3, 'vegetables': 2, 'wood': 1},  # Grassland - fertile
    6: {'wood': 3, 'fruit': 3, 'fiber': 2},  # Tropical Rainforest - abundant
    7: {'wood': 2, 'fruit': 1, 'vegetables': 1, 'meat': 1},  # Temperate Forest
    8: {'wood': 2, 'fur': 2},  # Taiga
    9: {'fur': 1, 'meat': 1},  # Tundra
    10: {},  # Snow - barren
    11: {'stone': 3},  # Mountain - rich in stone
}


# Animal resource yields (what you get from hunting/herding)
ANIMAL_RESOURCES = {
    # Herbivores
    'deer': {'meat': 2, 'hide': 1, 'bone': 1},
    'bison': {'meat': 3, 'hide': 2, 'bone': 1},
    'caribou': {'meat': 2, 'hide': 1, 'fur': 1},
    'gazelle': {'meat': 1, 'hide': 1},
    'elephant': {'meat': 5, 'hide': 3, 'ivory': 2, 'bone': 2},
    
    # Predators (dangerous but valuable)
    'wolf': {'fur': 2, 'bone': 1},
    'lion': {'fur': 2, 'bone': 1},
    'bear': {'fur': 3, 'meat': 2, 'bone': 1},
    'leopard': {'fur': 2},
    'arctic_fox': {'fur': 1},
    
    # Avian
    'songbird': {'meat': 0.2, 'feathers': 1},
    'waterfowl': {'meat': 1, 'feathers': 2},
    'raptor': {'feathers': 2, 'bone': 1},
    'seabird': {'meat': 0.5, 'feathers': 1},
    
    # Aquatic
    'fish': {'fish': 1},
    'marine_mammal': {'meat': 3, 'bone': 2},
}


# Technology requirements for accessing resources
RESOURCE_TECH_REQUIREMENTS = {
    'fish': ['fishing'],  # Need fishing tech to catch fish
    'deep_fish': ['advanced_fishing', 'boats'],  # Deep ocean fishing
    'ivory': ['hunting', 'weapons'],  # Need weapons to hunt elephants
    'pearls': ['diving', 'boats'],  # Need diving tech
    'advanced_stone': ['mining', 'tools'],  # Better stone extraction
}


def get_biome_description(biome_id):
    """Return a description of what a biome provides"""
    biome_names = {
        0: "Deep Ocean",
        1: "Shallow Ocean",
        2: "Beach",
        3: "Desert",
        4: "Savanna",
        5: "Grassland",
        6: "Tropical Rainforest",
        7: "Temperate Forest",
        8: "Taiga",
        9: "Tundra",
        10: "Snow",
        11: "Mountain"
    }
    
    resources = BIOME_RESOURCES.get(biome_id, {})
    name = biome_names.get(biome_id, "Unknown")
    
    if not resources:
        return f"{name}: Barren (no natural resources)"
    
    resource_list = ", ".join([
        f"{RESOURCES[r].icon} {r.capitalize()} ({qty})"
        for r, qty in resources.items()
    ])
    
    return f"{name}: {resource_list}"


if __name__ == "__main__":
    print("=== RESOURCE DEFINITIONS ===\n")
    
    print("All Resources:")
    for key, resource in RESOURCES.items():
        print(f"  {resource.icon} {resource.name} ({resource.category})")
    
    print("\nBiome Resources:")
    for biome_id in range(12):
        print(f"  {get_biome_description(biome_id)}")
    
    print("\nAnimal Resources (sample):")
    for animal in ['deer', 'elephant', 'wolf', 'fish']:
        resources = ANIMAL_RESOURCES[animal]
        res_list = ", ".join([
            f"{RESOURCES[r].icon} {r.capitalize()} ({qty})"
            for r, qty in resources.items()
        ])
        print(f"  {animal.capitalize()}: {res_list}")
