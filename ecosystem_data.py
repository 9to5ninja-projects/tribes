"""
Ecological Food Web Data Structure
For use in tribe survival game - defines predator-prey relationships,
biomass ratios, and resource values based on trophic position.
"""

# TROPHIC LEVEL DEFINITIONS
TROPHIC_LEVELS = {
    'producer': 0,      # Plants (not in game)
    'herbivore': 1,     # Primary consumers
    'predator': 2,      # Secondary consumers
    'apex': 3,          # Apex predators
    'scavenger': 4,     # Decomposers
}

# ANIMAL DATABASE
# Each animal has: trophic_level, biome(s), diet, spawn_weight, meat_yield, danger
ANIMALS = {
    # HERBIVORES (Trophic Level 1)
    'rabbit': {
        'trophic_level': 'herbivore',
        'biomes': ['grassland', 'forest', 'savanna', 'taiga', 'desert'], # Added savanna/taiga/desert for broad coverage
        'diet': 'plants',
        'spawn_weight': 200,  # Very common
        'meat_yield': 4,
        'danger': 1,
        'herd_size': (1, 3),
        'speed': 'fast',
        'special_drops': ['pelt_small'],
    },
    'deer': {
        'trophic_level': 'herbivore',
        'biomes': ['forest', 'grassland'],
        'diet': 'plants',
        'spawn_weight': 80,
        'meat_yield': 10,
        'danger': 2,
        'herd_size': (3, 8),
        'speed': 'fast',
        'special_drops': ['pelt_medium', 'antlers'],
    },
    'bison': {
        'trophic_level': 'herbivore',
        'biomes': ['grassland', 'savanna'],
        'diet': 'plants',
        'spawn_weight': 60,
        'meat_yield': 20,
        'danger': 4,  # Defensive when cornered
        'herd_size': (8, 20),
        'speed': 'medium',
        'special_drops': ['pelt_large', 'horns'],
    },
    'gazelle': {
        'trophic_level': 'herbivore',
        'biomes': ['savanna'],
        'diet': 'plants',
        'spawn_weight': 70,
        'meat_yield': 8,
        'danger': 1,
        'herd_size': (10, 30),
        'speed': 'very_fast',
        'special_drops': ['pelt_medium', 'horns'],
    },
    'caribou': {
        'trophic_level': 'herbivore',
        'biomes': ['taiga', 'tundra'],
        'diet': 'plants',
        'spawn_weight': 50,
        'meat_yield': 15,
        'danger': 2,
        'herd_size': (15, 50),
        'speed': 'medium',
        'special_drops': ['pelt_warm', 'antlers'],
    },
    'musk_ox': {
        'trophic_level': 'herbivore',
        'biomes': ['tundra', 'snow'],
        'diet': 'plants',
        'spawn_weight': 30,
        'meat_yield': 18,
        'danger': 5,  # Defensive formation
        'herd_size': (5, 15),
        'speed': 'slow',
        'special_drops': ['pelt_warm', 'horns'],
    },
    'elephant': {
        'trophic_level': 'herbivore',
        'biomes': ['savanna', 'rainforest'],
        'diet': 'plants',
        'spawn_weight': 10,  # Rare megafauna
        'meat_yield': 40,
        'danger': 8,  # Extremely dangerous if provoked
        'herd_size': (3, 10),
        'speed': 'slow',
        'special_drops': ['ivory', 'pelt_thick'],
    },
    'iguana': {
        'trophic_level': 'herbivore',
        'biomes': ['desert', 'beach'],
        'diet': 'plants',
        'spawn_weight': 40,
        'meat_yield': 3,
        'danger': 1,
        'herd_size': (1, 1),
        'speed': 'slow',
        'special_drops': [],
    },
    'frog': {
        'trophic_level': 'herbivore',  # Actually insectivore (secondary)
        'biomes': ['rainforest', 'swamp', 'forest'], # Added forest
        'diet': 'insects',
        'spawn_weight': 300,
        'meat_yield': 1,
        'danger': 0,
        'herd_size': (1, 5),
        'speed': 'slow',
        'special_drops': [],
    },
    
    # PREDATORS (Trophic Level 2)
    'wolf': {
        'trophic_level': 'predator',
        'biomes': ['forest', 'taiga'],
        'diet': ['deer', 'caribou', 'rabbit'],
        'spawn_weight': 15,
        'meat_yield': 10,
        'danger': 7,
        'herd_size': (3, 8),  # Pack
        'speed': 'fast',
        'special_drops': ['pelt_predator', 'fangs', 'claws'],
        'hunting_style': 'pack',
    },
    'lion': {
        'trophic_level': 'apex',  # Dual role: also apex
        'biomes': ['savanna'],
        'diet': ['gazelle', 'bison', 'elephant_young'],
        'spawn_weight': 8,
        'meat_yield': 15,
        'danger': 9,
        'herd_size': (2, 6),  # Pride
        'speed': 'fast',
        'special_drops': ['pelt_predator', 'fangs', 'claws', 'mane'],
        'hunting_style': 'pack',
    },
    'bear': {
        'trophic_level': 'predator',
        'biomes': ['forest'],
        'diet': ['deer', 'rabbit', 'fish', 'berries'],  # Omnivore
        'spawn_weight': 12,
        'meat_yield': 20,
        'danger': 8,
        'herd_size': (1, 1),
        'speed': 'medium',
        'special_drops': ['pelt_thick', 'claws', 'fangs'],
        'hunting_style': 'solo',
    },
    'polar_bear': {
        'trophic_level': 'apex',
        'biomes': ['snow', 'tundra'],
        'diet': ['marine_mammal', 'caribou', 'musk_ox'],
        'spawn_weight': 3,
        'meat_yield': 25,
        'danger': 10,
        'herd_size': (1, 1),
        'speed': 'medium',
        'special_drops': ['pelt_white', 'claws', 'fangs'],
        'hunting_style': 'solo',
    },
    'leopard': {
        'trophic_level': 'predator',
        'biomes': ['rainforest', 'savanna'],
        'diet': ['gazelle', 'deer', 'rabbit'],
        'spawn_weight': 10,
        'meat_yield': 12,
        'danger': 7,
        'herd_size': (1, 1),
        'speed': 'very_fast',
        'special_drops': ['pelt_spotted', 'fangs', 'claws'],
        'hunting_style': 'ambush',
    },
    'snow_leopard': {
        'trophic_level': 'predator',
        'biomes': ['mountain', 'snow'],
        'diet': ['caribou', 'musk_ox', 'rabbit'],
        'spawn_weight': 5,
        'meat_yield': 12,
        'danger': 7,
        'herd_size': (1, 1),
        'speed': 'fast',
        'special_drops': ['pelt_rare', 'fangs', 'claws'],
        'hunting_style': 'ambush',
    },
    'arctic_fox': {
        'trophic_level': 'predator',
        'biomes': ['tundra', 'snow'],
        'diet': ['rabbit', 'carrion'],  # Also scavenger
        'spawn_weight': 20,
        'meat_yield': 5,
        'danger': 3,
        'herd_size': (1, 2),
        'speed': 'fast',
        'special_drops': ['pelt_white'],
        'hunting_style': 'solo',
    },
    'red_fox': {
        'trophic_level': 'predator',
        'biomes': ['grassland', 'forest'],
        'diet': ['rabbit', 'frog'],
        'spawn_weight': 25,
        'meat_yield': 5,
        'danger': 3,
        'herd_size': (1, 2),
        'speed': 'fast',
        'special_drops': ['pelt_red'],
        'hunting_style': 'solo',
    },
    'boar': {
        'trophic_level': 'predator',
        'biomes': ['forest', 'rainforest'],
        'diet': ['roots', 'fungi', 'small_animals'],  # Omnivore
        'spawn_weight': 18,
        'meat_yield': 12,
        'danger': 6,
        'herd_size': (2, 6),
        'speed': 'medium',
        'special_drops': ['pelt_tough', 'tusks'],
        'hunting_style': 'aggressive',
    },
    'jackal': {
        'trophic_level': 'predator',
        'biomes': ['desert', 'savanna'],
        'diet': ['rabbit', 'gazelle', 'carrion'],
        'spawn_weight': 15,
        'meat_yield': 6,
        'danger': 4,
        'herd_size': (2, 4),
        'speed': 'fast',
        'special_drops': ['pelt_scavenger'],
        'hunting_style': 'opportunistic',
    },
    'crocodile': {
        'trophic_level': 'predator',
        'biomes': ['rivers', 'swamp'],
        'diet': ['any_at_water'],  # Ambush anything
        'spawn_weight': 8,
        'meat_yield': 15,
        'danger': 9,
        'herd_size': (1, 1),
        'speed': 'slow_land_fast_water',
        'special_drops': ['scales', 'teeth'],
        'hunting_style': 'ambush',
    },
    'snake': {
        'trophic_level': 'predator',
        'biomes': ['rainforest', 'desert'],
        'diet': ['rabbit', 'frog', 'iguana'],
        'spawn_weight': 20,
        'meat_yield': 4,
        'danger': 5,  # Venomous
        'herd_size': (1, 1),
        'speed': 'slow',
        'special_drops': ['scales', 'venom'],
        'hunting_style': 'ambush',
    },
    'giant_toad': {
        'trophic_level': 'predator',
        'biomes': ['rainforest', 'swamp'],
        'diet': ['frog', 'insects'],
        'spawn_weight': 30,
        'meat_yield': 3,
        'danger': 2,
        'herd_size': (1, 2),
        'speed': 'slow',
        'special_drops': ['toxin'],
        'hunting_style': 'ambush',
    },
    
    # AVIAN
    'songbird': {
        'trophic_level': 'herbivore',
        'biomes': ['all'],
        'diet': ['insects', 'seeds'],
        'spawn_weight': 150,
        'meat_yield': 1,
        'danger': 0,
        'herd_size': (5, 20),
        'speed': 'flying',
        'special_drops': ['feathers_small'],
    },
    'waterfowl': {
        'trophic_level': 'herbivore',
        'biomes': ['rivers', 'swamp', 'lakes'],
        'diet': ['aquatic_plants', 'fish_small'],
        'spawn_weight': 60,
        'meat_yield': 3,
        'danger': 0,
        'herd_size': (3, 15),
        'speed': 'flying',
        'special_drops': ['feathers_medium'],
    },
    'raptor': {
        'trophic_level': 'apex',
        'biomes': ['all'],
        'diet': ['rabbit', 'songbird', 'fish'],
        'spawn_weight': 10,
        'meat_yield': 4,
        'danger': 4,
        'herd_size': (1, 2),
        'speed': 'flying',
        'special_drops': ['feathers_raptor', 'talons'],
        'hunting_style': 'aerial',
    },
    'seabird': {
        'trophic_level': 'herbivore',
        'biomes': ['coastal', 'ocean'],
        'diet': ['fish'],
        'spawn_weight': 80,
        'meat_yield': 2,
        'danger': 0,
        'herd_size': (10, 50),
        'speed': 'flying',
        'special_drops': ['feathers_white'],
    },
    'insectivore': {
        'trophic_level': 'herbivore',
        'biomes': ['all'],
        'diet': ['insects'],
        'spawn_weight': 120,
        'meat_yield': 1,
        'danger': 0,
        'herd_size': (3, 10),
        'speed': 'flying',
        'special_drops': ['feathers_small'],
    },
    
    # AQUATIC
    'fish': {
        'trophic_level': 'herbivore',
        'biomes': ['rivers', 'lakes', 'ocean'],
        'diet': ['algae', 'plankton'],
        'spawn_weight': 500,
        'meat_yield': 2,
        'danger': 0,
        'herd_size': (10, 100),
        'speed': 'swimming',
        'special_drops': [],
    },
    'predatory_fish': {
        'trophic_level': 'predator',
        'biomes': ['rivers', 'lakes', 'ocean'],
        'diet': ['fish'],
        'spawn_weight': 80,
        'meat_yield': 5,
        'danger': 3,
        'herd_size': (1, 5),
        'speed': 'swimming',
        'special_drops': ['teeth'],
    },
    'marine_mammal': {
        'trophic_level': 'apex',
        'biomes': ['ocean', 'coastal'],
        'diet': ['fish', 'smaller_mammals'],
        'spawn_weight': 15,
        'meat_yield': 30,
        'danger': 8,
        'herd_size': (1, 6),
        'speed': 'swimming',
        'special_drops': ['blubber', 'teeth'],
    },
    'shark': {
        'trophic_level': 'apex',
        'biomes': ['ocean', 'coastal'],
        'diet': ['fish', 'marine_mammal'],
        'spawn_weight': 5,
        'meat_yield': 20,
        'danger': 10,
        'herd_size': (1, 1),
        'speed': 'swimming',
        'special_drops': ['teeth_shark', 'fins'],
    },
    
    # SCAVENGERS
    'scavenger': {
        'trophic_level': 'scavenger',
        'biomes': ['all'],
        'diet': ['carrion'],
        'spawn_weight': 40,
        'meat_yield': 4,
        'danger': 2,
        'herd_size': (3, 12),
        'speed': 'flying',
        'special_drops': [],
        'behavior': 'attracted_to_kills',
    },
}

# PREDATOR-PREY MATRIX
# Key: Predator, Value: List of preferred prey
PREDATION_MATRIX = {
    'wolf': ['deer', 'caribou', 'rabbit'],
    'lion': ['gazelle', 'bison'],
    'bear': ['deer', 'rabbit', 'fish'],
    'polar_bear': ['marine_mammal', 'caribou', 'musk_ox'],
    'leopard': ['gazelle', 'deer', 'rabbit'],
    'snow_leopard': ['caribou', 'musk_ox', 'rabbit'],
    'arctic_fox': ['rabbit'],
    'red_fox': ['rabbit', 'frog'],
    'boar': ['rabbit'],  # Simplified omnivore diet
    'jackal': ['rabbit', 'gazelle'],
    'crocodile': ['deer', 'gazelle', 'waterfowl'],
    'snake': ['rabbit', 'frog', 'iguana'],
    'giant_toad': ['frog'],
    'raptor': ['rabbit', 'songbird'],
    'predatory_fish': ['fish'],
    'marine_mammal': ['fish'],
    'shark': ['fish', 'marine_mammal'],
    'scavenger': [],  # Only eats carrion
}

# BIOME CARRYING CAPACITY (Max population density)
CARRYING_CAPACITY = {
    'grassland': 1.2,      # High herbivore capacity
    'savanna': 1.3,        # Highest (open plains)
    'forest': 1.0,         # Baseline
    'taiga': 0.7,          # Cold, sparse
    'tundra': 0.4,         # Very sparse
    'snow': 0.3,           # Minimal
    'rainforest': 0.9,     # High diversity, vertical niches
    'desert': 0.3,         # Water/food scarce
    'swamp': 0.8,          # Wetland specialist
    'mountain': 0.5,       # Harsh terrain
    'beach': 0.6,          # Transitional
    'coastal': 0.9,        # Rich marine life
    'ocean': 1.5,          # Massive fish biomass
    'rivers': 1.1,         # High aquatic productivity
    'lakes': 1.0,          # Moderate aquatic
}

# COMPETITION GROUPS (Animals that compete for same resources)
COMPETITION_GROUPS = {
    'grassland_grazers': ['bison', 'gazelle', 'deer', 'rabbit'],
    'forest_browsers': ['deer', 'rabbit'],
    'tundra_grazers': ['caribou', 'musk_ox'],
    'pack_predators': ['wolf', 'lion'],
    'solo_predators': ['leopard', 'snow_leopard', 'bear'],
    'small_predators': ['red_fox', 'arctic_fox', 'snake'],
    'scavenger_niche': ['scavenger', 'jackal', 'arctic_fox'],
    'aquatic_predators': ['crocodile', 'predatory_fish', 'shark'],
    'aerial_hunters': ['raptor'],
}

# BIOMASS RATIOS (for population spawn balancing)
# Based on ecological pyramid: 10:1 ratio per trophic level
BIOMASS_RATIOS = {
    'herbivore': 100,   # Most common
    'predator': 10,     # 10% of herbivore population
    'apex': 1,          # 1% of herbivore population
    'scavenger': 5,     # Tied to predator activity
}

def calculate_spawn_rate(animal_name, biome):
    """
    Calculate spawn probability for an animal in a given biome.
    
    Returns float between 0-1 representing spawn chance.
    """
    animal = ANIMALS[animal_name]
    
    # Check if animal lives in this biome
    if biome not in animal['biomes'] and 'all' not in animal['biomes']:
        return 0.0
    
    # Base spawn from animal definition
    base_spawn = animal['spawn_weight']
    
    # Modify by biome carrying capacity
    capacity_modifier = CARRYING_CAPACITY.get(biome, 1.0)
    
    # Modify by trophic level (maintain pyramid)
    trophic_modifier = BIOMASS_RATIOS.get(animal['trophic_level'], 1.0) / 100.0
    
    # Final spawn rate (normalize to 0-1)
    spawn_rate = (base_spawn * capacity_modifier * trophic_modifier) / 10000.0
    
    return min(spawn_rate, 1.0)

def get_prey_for_predator(predator_name):
    """Returns list of valid prey for a given predator."""
    return PREDATION_MATRIX.get(predator_name, [])

def get_predators_for_prey(prey_name):
    """Returns list of predators that hunt a given prey."""
    predators = []
    for predator, prey_list in PREDATION_MATRIX.items():
        if prey_name in prey_list:
            predators.append(predator)
    return predators

def get_competitors(animal_name):
    """Returns list of animals that compete for same resources."""
    competitors = []
    for group, members in COMPETITION_GROUPS.items():
        if animal_name in members:
            competitors.extend([m for m in members if m != animal_name])
    return list(set(competitors))  # Remove duplicates
