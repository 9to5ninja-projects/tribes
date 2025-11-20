"""
FastAPI server that wraps the game simulation.
React will communicate with this via HTTP.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import numpy as np
from typing import Optional

from game_controller import GameState, WorldConfig

app = FastAPI()

# Allow React to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global game state
current_game: Optional[GameState] = None


class NewGameRequest(BaseModel):
    width: int = 100
    height: int = 80
    sea_level: float = 0.42
    herbivore_population: int = 120
    predator_population: int = 10


@app.get("/")
async def root():
    return {"status": "Game server running"}


@app.post("/game/new")
async def new_game(config: NewGameRequest):
    """Create a new game world"""
    global current_game
    
    world_config = WorldConfig()
    world_config.width = config.width
    world_config.height = config.height
    world_config.sea_level = config.sea_level
    world_config.herbivore_population = config.herbivore_population
    world_config.predator_population = config.predator_population
    
    current_game = GameState(world_config)
    current_game.initialize_world()
    
    return {
        "status": "success",
        "world_size": [world_config.width, world_config.height]
    }


@app.get("/game/world")
async def get_world():
    """Get complete world state for rendering"""
    if not current_game:
        return {"error": "No active game"}
    
    # Convert numpy arrays to lists for JSON
    world_data = {
        "width": int(current_game.world.width),
        "height": int(current_game.world.height),
        "biomes": current_game.world.biomes.tolist(),
        "vegetation": current_game.vegetation.density.tolist(),
    }
    
    return world_data


@app.get("/game/entities")
async def get_entities():
    """Get all entity positions and stats"""
    if not current_game:
        return {"error": "No active game"}
    
    entities = {
        "herbivores": [],
        "predators": [],
        "avian": [],
        "aquatic": []
    }
    
    # Herbivores
    if current_game.animals:
        for animal in current_game.animals.herbivores:
            entities["herbivores"].append({
                "species": animal.species,
                "x": int(animal.x),
                "y": int(animal.y),
                "hp": int(animal.combat_stats.current_hp),
                "max_hp": int(animal.combat_stats.max_hp),
                "attack": int(animal.combat_stats.attack),
                "defense": int(animal.combat_stats.defense)
            })
    
    # Predators
    if current_game.predators:
        for pred in current_game.predators.predators:
            entities["predators"].append({
                "species": pred.species,
                "x": int(pred.x),
                "y": int(pred.y),
                "hp": int(pred.combat_stats.current_hp),
                "max_hp": int(pred.combat_stats.max_hp),
                "attack": int(pred.combat_stats.attack),
                "defense": int(pred.combat_stats.defense)
            })
    
    # Avian
    if current_game.ecology:
        for bird in current_game.ecology.avian_creatures:
            entities["avian"].append({
                "species": bird.species,
                "x": int(bird.x),
                "y": int(bird.y),
                "hp": int(bird.energy * 100),
                "max_hp": 100
            })
        
        # Aquatic
        for aq in current_game.ecology.aquatic_creatures:
            entities["aquatic"].append({
                "species": aq.species,
                "x": int(aq.x),
                "y": int(aq.y),
                "hp": int(aq.energy * 100),
                "max_hp": 100
            })
    
    return entities


@app.get("/game/stats")
async def get_stats():
    """Get game statistics"""
    if not current_game:
        return {"error": "No active game"}
    
    stats = current_game.get_current_statistics()
    
    # Add summary for frontend compatibility
    stats["population"] = {
        "herbivores": sum(stats["populations"].get("herbivores", {}).values()),
        "predators": sum(stats["populations"].get("predators", {}).values())
    }
    
    # Helper to convert numpy types
    def convert_numpy(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy(i) for i in obj]
        return obj
        
    return convert_numpy(stats)


@app.post("/game/step")
async def step_turn():
    """Advance the game by one turn"""
    if not current_game:
        return {"error": "No active game"}
    
    current_game.advance_turn()
    
    return {
        "status": "success",
        "turn": int(current_game.turn),
        "year": int(current_game.climate.year)
    }


@app.get("/game/tile/{x}/{y}")
async def get_tile_info(x: int, y: int):
    """Get detailed info about a specific tile"""
    if not current_game:
        return {"error": "No active game"}
    
    # Terrain info
    biome_names = {
        0: "Deep Ocean", 1: "Shallow Ocean", 2: "Beach", 3: "Desert",
        4: "Savanna", 5: "Grassland", 6: "Tropical Rainforest",
        7: "Temperate Forest", 8: "Taiga", 9: "Tundra", 10: "Snow", 11: "Mountain"
    }
    
    try:
        biome = int(current_game.world.biomes[y, x])
        veg = float(current_game.vegetation.density[y, x])
        temp = float(current_game.world.temperature[y, x])
        moisture = float(current_game.world.moisture[y, x])
        
        # Find entities at this location
        entities_here = []
        
        if current_game.animals:
            for animal in current_game.animals.herbivores:
                if int(animal.x) == x and int(animal.y) == y:
                    entities_here.append({
                        "type": "herbivore",
                        "species": animal.species,
                        "hp": f"{int(animal.combat_stats.current_hp)}/{int(animal.combat_stats.max_hp)}",
                        "stats": f"ATK {int(animal.combat_stats.attack)} | DEF {int(animal.combat_stats.defense)}"
                    })
        
        if current_game.predators:
            for pred in current_game.predators.predators:
                if int(pred.x) == x and int(pred.y) == y:
                    entities_here.append({
                        "type": "predator",
                        "species": pred.species,
                        "hp": f"{int(pred.combat_stats.current_hp)}/{int(pred.combat_stats.max_hp)}",
                        "stats": f"ATK {int(pred.combat_stats.attack)} | DEF {int(pred.combat_stats.defense)}"
                    })
        
        return {
            "terrain": biome_names.get(biome, "Unknown"),
            "vegetation": f"{veg*100:.1f}%",
            "temperature": f"{temp:.2f}",
            "moisture": f"{moisture:.2f}",
            "entities": entities_here
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("Starting game server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
