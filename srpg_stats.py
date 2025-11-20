"""
SRPG stat system for all entities in the world.
Every creature, hazard, and resource has discrete stats.
Combat is deterministic based on ATK/DEF/HP rather than probability.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class CombatStats:
    """Base stats for any entity that can engage in combat"""
    max_hp: int
    current_hp: int
    attack: int
    defense: int
    speed: int  # Turn order / movement range
    evasion: int = 0  # Chance to avoid damage (0-100)
    accuracy: int = 100  # Chance to hit (0-100)
    
    # Status effects
    status_effects: List[str] = None
    
    def __post_init__(self):
        if self.status_effects is None:
            self.status_effects = []
    
    def take_damage(self, raw_damage: int) -> int:
        """Apply damage after defense, return actual damage dealt"""
        # Defense reduces damage (not below 1)
        mitigated = max(1, raw_damage - self.defense)
        actual_damage = min(mitigated, self.current_hp)
        self.current_hp -= actual_damage
        return actual_damage
    
    def heal(self, amount: int):
        """Restore HP"""
        self.current_hp = min(self.max_hp, self.current_hp + amount)
    
    def is_alive(self) -> bool:
        return self.current_hp > 0
    
    def hp_percentage(self) -> float:
        return self.current_hp / self.max_hp if self.max_hp > 0 else 0


@dataclass
class MovementStats:
    """Movement capabilities"""
    movement_range: int  # Tiles per turn
    terrain_preferences: Dict[int, float]  # biome_id -> speed_multiplier
    can_swim: bool = False
    can_fly: bool = False


# === HERBIVORE STAT DEFINITIONS ===
HERBIVORE_STATS = {
    'deer': {
        'stats': CombatStats(
            max_hp=30, current_hp=30,
            attack=5,   # Low (defensive only)
            defense=3,
            speed=8,    # Fast
            evasion=20  # Agile
        ),
        'movement': MovementStats(
            movement_range=3,
            terrain_preferences={
                5: 1.0,  # Grassland - optimal
                7: 1.0,  # Forest - optimal
                4: 0.8,  # Savanna - okay
                8: 0.7   # Taiga - slower
            }
        ),
        'food_value': 15,  # HP restored when eaten
        'reproduction_threshold': 20,  # HP needed to breed
        'offspring_count': 2
    },
    'bison': {
        'stats': CombatStats(
            max_hp=50, current_hp=50,
            attack=12,  # Can fight back
            defense=8,
            speed=5,    # Slow
            evasion=5
        ),
        'movement': MovementStats(
            movement_range=2,
            terrain_preferences={
                5: 1.0,  # Grassland - optimal
                4: 0.8   # Savanna
            }
        ),
        'food_value': 30,
        'reproduction_threshold': 30,
        'offspring_count': 1
    },
    'caribou': {
        'stats': CombatStats(
            max_hp=35, current_hp=35,
            attack=6,
            defense=4,
            speed=7,
            evasion=15
        ),
        'movement': MovementStats(
            movement_range=4,  # Migratory
            terrain_preferences={
                8: 1.0,  # Taiga - optimal
                9: 1.0,  # Tundra - optimal
                10: 0.7  # Snow - possible
            }
        ),
        'food_value': 18,
        'reproduction_threshold': 20,
        'offspring_count': 1
    },
    'gazelle': {
        'stats': CombatStats(
            max_hp=25, current_hp=25,
            attack=4,
            defense=2,
            speed=10,  # Fastest
            evasion=30  # Very agile
        ),
        'movement': MovementStats(
            movement_range=4,
            terrain_preferences={
                4: 1.0,  # Savanna - optimal
                5: 0.8   # Grassland
            }
        ),
        'food_value': 12,
        'reproduction_threshold': 15,
        'offspring_count': 2
    },
    'elephant': {
        'stats': CombatStats(
            max_hp=100, current_hp=100,
            attack=25,  # Dangerous when threatened
            defense=15,
            speed=4,
            evasion=0   # Too big to dodge
        ),
        'movement': MovementStats(
            movement_range=2,
            terrain_preferences={
                4: 1.0,  # Savanna - optimal
                6: 1.0   # Rainforest - optimal
            }
        ),
        'food_value': 50,
        'reproduction_threshold': 60,
        'offspring_count': 1
    }
}


# === PREDATOR STAT DEFINITIONS ===
PREDATOR_STATS = {
    'wolf': {
        'stats': CombatStats(
            max_hp=40, current_hp=40,
            attack=15,
            defense=5,
            speed=9,
            evasion=10,
            accuracy=85  # Pack hunters - good accuracy
        ),
        'movement': MovementStats(
            movement_range=3,
            terrain_preferences={
                5: 1.0, 7: 1.0, 8: 1.0
            }
        ),
        'pack_bonus': 3,  # +3 ATK per ally
        'preferred_prey': ['deer', 'caribou', 'bison'],
        'reproduction_threshold': 25,
        'offspring_count': 3
    },
    'lion': {
        'stats': CombatStats(
            max_hp=60, current_hp=60,
            attack=20,
            defense=7,
            speed=8,
            evasion=8,
            accuracy=80
        ),
        'movement': MovementStats(
            movement_range=3,
            terrain_preferences={
                4: 1.0  # Savanna
            }
        ),
        'pack_bonus': 4,
        'preferred_prey': ['gazelle', 'bison', 'elephant'],
        'reproduction_threshold': 35,
        'offspring_count': 2
    },
    'bear': {
        'stats': CombatStats(
            max_hp=70, current_hp=70,
            attack=18,
            defense=10,
            speed=5,
            evasion=5,
            accuracy=70  # Less accurate (opportunistic)
        ),
        'movement': MovementStats(
            movement_range=2,
            terrain_preferences={
                7: 1.0, 8: 1.0
            }
        ),
        'pack_bonus': 0,  # Solitary
        'preferred_prey': ['deer', 'caribou'],
        'can_eat_vegetation': True,
        'vegetation_heal': 5,  # HP per turn from vegetation
        'reproduction_threshold': 40,
        'offspring_count': 2
    },
    'leopard': {
        'stats': CombatStats(
            max_hp=45, current_hp=45,
            attack=17,
            defense=4,
            speed=10,
            evasion=20,  # Agile
            accuracy=90  # Ambush specialist
        ),
        'movement': MovementStats(
            movement_range=3,
            terrain_preferences={
                4: 1.0, 6: 1.0, 7: 1.0
            }
        ),
        'pack_bonus': 0,
        'ambush_bonus': 5,  # Extra damage when attacking from cover
        'preferred_prey': ['gazelle', 'deer'],
        'reproduction_threshold': 28,
        'offspring_count': 2
    },
    'arctic_fox': {
        'stats': CombatStats(
            max_hp=20, current_hp=20,
            attack=8,
            defense=3,
            speed=9,
            evasion=25,
            accuracy=75
        ),
        'movement': MovementStats(
            movement_range=3,
            terrain_preferences={
                9: 1.0, 10: 1.0
            }
        ),
        'pack_bonus': 0,
        'preferred_prey': ['caribou'],  # Opportunistic
        'reproduction_threshold': 12,
        'offspring_count': 4
    }
}


# === ENVIRONMENTAL HAZARD STATS ===
HAZARD_STATS = {
    'wildfire': {
        'damage_per_turn': 15,
        'defense_penetration': 5,  # Ignores some defense
        'affects': ['all_land_creatures', 'vegetation']
    },
    'flood': {
        'damage_per_turn': 10,
        'drowning_threshold': 3,  # Turns until drowning
        'affects': ['non_aquatic']
    },
    'blizzard': {
        'damage_per_turn': 8,
        'speed_reduction': 0.5,  # Halves movement
        'affects': ['all_creatures']
    },
    'earthquake': {
        'damage_burst': 20,
        'terrain_destruction': True,
        'affects': ['all']
    }
}


# === DISEASE STATS ===
DISEASE_STATS = {
    'plague': {
        'damage_per_turn': 5,
        'spread_chance': 0.3,  # Per adjacent creature
        'duration': 8,
        'targets': ['herbivores', 'predators']
    },
    'flu': {
        'damage_per_turn': 3,
        'speed_reduction': 0.3,
        'spread_chance': 0.4,
        'duration': 5,
        'targets': ['all']
    },
    'parasites': {
        'damage_per_turn': 2,
        'defense_reduction': 3,
        'duration': 12,
        'targets': ['herbivores']
    }
}


# === TERRAIN COMBAT MODIFIERS ===
TERRAIN_MODIFIERS = {
    # biome_id: {stat_type: modifier}
    0: {'evasion': -20, 'accuracy': -10},  # Ocean - hard to fight in
    2: {'speed': 0.8},  # Beach - sandy, slower
    3: {'evasion': -10, 'accuracy': -5},  # Desert - visibility issues
    6: {'evasion': 10, 'accuracy': -10},  # Rainforest - cover
    7: {'evasion': 5, 'accuracy': -5},  # Forest - some cover
    8: {'speed': 0.9},  # Taiga - cold, slower
    9: {'speed': 0.7, 'evasion': -5},  # Tundra - very cold
    10: {'speed': 0.5, 'damage': 3},  # Snow - harsh conditions
    11: {'evasion': 15, 'defense': 2},  # Mountain - high ground advantage
}


# === VEGETATION AS RESOURCE ===
VEGETATION_STATS = {
    'food_value': 8,  # HP restored per vegetation unit consumed
    'regrowth_per_turn': 0.05,  # How fast it recovers
    'max_density': 1.0
}


def calculate_combat_damage(attacker: CombatStats, defender: CombatStats, 
                            terrain_modifiers: dict = None) -> tuple[int, bool]:
    """
    Calculate damage for one attack.
    Returns: (damage_dealt, hit_success)
    """
    # Apply terrain modifiers
    attacker_acc = attacker.accuracy
    defender_eva = defender.evasion
    
    if terrain_modifiers:
        attacker_acc += terrain_modifiers.get('accuracy', 0)
        defender_eva += terrain_modifiers.get('evasion', 0)
    
    # Hit check
    hit_roll = np.random.randint(0, 100)
    hit_chance = attacker_acc - defender_eva
    
    if hit_roll >= hit_chance:
        return 0, False  # Miss
    
    # Calculate damage
    raw_damage = attacker.attack
    if terrain_modifiers:
        raw_damage += terrain_modifiers.get('damage', 0)
    
    # Apply to defender
    actual_damage = defender.take_damage(raw_damage)
    
    return actual_damage, True


def get_species_stats(species: str, species_type: str = 'herbivore') -> dict:
    """Get stat template for a species"""
    if species_type == 'herbivore':
        return HERBIVORE_STATS.get(species, HERBIVORE_STATS['deer'])
    elif species_type == 'predator':
        return PREDATOR_STATS.get(species, PREDATOR_STATS['wolf'])
    return None


def create_stats_from_template(template: dict) -> CombatStats:
    """Create a new CombatStats instance from template"""
    stats = template['stats']
    return CombatStats(
        max_hp=stats.max_hp,
        current_hp=stats.current_hp,
        attack=stats.attack,
        defense=stats.defense,
        speed=stats.speed,
        evasion=stats.evasion,
        accuracy=stats.accuracy
    )


if __name__ == "__main__":
    print("=== SRPG STAT SYSTEM ===\n")
    
    print("HERBIVORE STATS:")
    for species, data in HERBIVORE_STATS.items():
        stats = data['stats']
        print(f"\n{species.upper()}:")
        print(f"  HP: {stats.max_hp} | ATK: {stats.attack} | DEF: {stats.defense}")
        print(f"  SPD: {stats.speed} | EVA: {stats.evasion}")
        print(f"  Food Value: {data['food_value']}")
    
    print("\n\nPREDATOR STATS:")
    for species, data in PREDATOR_STATS.items():
        stats = data['stats']
        print(f"\n{species.upper()}:")
        print(f"  HP: {stats.max_hp} | ATK: {stats.attack} | DEF: {stats.defense}")
        print(f"  SPD: {stats.speed} | EVA: {stats.evasion} | ACC: {stats.accuracy}")
        print(f"  Pack Bonus: +{data['pack_bonus']} ATK per ally")
    
    print("\n\nCOMBAT EXAMPLE:")
    wolf = create_stats_from_template(PREDATOR_STATS['wolf'])
    deer = create_stats_from_template(HERBIVORE_STATS['deer'])
    
    print(f"Wolf (HP:{wolf.current_hp} ATK:{wolf.attack}) attacks Deer (HP:{deer.current_hp} DEF:{deer.defense})")
    damage, hit = calculate_combat_damage(wolf, deer)
    
    if hit:
        print(f"  HIT! {damage} damage dealt. Deer HP: {deer.current_hp}/{deer.max_hp}")
    else:
        print(f"  MISS! Deer evaded.")
