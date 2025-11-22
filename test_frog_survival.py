
import sys
import os
from game_controller import GameState, WorldConfig

def test_frog_integration():
    print("Testing Frog Survival (Full Integration)...")
    
    config = WorldConfig()
    config.width = 50
    config.height = 50
    config.herbivore_population = 10 # Small pop for test
    config.predator_population = 0
    
    game = GameState(config)
    game.initialize_world()
    
    # Check frogs
    frogs = [a for a in game.animals.herbivores if a.species == 'frog']
    print(f"Initial Frogs: {len(frogs)}")
    
    if not frogs:
        print("No frogs spawned! Spawning one manually.")
        from animal_system import Animal
        frog = Animal(25, 25, 'frog')
        game.animals.herbivores.append(frog)
        frogs = [frog]
        
    # Track a frog
    frog = frogs[0]
    print(f"Tracking Frog {frog.id} at ({frog.x}, {frog.y})")
    print(f"Initial HP: {frog.combat_stats.current_hp}")
    
    # Run 20 turns
    for i in range(20):
        game.advance_turn()
        print(f"Turn {i+1}: HP={frog.combat_stats.current_hp}, Alive={frog.is_alive()}")
        if not frog.is_alive():
            print(f"Frog Died! Cause: {frog.cause_of_death}")
            break

if __name__ == "__main__":
    test_frog_integration()
