"""
Combat resolution system for SRPG mechanics.
Handles all entity-vs-entity interactions using discrete stats.
"""

import numpy as np
from srpg_stats import (
    CombatStats, calculate_combat_damage, TERRAIN_MODIFIERS,
    HERBIVORE_STATS, PREDATOR_STATS, VEGETATION_STATS
)


class CombatResolver:
    """Resolves all combat interactions in the world"""
    
    def __init__(self, world_generator):
        self.world = world_generator
        self.combat_log = []
    
    def resolve_predator_hunt(self, predator, prey, predator_stats_template, 
                              prey_stats_template, pack_members=0) -> tuple[bool, int]:
        """
        Resolve a predator hunting prey.
        Returns: (kill_successful, damage_dealt)
        """
        # Get stats
        pred_stats = predator.combat_stats
        prey_stats = prey.combat_stats
        
        # Apply pack bonus
        if pack_members > 0:
            bonus = predator_stats_template.get('pack_bonus', 0) * pack_members
            pred_stats.attack += bonus
        
        # Get terrain modifiers
        terrain = self.world.biomes[predator.y, predator.x]
        terrain_mods = TERRAIN_MODIFIERS.get(terrain, {})
        
        # Calculate damage
        damage, hit = calculate_combat_damage(pred_stats, prey_stats, terrain_mods)
        
        # Remove pack bonus for next turn
        if pack_members > 0:
            bonus = predator_stats_template.get('pack_bonus', 0) * pack_members
            pred_stats.attack -= bonus
        
        # Check if prey died
        kill = not prey_stats.is_alive()
        
        # Log
        if kill:
            self.combat_log.append({
                'type': 'kill',
                'predator': predator.species,
                'prey': prey.species,
                'location': (predator.x, predator.y)
            })
        
        return kill, damage
    
    def resolve_herbivore_feeding(self, herbivore, vegetation_density, 
                                  herbivore_stats_template) -> float:
        """
        Herbivore eats vegetation, returns amount consumed.
        """
        stats = herbivore.combat_stats
        
        # Can only eat if vegetation exists
        if vegetation_density < 0.05:
            return 0.0
        
        # Hunger determines consumption
        hunger = stats.max_hp - stats.current_hp
        max_consumption = min(0.3, hunger / VEGETATION_STATS['food_value'])
        
        actual_consumption = min(vegetation_density, max_consumption)
        
        # Heal herbivore
        hp_gained = int(actual_consumption * VEGETATION_STATS['food_value'])
        stats.heal(hp_gained)
        
        return actual_consumption
    
    def resolve_environmental_damage(self, creature, hazard_type, hazard_intensity) -> int:
        """
        Apply environmental damage (fire, flood, blizzard, etc.)
        Returns damage dealt
        """
        from srpg_stats import HAZARD_STATS
        
        hazard_data = HAZARD_STATS.get(hazard_type, {})
        base_damage = hazard_data.get('damage_per_turn', 10)
        
        # Scale by intensity
        actual_damage = int(base_damage * hazard_intensity)
        
        # Some hazards penetrate defense
        if hazard_data.get('defense_penetration', 0) > 0:
            penetration = hazard_data['defense_penetration']
            old_def = creature.combat_stats.defense
            creature.combat_stats.defense = max(0, old_def - penetration)
            damage = creature.combat_stats.take_damage(actual_damage)
            creature.combat_stats.defense = old_def
        else:
            damage = creature.combat_stats.take_damage(actual_damage)
        
        return damage
    
    def resolve_disease_damage(self, creature, disease_type) -> int:
        """Apply disease damage"""
        from srpg_stats import DISEASE_STATS
        
        disease_data = DISEASE_STATS.get(disease_type, DISEASE_STATS['flu'])
        damage = disease_data['damage_per_turn']
        
        return creature.combat_stats.take_damage(damage)
    
    def can_reproduce(self, creature, stats_template) -> bool:
        """Check if creature has enough HP to reproduce"""
        threshold = stats_template.get('reproduction_threshold', 20)
        return creature.combat_stats.current_hp >= threshold
    
    def get_combat_log(self, clear=True):
        """Get and optionally clear combat log"""
        log = self.combat_log.copy()
        if clear:
            self.combat_log = []
        return log


class TurnOrderManager:
    """Manages turn order based on speed stats"""
    
    def __init__(self):
        self.turn_queue = []
    
    def initialize_turn(self, creatures: list):
        """
        Sort creatures by speed for turn order.
        Creatures is list of (entity, stats) tuples
        """
        self.turn_queue = sorted(
            creatures,
            key=lambda x: x[1].speed,
            reverse=True
        )
    
    def get_next_actor(self):
        """Get next creature to act"""
        if self.turn_queue:
            return self.turn_queue.pop(0)
        return None
    
    def has_actors(self):
        return len(self.turn_queue) > 0


if __name__ == "__main__":
    print("=== COMBAT SYSTEM TEST ===\n")
    
    from terrain_generator import WorldGenerator
    from srpg_stats import create_stats_from_template
    
    # Mock world
    world = WorldGenerator(width=10, height=10, seed=42)
    world.generate_world()
    
    # Create combat resolver
    resolver = CombatResolver(world)
    
    # Mock creatures
    class MockCreature:
        def __init__(self, x, y, species, stats):
            self.x = x
            self.y = y
            self.species = species
            self.combat_stats = stats
    
    # Wolf vs Deer
    wolf = MockCreature(5, 5, 'wolf', create_stats_from_template(PREDATOR_STATS['wolf']))
    deer = MockCreature(5, 5, 'deer', create_stats_from_template(HERBIVORE_STATS['deer']))
    
    print(f"Wolf (HP:{wolf.combat_stats.current_hp}) hunts Deer (HP:{deer.combat_stats.current_hp})")
    
    for turn in range(1, 6):
        kill, damage = resolver.resolve_predator_hunt(
            wolf, deer,
            PREDATOR_STATS['wolf'],
            HERBIVORE_STATS['deer'],
            pack_members=0
        )
        
        print(f"Turn {turn}: {'HIT' if damage > 0 else 'MISS'} - {damage} damage")
        print(f"  Deer HP: {deer.combat_stats.current_hp}/{deer.combat_stats.max_hp}")
        
        if kill:
            print(f"  DEER KILLED!")
            break
    
    print(f"\nCombat log: {resolver.get_combat_log()}")
