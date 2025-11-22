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

from game_controller import GameState, WorldConfig, SaveSystem
from tribe_system import Tribe, Unit, UnitType, Structure, StructureType
import os
import glob

app = FastAPI()

# Ensure saves directory exists
os.makedirs("saves", exist_ok=True)

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
    starting_units: dict = {"gatherer": 2, "hunter": 1}
    starting_biome: Optional[str] = None
    fog_of_war: bool = True

class MoveUnitRequest(BaseModel):
    unit_id: str
    dx: int
    dy: int

class ActionRequest(BaseModel):
    unit_id: str
    action_type: str # "gather", "hunt", "build", "recruit"
    target_resource: Optional[str] = None
    target_id: Optional[str] = None # For hunting
    structure_type: Optional[str] = None # For building
    build_x: Optional[int] = None # For building location
    build_y: Optional[int] = None
    unit_type: Optional[str] = None # For recruiting

class SaveGameRequest(BaseModel):
    filename: str

class LoadGameRequest(BaseModel):
    filename: str


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
    
    # Handle "Random" biome selection
    biome_pref = config.starting_biome
    if biome_pref == "Random":
        biome_pref = None
        
    current_game.initialize_world(
        starting_units=config.starting_units,
        preferred_biome=biome_pref,
        fog_of_war=config.fog_of_war
    )
    
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
        "aquatic": [],
        "scavengers": [],
        "nomads": []
    }
    
    # Herbivores
    if current_game.animals:
        for animal in current_game.animals.herbivores:
            entities["herbivores"].append({
                "id": animal.id,
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
                "id": pred.id,
                "species": pred.species,
                "x": int(pred.x),
                "y": int(pred.y),
                "hp": int(pred.combat_stats.current_hp),
                "max_hp": int(pred.combat_stats.max_hp),
                "attack": int(pred.combat_stats.attack),
                "defense": int(pred.combat_stats.defense)
            })
            
    # Nomads
    if current_game.nomads:
        for band in current_game.nomads.bands:
            for member in band.members:
                entities["nomads"].append({
                    "id": member.id,
                    "x": int(member.x),
                    "y": int(member.y),
                    "hp": int(member.hp),
                    "max_hp": int(member.max_hp),
                    "energy": int(member.energy),
                    "band_id": band.id
                })
    
    # Ecology
    if current_game.ecology:
        # Avian
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
            
        # Scavengers
        for scav in current_game.ecology.scavengers:
            entities["scavengers"].append({
                "species": scav.species,
                "x": int(scav.x),
                "y": int(scav.y),
                "hp": int(scav.energy * 100),
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
        "predators": sum(stats["populations"].get("predators", {}).values()),
        "scavengers": stats["populations"].get("scavengers", 0),
        "avian": stats["populations"].get("avian", 0),
        "aquatic": stats["populations"].get("aquatic", 0)
    }

    # Add tribe stats if available
    if current_game.tribe:
        stats["tribe"] = {
            "population": len(current_game.tribe.units),
            "stockpile": current_game.tribe.stockpile
        }
    
    # Add history for graphs
    stats["history"] = current_game.get_population_history()
    
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


@app.get("/game/tribe")
async def get_tribe():
    """Get tribe status and units"""
    if not current_game or not current_game.tribe:
        return {"error": "No active tribe"}
    return current_game.tribe.to_dict()


@app.post("/game/unit/move")
async def move_unit(request: MoveUnitRequest):
    """Move a unit"""
    if not current_game or not current_game.tribe:
        return {"error": "No active game"}
    
    # Find unit
    unit = next((u for u in current_game.tribe.units if u.id == request.unit_id), None)
    if not unit:
        return {"error": "Unit not found"}
        
    if unit.has_moved:
        return {"error": "Unit has already moved this turn"}

    # Validate move (Manhattan distance for diamond shape)
    distance = abs(request.dx) + abs(request.dy)
    if distance > unit.movement_range:
        return {"error": f"Move out of range (max {unit.movement_range})"}
        
    # Execute move
    unit.move(request.dx, request.dy)
    current_game.tribe.update_visibility()
    
    return {"status": "success", "unit": unit.to_dict()}


@app.post("/game/unit/action")
async def unit_action(request: ActionRequest):
    """Perform a unit action (gather, etc)"""
    if not current_game or not current_game.tribe:
        return {"error": "No active game"}
    
    # Find unit
    unit = next((u for u in current_game.tribe.units if u.id == request.unit_id), None)
    if not unit:
        return {"error": "Unit not found"}
        
    if unit.has_acted:
        return {"error": "Unit has already acted this turn"}

    if request.action_type == "gather":
        if unit.type == "hunter":
            return {"error": "Hunters cannot gather resources"}

        # Check resources at unit location
        tile_res = current_game.resource_map.get((unit.x, unit.y))
        if not tile_res:
            return {"error": "No resources here"}
            
        target = request.target_resource
        # If no target specified, pick the first one
        if not target:
            target = next(iter(tile_res.keys()))
            
        if target not in tile_res:
             return {"error": f"No {target} here"}
             
        # Calculate amount based on unit type
        amount = 10 # Base amount
        if unit.type == "gatherer":
            amount = 20
            
        # Deplete from tile
        available = tile_res[target]
        gathered = min(available, amount)
        tile_res[target] -= gathered
        
        # Cleanup empty resources
        if tile_res[target] <= 0:
            del tile_res[target]
            
        # Add to stockpile
        current_game.tribe.stockpile[target] = current_game.tribe.stockpile.get(target, 0) + gathered
        
        unit.has_acted = True
        unit.has_moved = True # Action ends turn (cannot move after)
        unit.energy = max(0, unit.energy - 1)
        
        return {
            "status": "success", 
            "gathered": gathered, 
            "resource": target,
            "stockpile": current_game.tribe.stockpile
        }
        
    elif request.action_type == "hunt":
        # Check for animals in range (Range 2 for hunters, 1 for others)
        hunt_range = 2 if unit.type == "hunter" else 1
        
        # Find targets
        targets = []
        
        # Check herbivores
        if current_game.animals:
            for animal in current_game.animals.herbivores:
                dist = abs(animal.x - unit.x) + abs(animal.y - unit.y)
                if dist <= hunt_range:
                    targets.append(animal)

        # Check predators
        if current_game.predators:
            for pred in current_game.predators.predators:
                dist = abs(pred.x - unit.x) + abs(pred.y - unit.y)
                if dist <= hunt_range:
                    targets.append(pred)
        
        if not targets:
            return {"error": "No animals in range"}
            
        # Attack specific target if provided, otherwise first available
        target = None
        if request.target_id:
            target = next((t for t in targets if str(t.id) == request.target_id), None)
            
        if not target:
            target = targets[0]
        
        # Calculate damage
        damage = 5
        if unit.type == "hunter":
            damage = 15
            # Apply research bonuses
            if current_game.tribe:
                # Check for completed research structures to determine "tech level"
                # For now, just having the structure adds a bonus?
                # Or use the research_levels dict we added
                weapon_level = current_game.tribe.research_levels.get("weapons", 0)
                damage += (weapon_level * 5)
                
                # Also check if we have the structure built, maybe that gives base level 1?
                # The user said "derived from the... buildings".
                # Let's say: Base 15.
                # If Weapon Lab exists: +5.
                # Future: Research actions increase level.
                has_weapon_lab = any(s.type == StructureType.RESEARCH_WEAPON and s.is_complete for s in current_game.tribe.structures)
                if has_weapon_lab:
                    damage += 5
            
        target.combat_stats.take_damage(damage)
        
        result = {
            "status": "success",
            "action": "hunt",
            "damage": damage,
            "target_hp": target.combat_stats.current_hp,
            "target_species": target.species,
            "target_location": [int(target.x), int(target.y)]
        }
        
        if not target.is_alive():
            # Kill reward
            food_gain = 20
            current_game.tribe.stockpile["food"] += food_gain
            result["kill"] = True
            result["food_gain"] = food_gain
            
            # Remove from game world immediately
            if current_game.animals and target in current_game.animals.herbivores:
                current_game.animals.herbivores.remove(target)
            elif current_game.predators and target in current_game.predators.predators:
                current_game.predators.predators.remove(target)
            
        unit.has_acted = True
        unit.has_moved = True # Action ends turn (cannot move after)
        unit.energy = max(0, unit.energy - 1)
        return result

    elif request.action_type == "build":
        # Determine build location
        bx = request.build_x if request.build_x is not None else unit.x
        by = request.build_y if request.build_y is not None else unit.y
        
        # Check adjacency
        dist = abs(bx - unit.x) + abs(by - unit.y)
        if dist > 1:
            return {"error": "Can only build on current or adjacent tile"}
            
        # Check if tile is occupied by structure
        for s in current_game.tribe.structures:
            if s.x == bx and s.y == by:
                return {"error": "Tile already has a structure"}

        # Define costs and requirements
        costs = {}
        req_type = request.structure_type
        st_enum = None
        
        if req_type == "bonfire":
            # Any class can build bonfires
            costs = {"wood": 10, "flint": 5}
            st_enum = StructureType.BONFIRE
            
        elif req_type == "hut":
            if unit.type != "crafter":
                return {"error": "Only Crafters can build Huts"}
            costs = {"wood": 20, "fiber": 10}
            st_enum = StructureType.HUT

        elif req_type == "workshop":
            if unit.type != "crafter":
                return {"error": "Only Crafters can build Workshops"}
            costs = {"wood": 20, "stone": 20}
            st_enum = StructureType.WORKSHOP
            
        elif req_type == "research_weapon":
            if unit.type != "crafter":
                return {"error": "Only Crafters can build Research Stations"}
            costs = {"wood": 30, "stone": 10}
            st_enum = StructureType.RESEARCH_WEAPON
            
        elif req_type == "research_armor":
            if unit.type != "crafter":
                return {"error": "Only Crafters can build Research Stations"}
            costs = {"wood": 30, "fiber": 20}
            st_enum = StructureType.RESEARCH_ARMOR
            
        elif req_type == "idol":
            if unit.type != "crafter":
                return {"error": "Only Crafters can build Idols"}
            costs = {"wood": 40, "stone": 40}
            st_enum = StructureType.IDOL
            
        else:
            return {"error": f"Unknown structure type: {req_type}"}

        # Check cost
        for res, amount in costs.items():
            if current_game.tribe.stockpile.get(res, 0) < amount:
                return {"error": f"Not enough {res} (need {amount})"}
        
        # Deduct cost
        for res, amount in costs.items():
            current_game.tribe.stockpile[res] -= amount
            
        # Determine construction time
        build_turns = 0
        if st_enum == StructureType.BONFIRE:
            build_turns = 1
        elif st_enum == StructureType.HUT:
            build_turns = 4
        elif st_enum == StructureType.WORKSHOP:
            build_turns = 6
        elif st_enum in [StructureType.RESEARCH_WEAPON, StructureType.RESEARCH_ARMOR]:
            build_turns = 8
        elif st_enum == StructureType.IDOL:
            build_turns = 12
            
        # Create structure
        structure = Structure(bx, by, st_enum)
        structure.construction_turns_left = build_turns
        structure.max_construction_turns = build_turns
        structure.is_complete = False
        
        current_game.tribe.add_structure(structure)
        
        unit.has_acted = True
        unit.has_moved = True
        unit.energy = max(0, unit.energy - 1)
        
        return {
            "status": "success",
            "action": "build",
            "structure": structure.to_dict(),
            "stockpile": current_game.tribe.stockpile,
            "message": f"Construction started: {req_type} ({build_turns} turns)"
        }
            
    elif request.action_type == "recruit":
        unit_type = request.unit_type
        
        # Requirements and Costs
        food_cost = 0
        turns = 0
        req_structure = None
        
        if unit_type == "gatherer":
            food_cost = 5
            turns = 3
        elif unit_type == "hunter":
            food_cost = 7
            turns = 3
        elif unit_type == "crafter":
            food_cost = 10
            turns = 9
            req_structure = StructureType.BONFIRE
            # Culture Requirement
            if current_game.tribe.culture < 5:
                 return {"error": "Need 5 Culture to recruit Crafter"}
        elif unit_type == "shaman":
            food_cost = 12
            turns = 12
            req_structure = StructureType.IDOL
        else:
            return {"error": f"Unknown unit type: {unit_type}"}
            
        # Check Structure Requirement
        if req_structure:
            near_structure = False
            for s in current_game.tribe.structures:
                if s.type == req_structure and s.is_complete:
                    dist = abs(s.x - unit.x) + abs(s.y - unit.y)
                    if dist <= 3:
                        near_structure = True
                        break
            if not near_structure:
                return {"error": f"Must be near a completed {req_structure} to recruit {unit_type}"}
        
        # Check Food Cost
        if current_game.tribe.stockpile.get("food", 0) < food_cost:
            return {"error": f"Not enough food (need {food_cost})"}
            
        # Deduct Cost
        current_game.tribe.stockpile["food"] -= food_cost
        
        # Add to Training Queue
        current_game.tribe.training_queue.append({
            "type": unit_type,
            "turns_left": turns,
            "x": unit.x,
            "y": unit.y
        })
        
        unit.has_acted = True
        unit.energy = max(0, unit.energy - 1)
        
        return {
            "status": "success",
            "action": "recruit",
            "message": f"Training started for {unit_type} ({turns} turns)",
            "stockpile": current_game.tribe.stockpile
        }

    return {"error": "Unknown action"}


@app.post("/game/step")
async def step_turn():
    """Advance the game by one turn"""
    if not current_game:
        return {"error": "No active game"}
    
    current_game.advance_turn()
    
    # Process Tribe Queues & Updates
    queue_messages = []
    
    # Add general game events (attacks, deaths, etc)
    if hasattr(current_game, 'current_turn_log'):
        queue_messages.extend(current_game.current_turn_log)
        
    if current_game.tribe:
        # Process construction/training queues
        queue_messages.extend(current_game.tribe.process_queues())
        
        # Process turn updates (Decay, Culture)
        # Check if new year (every 4 turns, assuming season 0 is start of year)
        is_new_year = (current_game.climate.season == 0)
        update_msgs = current_game.tribe.process_turn_updates(is_new_year)
        queue_messages.extend(update_msgs)
    
    return {
        "status": "success",
        "turn": int(current_game.turn),
        "year": int(current_game.climate.year),
        "messages": queue_messages
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
                        "id": animal.id,
                        "type": "herbivore",
                        "species": animal.species,
                        "hp": f"{int(animal.combat_stats.current_hp)}/{int(animal.combat_stats.max_hp)}",
                        "stats": f"ATK {int(animal.combat_stats.attack)} | DEF {int(animal.combat_stats.defense)}"
                    })
        
        if current_game.predators:
            for pred in current_game.predators.predators:
                if int(pred.x) == x and int(pred.y) == y:
                    entities_here.append({
                        "id": pred.id,
                        "type": "predator",
                        "species": pred.species,
                        "hp": f"{int(pred.combat_stats.current_hp)}/{int(pred.combat_stats.max_hp)}",
                        "stats": f"ATK {int(pred.combat_stats.attack)} | DEF {int(pred.combat_stats.defense)}"
                    })
        
        # Get resources at this tile
        resources = current_game.resource_map.get((x, y), {})
        
        return {
            "terrain": biome_names.get(biome, "Unknown"),
            "vegetation": f"{veg*100:.1f}%",
            "temperature": f"{temp:.2f}",
            "moisture": f"{moisture:.2f}",
            "entities": entities_here,
            "resources": resources
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/game/saves")
async def list_saves():
    """List available save files"""
    files = glob.glob("saves/*.json")
    return {"saves": [os.path.basename(f) for f in files]}


@app.post("/game/save")
async def save_game(request: SaveGameRequest):
    """Save current game state"""
    if not current_game:
        return {"error": "No active game"}
    
    filename = request.filename
    if not filename.endswith(".json"):
        filename += ".json"
        
    filepath = os.path.join("saves", filename)
        
    try:
        SaveSystem.save_game(current_game, filepath)
        return {"status": "success", "message": f"Game saved to {filename}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/game/load")
async def load_game(request: LoadGameRequest):
    """Load game state"""
    global current_game
    
    filepath = os.path.join("saves", request.filename)
    if not os.path.exists(filepath):
        return {"error": "Save file not found"}
        
    try:
        current_game = SaveSystem.load_game(filepath)
        return {"status": "success", "message": f"Game loaded from {request.filename}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("Starting game server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
