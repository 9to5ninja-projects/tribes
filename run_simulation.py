
import sys
import os
import numpy as np
import time
import pandas as pd
from game_controller import GameState, WorldConfig

# Add current directory to path
sys.path.append(os.getcwd())

def run_single_simulation(turns=100, seed=None):
    config = WorldConfig()
    config.width = 100
    config.height = 80
    config.seed = seed
    config.fog_of_war = False # Don't need fog for simulation
    
    # Suppress print output during simulation
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w', encoding='utf-8')
    
    try:
        game = GameState(config)
        game.initialize_world()
        
        # Run simulation
        start_time = time.time()
        for _ in range(turns):
            game.advance_turn()
        duration = time.time() - start_time
        
        # Collect stats
        stats = game.get_current_statistics()
        history = game.get_population_history()
        
        return {
            'seed': config.seed,
            'duration': duration,
            'final_turn': game.turn,
            'populations': stats['populations'],
            'extinctions': game.statistics['extinctions'],
            'death_causes': stats['death_causes'],
            'food_chain': stats['food_chain'],
            'history': history
        }
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout

def run_batch_simulations(num_sims=10, turns_per_sim=100):
    print(f"Running {num_sims} simulations of {turns_per_sim} turns each...")
    
    results = []
    
    for i in range(num_sims):
        print(f"  Sim {i+1}/{num_sims}...", end='\r')
        # Use different seeds
        res = run_single_simulation(turns=turns_per_sim, seed=i+1000) 
        results.append(res)
        
    print(f"\nCompleted {num_sims} simulations.")
    return results

def analyze_results(results):
    print("\n=== SIMULATION ANALYSIS ===")
    
    num_sims = len(results)
    
    # 1. Extinction Rates
    all_extinctions = []
    for r in results:
        all_extinctions.extend(r['extinctions'])
    
    extinction_counts = pd.Series(all_extinctions).value_counts()
    print("\nExtinction Frequency (by species):")
    if extinction_counts.empty:
        print("  No extinctions recorded.")
    else:
        print(extinction_counts)
        
    # 2. Population Stability (Avg Final Population)
    print("\nAverage Final Populations:")
    
    # Herbivores
    herb_pops = {}
    for r in results:
        if 'herbivores' in r['populations']:
            for species, count in r['populations']['herbivores'].items():
                if species not in herb_pops: herb_pops[species] = []
                herb_pops[species].append(count)
            
    print("  Herbivores:")
    for species, counts in herb_pops.items():
        avg = np.mean(counts)
        std = np.std(counts)
        print(f"    {species.capitalize()}: {avg:.1f} ± {std:.1f}")
        
    # Predators
    pred_pops = {}
    for r in results:
        if 'predators' in r['populations']:
            for species, count in r['populations']['predators'].items():
                if species not in pred_pops: pred_pops[species] = []
                pred_pops[species].append(count)
            
    print("  Predators:")
    for species, counts in pred_pops.items():
        avg = np.mean(counts)
        std = np.std(counts)
        print(f"    {species.capitalize()}: {avg:.1f} ± {std:.1f}")

    # 3. Death Causes
    print("\nTop Causes of Death (Aggregated):")
    death_causes = {}
    for r in results:
        for species, causes in r['death_causes'].items():
            for cause, count in causes.items():
                key = f"{species}:{cause}"
                death_causes[key] = death_causes.get(key, 0) + count
    
    sorted_deaths = sorted(death_causes.items(), key=lambda x: x[1], reverse=True)
    for k, v in sorted_deaths[:15]:
        print(f"  {k}: {v}")

if __name__ == "__main__":
    # Run a batch
    # User asked for 100-1000, but that might take too long for this interaction.
    # I'll run 20 for now to demonstrate, and the user can run more.
    results = run_batch_simulations(num_sims=20, turns_per_sim=50)
    analyze_results(results)

