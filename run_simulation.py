
import sys
import os
import numpy as np
import time

# Add current directory to path
sys.path.append(os.getcwd())

from terrain_generator import WorldGenerator
from climate_engine import ClimateEngine
from vegetation_system import VegetationSystem
from animal_system import AnimalSystem
from predator_system import PredatorSystem

def run_long_simulation():
    print("=== STARTING LONG-TERM ECOSYSTEM SIMULATION ===")
    print("Goal: Verify stability with new mortality and environmental systems.")
    
    # 1. Setup World
    print("\n[1/4] Generating World...")
    # Use a larger map to ensure biome diversity
    world = WorldGenerator(width=100, height=80, seed=42) 
    world.generate_world(sea_level=0.4)
    
    climate = ClimateEngine(world)
    vegetation = VegetationSystem(world)
    
    # 2. Initialize Life
    print("\n[2/4] Seeding Life...")
    animals = AnimalSystem(world, vegetation)
    predators = PredatorSystem(world, vegetation, animals)
    
    # Establish vegetation first
    print("  Growing vegetation (5 years)...")
    for _ in range(20):
        climate.advance_turn()
        vegetation.update(climate)
        
    # Spawn animals
    print("  Spawning herbivores...")
    animals.spawn_initial_populations(population_per_species=30)
    
    print("  Spawning predators...")
    predators.spawn_initial_populations(population_per_species=10)
    
    # Initial counts
    h_counts = animals.get_population_counts()
    p_counts = predators.get_population_counts()
    
    print(f"\nInitial Populations:")
    print(f"  Herbivores: {sum(h_counts.values())}")
    print(f"  Predators: {sum(p_counts.values())}")
    
    # 3. Run Simulation
    years = 30
    turns = years * 4
    print(f"\n[3/4] Running Simulation for {years} years ({turns} turns)...")
    
    start_time = time.time()
    
    history = {
        'herbivores': [],
        'predators': []
    }
    
    # Track cumulative deaths for the year
    yearly_deaths = {'herbivores': {}, 'predators': {}}
    
    # Detailed tracking: species -> cause -> count
    detailed_deaths = {} 
    
    for turn in range(1, turns + 1):
        climate.advance_turn()
        vegetation.update(climate)
        animals.update(climate, predators.predators)
        predators.update(climate)
        
        # Aggregate deaths
        # We need to access the raw death data if possible, but animal_system only exposes recent_deaths by cause
        # Let's try to get more detail if we can, or just stick to cause
        
        # Update detailed tracking
        # We need to modify AnimalSystem to track deaths by species AND cause to do this properly
        # For now, we'll just use the aggregate cause
        
        for cause, count in animals.recent_deaths.items():
            yearly_deaths['herbivores'][cause] = yearly_deaths['herbivores'].get(cause, 0) + count
            
        for cause, count in predators.recent_deaths.items():
            yearly_deaths['predators'][cause] = yearly_deaths['predators'].get(cause, 0) + count
        
        # Record stats
        h_pop = sum(animals.get_population_counts().values())
        p_pop = sum(predators.get_population_counts().values())
        history['herbivores'].append(h_pop)
        history['predators'].append(p_pop)
        
        # Annual Report
        if turn % 4 == 0:
            year = turn // 4
            print(f"\n--- Year {year} Report ---")
            print(f"  Total Herbivores: {h_pop}")
            print(f"  Total Predators: {p_pop}")
            
            # Death Report
            print("  Deaths this year:")
            if yearly_deaths['herbivores']:
                print("    Herbivores:")
                for cause, count in yearly_deaths['herbivores'].items():
                    print(f"      - {cause}: {count}")
            else:
                print("    Herbivores: None")
                
            if yearly_deaths['predators']:
                print("    Predators:")
                for cause, count in yearly_deaths['predators'].items():
                    print(f"      - {cause}: {count}")
            else:
                print("    Predators: None")
            
            # Reset yearly deaths
            yearly_deaths = {'herbivores': {}, 'predators': {}}
            
            # Check specific new species
            h_counts = animals.get_population_counts()
            p_counts = predators.get_population_counts()
            
            # Show all species with non-zero population or that are new
            print("  Species Status:")
            all_species = set(list(h_counts.keys()) + list(p_counts.keys()))
            sorted_species = sorted(list(all_species))
            
            # Group by 4 for compact printing
            buffer = []
            for s in sorted_species:
                count = h_counts.get(s, p_counts.get(s, 0))
                if count > 0 or s in ['musk_ox', 'polar_bear', 'iguana']:
                    buffer.append(f"{s}: {count}")
                    if len(buffer) >= 4:
                        print(f"    {', '.join(buffer)}")
                        buffer = []
            if buffer:
                print(f"    {', '.join(buffer)}")
                
    end_time = time.time()
    duration = end_time - start_time
    
    # 4. Final Analysis
    print("\n[4/4] Simulation Complete")
    print(f"Time taken: {duration:.2f}s ({duration/turns:.3f}s per turn)")
    
    h_final = history['herbivores'][-1]
    p_final = history['predators'][-1]
    
    print("\n=== FINAL RESULTS ===")
    print(f"Herbivores: {history['herbivores'][0]} -> {h_final}")
    print(f"Predators: {history['predators'][0]} -> {p_final}")
    
    if h_final == 0:
        print("CRITICAL: Herbivore extinction event!")
    elif h_final < 50:
        print("WARNING: Low herbivore population.")
        
    if p_final == 0:
        print("CRITICAL: Predator extinction event!")
        
    # Check for stability (simple variance check on last 5 years)
    if years >= 10:
        recent_h = history['herbivores'][-20:]
        h_variance = np.std(recent_h)
        print(f"Stability Score (lower is better): {h_variance:.2f}")

if __name__ == "__main__":
    run_long_simulation()
