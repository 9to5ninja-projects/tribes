import numpy as np
from enum import Enum
import uuid
import random

class UnitType(str, Enum):
    GATHERER = "gatherer"
    HUNTER = "hunter"
    CRAFTER = "crafter"
    SHAMAN = "shaman"

class StructureType(str, Enum):
    BONFIRE = "bonfire"
    HUT = "hut"
    WORKSHOP = "workshop"
    RESEARCH_WEAPON = "research_weapon"
    RESEARCH_ARMOR = "research_armor"
    IDOL = "idol"

class Structure:
    def __init__(self, x, y, structure_type=StructureType.BONFIRE):
        self.id = str(uuid.uuid4())
        self.x = int(x)
        self.y = int(y)
        self.type = structure_type
        
        # Stats
        self.hp = 100
        self.max_hp = 100
        
        # Bonfire specific stats
        if structure_type == StructureType.BONFIRE:
            self.hp = 20
            self.max_hp = 20
            self.decay_rate = 1 # HP loss per turn
        else:
            self.decay_rate = 0
            
        self.stationed_unit_id = None # ID of unit working here
        
        # Construction
        self.is_complete = False
        self.construction_turns_left = 0
        self.max_construction_turns = 0
        
    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "type": self.type,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "stationed_unit_id": self.stationed_unit_id,
            "is_complete": self.is_complete,
            "construction_turns_left": self.construction_turns_left,
            "max_construction_turns": self.max_construction_turns
        }

class Unit:
    def __init__(self, x, y, unit_type=UnitType.GATHERER):
        self.id = str(uuid.uuid4())
        self.x = int(x)
        self.y = int(y)
        self.type = unit_type
        
        # Stats
        self.hp = 10
        self.max_hp = 10
        self.energy = 100
        self.max_energy = 100
        self.hunger = 0
        self.max_hunger = 100
        
        # Identity
        self.name = f"{unit_type.capitalize()} {str(uuid.uuid4())[:4]}"
        
        # Capabilities
        self.movement_range = 3 if unit_type == UnitType.HUNTER else 2
        self.inventory = {}  # Personal carry
        self.action_points = 1 # Actions per turn
        
        # Turn State
        self.has_moved = False
        self.has_acted = False
        self.is_working = False # If true, unit is stationed at a structure
        
    def move(self, dx, dy):
        if self.is_working:
            return # Cannot move while working
        self.x += dx
        self.y += dy
        self.has_moved = True
        self.energy = max(0, self.energy - 1)
        
    def reset_turn(self):
        self.has_moved = False
        self.has_acted = False
        # Note: is_working persists across turns until manually stopped
        
    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "type": self.type,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "energy": self.energy,
            "max_energy": self.max_energy,
            "name": self.name,
            "movement_range": self.movement_range,
            "has_moved": self.has_moved,
            "has_acted": self.has_acted,
            "is_working": self.is_working
        }

class Tribe:
    def __init__(self, world_width, world_height, fog_of_war=True):
        self.name = "Player Tribe"
        self.units = []
        self.structures = []
        self.fog_of_war = fog_of_war
        self.stockpile = {
            "wood": 0,
            "stone": 0,
            "fiber": 0,
            "food": 50, # Start with some food
            "clay": 0,
            "flint": 0
        }
        self.tech_tree = {
            "fire": False,
            "tools": False,
            "weaving": False,
            "pottery": False
        }
        
        # Research / Upgrades
        self.research_levels = {
            "weapons": 0,
            "armor": 0
        }
        
        # Culture
        self.culture = 0
        self.culture_rate = 0
        
        # Training Queue: List of dicts {type, turns_left, x, y}
        self.training_queue = []
        
        # Population History
        self.population_history = {
            'total': [],
            'gatherer': [],
            'hunter': [],
            'crafter': [],
            'shaman': []
        }
        
        # Fog of War: False = hidden, True = revealed
        if self.fog_of_war:
            self.fog_map = np.zeros((world_height, world_width), dtype=bool)
        else:
            self.fog_map = np.ones((world_height, world_width), dtype=bool)
        
    def add_unit(self, unit):
        self.units.append(unit)
        self.reveal_area(unit.x, unit.y, radius=5)

    def add_structure(self, structure):
        self.structures.append(structure)
        self.reveal_area(structure.x, structure.y, radius=3)

    def calculate_culture_income(self):
        """Calculate yearly culture income"""
        income = 0
        
        # Units
        for unit in self.units:
            if unit.hp > 0:
                income += 1
                if unit.type == UnitType.SHAMAN:
                    income += 1 # Shamans give +2 total
        
        # Structures
        for structure in self.structures:
            if structure.is_complete and structure.hp > 0:
                if structure.type == StructureType.BONFIRE:
                    income += 1
                    
        return income

    def process_turn_updates(self, is_new_year=False):
        """Process turn-based updates for tribe (decay, culture, etc)"""
        messages = []
        
        # Track Population History
        counts = {
            'gatherer': 0,
            'hunter': 0,
            'crafter': 0,
            'shaman': 0
        }
        for unit in self.units:
            if unit.type in counts:
                counts[unit.type] += 1
        
        self.population_history['total'].append(len(self.units))
        for type_name, count in counts.items():
            self.population_history[type_name].append(count)
        
        # Structure Decay
        dead_structures = []
        for structure in self.structures:
            if structure.is_complete and structure.decay_rate > 0:
                structure.hp -= structure.decay_rate
                if structure.hp <= 0:
                    dead_structures.append(structure)
                    messages.append(f"{structure.type.capitalize()} has burned out.")
        
        for s in dead_structures:
            self.structures.remove(s)
            
        # Culture Calculation (Yearly)
        if is_new_year:
            income = self.calculate_culture_income()
            self.culture += income
            self.culture_rate = income # Store for UI
            messages.append(f"Culture generated: +{income} (Total: {self.culture})")
            
        return messages

    def process_queues(self):
        """Advance training and construction queues"""
        messages = []
        
        # Process Training
        completed_training = []
        for item in self.training_queue:
            item["turns_left"] -= 1
            if item["turns_left"] <= 0:
                completed_training.append(item)
                
        for item in completed_training:
            self.training_queue.remove(item)
            new_unit = Unit(item["x"], item["y"], item["type"])
            self.add_unit(new_unit)
            messages.append(f"Training complete: {item['type'].capitalize()} joined the tribe.")
            
        # Process Construction
        for structure in self.structures:
            if not structure.is_complete and structure.construction_turns_left > 0:
                structure.construction_turns_left -= 1
                if structure.construction_turns_left <= 0:
                    structure.is_complete = True
                    messages.append(f"Construction complete: {structure.type.capitalize()}.")
                    
        return messages

    def reveal_area(self, x, y, radius):
        """Reveal area around a point (Radial)"""
        if not self.fog_of_war:
            return # Map is already fully revealed

        h, w = self.fog_map.shape
        
        # Define bounding box to limit iteration
        y_min = max(0, y - radius)
        y_max = min(h, y + radius + 1)
        x_min = max(0, x - radius)
        x_max = min(w, x + radius + 1)
        
        # Create coordinate grids for the bounding box
        # Adjust grid coordinates to be relative to the center (x, y)
        # We need the absolute coordinates to match the slice
        Y, X = np.ogrid[y_min:y_max, x_min:x_max]
        
        # Calculate squared distance from center
        dist_sq = (X - x)**2 + (Y - y)**2
        
        # Create mask for points within radius
        mask = dist_sq <= radius**2
        
        # Apply mask to fog map slice
        # Note: We must use the same slice to ensure we modify the original array
        self.fog_map[y_min:y_max, x_min:x_max][mask] = True
        
    def update_visibility(self):
        """Update visibility based on all unit positions"""
        # Could reset fog here if we want "shroud" vs "fog"
        # For now, once revealed, always revealed
        for unit in self.units:
            self.reveal_area(unit.x, unit.y, radius=4)
        for structure in self.structures:
            self.reveal_area(structure.x, structure.y, radius=3)

    def consume_food(self):
        """Consume food for all units based on class"""
        consumption, reduction = self.get_expected_food_consumption()
        
        if self.stockpile["food"] >= consumption:
            self.stockpile["food"] -= consumption
            return True, f"Tribe consumed {consumption} food (Base: {consumption + reduction}, Reduced by Huts: {reduction})."
        else:
            # Starvation logic
            deficit = consumption - self.stockpile["food"]
            self.stockpile["food"] = 0
            
            # Damage units based on deficit?
            # For now, just log it and maybe reduce health of random units
            starving_units = random.sample(self.units, min(len(self.units), deficit))
            for unit in starving_units:
                unit.hp -= 5 # Take damage from starvation
                
            return False, f"Starvation! {deficit} units suffered."

    def get_expected_food_consumption(self):
        """Calculate expected food consumption for next turn"""
        consumption_rates = {
            UnitType.GATHERER: 1,
            UnitType.HUNTER: 2,
            UnitType.CRAFTER: 3,
            UnitType.SHAMAN: 4
        }
        
        base_consumption = 0
        for unit in self.units:
            base_consumption += consumption_rates.get(unit.type, 1)
        
        # Huts reduce consumption (only completed huts)
        huts = [s for s in self.structures if s.type == StructureType.HUT and s.is_complete]
        reduction = len(huts) * 3
        
        consumption = max(0, base_consumption - reduction)
        return consumption, reduction

    def to_dict(self):
        consumption, reduction = self.get_expected_food_consumption()
        return {
            "name": self.name,
            "stockpile": self.stockpile,
            "culture": self.culture,
            "culture_rate": self.culture_rate,
            "expected_food_consumption": consumption,
            "units": [u.to_dict() for u in self.units],
            "structures": [s.to_dict() for s in self.structures],
            "tech_tree": self.tech_tree,
            "research_levels": self.research_levels,
            "training_queue": self.training_queue,
            "fog_map": self.fog_map.tolist() # Send as list of lists
        }
