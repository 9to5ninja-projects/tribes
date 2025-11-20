"""
Balance configuration for ecosystem stability.
Adjust these values to prevent collapse and create stable population cycles.
"""

# === VEGETATION BALANCE ===
VEGETATION_CONFIG = {
    # Growth rates per biome (base values in vegetation_system.py will be multiplied by these)
    'growth_multiplier': 1.5,  # Global growth speed boost
    
    # Initial density boost
    'initial_density_boost': 1.3,  # Start with more established vegetation
    
    # Biome-specific adjustments
    'biome_adjustments': {
        5: 1.2,  # Grassland - extra boost (prime herbivore habitat)
        6: 1.3,  # Rainforest - extra boost
        7: 1.2,  # Temperate Forest - boost
    }
}

# === HERBIVORE BALANCE ===
HERBIVORE_CONFIG = {
    # Metabolism (energy consumed per turn)
    'metabolism_multiplier': 0.6,  # Reduce by 40% (live longer without food)
    
    # Feeding efficiency
    'food_efficiency_multiplier': 1.8,  # Get more energy from vegetation
    
    # Reproduction
    'reproduction_threshold': 0.5,  # Can reproduce at 50% energy (was 60%)
    'reproduction_rate_multiplier': 1.5,  # More offspring
    'reproduction_cooldown_reduction': 0.6,  # Breed more frequently
    
    # Movement
    'migration_cost_multiplier': 0.4,  # Moving costs less energy
    
    # Initial spawn
    'spawn_energy_range': (0.8, 1.0),  # Start with more energy (was 0.5-0.8)
}

# === PREDATOR BALANCE ===
PREDATOR_CONFIG = {
    # Hunting
    'hunt_success_multiplier': 0.7,  # Slightly less successful hunts
    'hunt_cooldown_multiplier': 1.5,  # Longer rest after kills
    
    # Metabolism
    'metabolism_multiplier': 0.7,  # Reduce hunger pressure
    
    # Can supplement diet (especially bears)
    'allow_vegetation_backup': True,
    'vegetation_backup_efficiency': 0.5,  # How much energy from plants
    
    # Population control
    'max_population_per_species': 25,  # Cap predators to prevent over-hunting
}

# === SPAWNING BALANCE ===
SPAWN_CONFIG = {
    # Establishment phases
    'vegetation_establishment_years': 8,  # More time for plants (was 5)
    'herbivore_establishment_years': 5,   # More time before predators (was 3)
    'predator_delay_years': 2,            # Additional delay before predators
    
    # Initial populations
    'herbivore_per_species': 120,  # Up from 100
    'predator_per_species': 10,    # Down from 15
    'scavenger_count': 25,         # Down from 40
    'avian_count': 80,             # Down from 100
    'aquatic_count': 120,          # Down from 150
    
    # Spawn quality checks
    'herbivore_min_vegetation': 0.15,  # Must have vegetation nearby (was 0.2)
    'predator_min_prey_nearby': 5,     # Must have prey nearby to spawn
}

# === ECOLOGY BALANCE ===
ECOLOGY_CONFIG = {
    # Event frequencies (reduce chaos during establishment)
    'disease_frequency': 0.01,   # Reduce from 0.02
    'disaster_frequency': 0.005, # Reduce from 0.01
    
    # Event severity
    'disease_virulence_multiplier': 0.7,  # Less deadly
    'disaster_intensity_multiplier': 0.7,  # Less destructive
    
    # Scavenger adjustments
    'scavenger_metabolism': 0.05,  # Even lower (was 0.06)
    'carrion_decay_rate': 0.9,     # Slower decay (more food available)
}

# === CLIMATE BALANCE ===
CLIMATE_CONFIG = {
    # Seasonal variation (reduce stress during establishment)
    'seasonal_temperature_shift': 0.8,  # Less extreme seasons
    'seasonal_moisture_shift': 0.8,
    
    # Weather events
    'storm_spawn_multiplier': 0.7,   # Fewer storms
    'drought_spawn_multiplier': 0.7,  # Fewer droughts
}


def apply_balance_to_game(game_state):
    """
    Apply balance configurations to an initialized game state.
    Note: With SRPG system, most stats are defined in srpg_stats.py.
    This function now primarily handles initial population scaling.
    """
    
    # === Apply Vegetation Balance ===
    veg = game_state.vegetation
    veg.density *= VEGETATION_CONFIG['initial_density_boost']
    veg.density = veg.density.clip(0, 1)
    
    for biome_id, multiplier in VEGETATION_CONFIG['biome_adjustments'].items():
        mask = game_state.world.biomes == biome_id
        veg.density[mask] *= multiplier
        veg.density = veg.density.clip(0, 1)
    
    # Boost growth rates
    for biome_id in veg.biome_growth_rates:
        veg.biome_growth_rates[biome_id] *= VEGETATION_CONFIG['growth_multiplier']
    
    # === Apply Ecology Balance ===
    if hasattr(game_state, 'ecology') and game_state.ecology:
        ecology = game_state.ecology
        ecology.disease_spawn_rate = ECOLOGY_CONFIG['disease_frequency']
        ecology.disaster_spawn_rate = ECOLOGY_CONFIG['disaster_frequency']
    
    print("✓ Balance configuration applied (SRPG Stats active)")
    print(f"  - Vegetation boosted by {VEGETATION_CONFIG['initial_density_boost']}x")


def get_balanced_world_config():
    """Return a WorldConfig with balanced initial populations"""
    from game_controller import WorldConfig
    config = WorldConfig()
    config.herbivore_population = SPAWN_CONFIG['herbivore_per_species']
    config.predator_population = SPAWN_CONFIG['predator_per_species']
    config.scavenger_population = SPAWN_CONFIG['scavenger_count']
    config.avian_population = SPAWN_CONFIG['avian_count']
    config.aquatic_population = SPAWN_CONFIG['aquatic_count']
    config.disease_frequency = ECOLOGY_CONFIG['disease_frequency']
    config.disaster_frequency = ECOLOGY_CONFIG['disaster_frequency']
    return config


if __name__ == "__main__":
    print("=== BALANCE CONFIGURATION ===\n")
    print("Key Changes:")
    print(f"  • Herbivore metabolism: -{(1-HERBIVORE_CONFIG['metabolism_multiplier'])*100:.0f}%")
    print(f"  • Herbivore food efficiency: +{(HERBIVORE_CONFIG['food_efficiency_multiplier']-1)*100:.0f}%")
    print(f"  • Vegetation growth: +{(VEGETATION_CONFIG['growth_multiplier']-1)*100:.0f}%")
    print(f"  • Predator hunt success: -{(1-PREDATOR_CONFIG['hunt_success_multiplier'])*100:.0f}%")
    print(f"  • Initial herbivores: {SPAWN_CONFIG['herbivore_per_species']} per species")
    print(f"  • Initial predators: {SPAWN_CONFIG['predator_per_species']} per species")
    print(f"\nEstablishment timeline:")
    print(f"  1. Vegetation: {SPAWN_CONFIG['vegetation_establishment_years']} years")
    print(f"  2. Herbivores: {SPAWN_CONFIG['herbivore_establishment_years']} years")
    print(f"  3. Predators: +{SPAWN_CONFIG['predator_delay_years']} years delay")
