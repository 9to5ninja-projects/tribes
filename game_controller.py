import numpy as np
import json
import pickle
from datetime import datetime
from terrain_generator import WorldGenerator
from climate_engine import ClimateEngine
from vegetation_system import VegetationSystem
from animal_system import AnimalSystem
from predator_system import PredatorSystem
from events_ecology import EventsEcologySystem
from balance_config import apply_balance_to_game, SPAWN_CONFIG
from tribe_system import Tribe, Unit, UnitType, StructureType


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


class WorldConfig:
    """Configuration for world generation"""
    def __init__(self):
        # Terrain parameters
        self.width = 150
        self.height = 100
        self.sea_level = 0.42
        self.seed = None  # None = random
        
        # Initial population sizes
        self.herbivore_population = 100  # per species
        self.predator_population = 15    # per species
        self.scavenger_population = 40
        self.avian_population = 100
        self.aquatic_population = 150
        
        # Vegetation parameters
        self.vegetation_density_multiplier = 1.0  # 0.5 = sparse, 2.0 = lush
        
        # Event frequency
        self.disease_frequency = 0.02  # Base chance per turn
        self.disaster_frequency = 0.01
        
        # Climate intensity
        self.seasonal_variation = 1.0  # How extreme seasons are
        self.weather_intensity = 1.0   # Storm/drought severity
        
        # Game Rules
        self.fog_of_war = True
    
    def to_dict(self):
        """Convert to dictionary for saving"""
        return {
            'width': self.width,
            'height': self.height,
            'sea_level': self.sea_level,
            'seed': self.seed,
            'herbivore_population': self.herbivore_population,
            'predator_population': self.predator_population,
            'scavenger_population': self.scavenger_population,
            'avian_population': self.avian_population,
            'aquatic_population': self.aquatic_population,
            'vegetation_density_multiplier': self.vegetation_density_multiplier,
            'disease_frequency': self.disease_frequency,
            'disaster_frequency': self.disaster_frequency,
            'seasonal_variation': self.seasonal_variation,
            'weather_intensity': self.weather_intensity,
            'fog_of_war': self.fog_of_war
        }
    
    @classmethod
    def from_dict(cls, data):
        """Load from dictionary"""
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


class GameState:
    """Complete game state - everything needed to save/load"""
    def __init__(self, config=None):
        self.config = config or WorldConfig()
        
        # Core systems (will be initialized)
        self.world = None
        self.climate = None
        self.vegetation = None
        self.animals = None
        self.predators = None
        self.ecology = None
        self.tribe = None  # The player's tribe
        self.resource_map = {} # (x,y) -> {resource_type: amount}
        
        # Game state
        self.turn = 0
        self.paused = True
        self.game_speed = 1  # Turns per second when running
        
        # Statistics tracking
        self.statistics = {
            'total_turns': 0,
            'total_births': 0,
            'total_deaths': 0,
            'extinctions': [],
            'interaction_log': [], # Detailed log of interactions
            'death_causes': {},    # Aggregated death causes
            'food_chain': {}       # Aggregated predation stats: {predator: {prey: count}}
        }
        
        # Temporary log for the current turn (sent to frontend)
        self.current_turn_log = []
    
    def initialize_world(self, starting_units=None, preferred_biome=None, fog_of_war=True):
        """Generate new world from config"""
        print("=== WORLD GENERATION ===")
        print(f"Dimensions: {self.config.width}x{self.config.height}")
        print(f"Sea level: {self.config.sea_level}")
        print(f"Seed: {self.config.seed if self.config.seed else 'Random'}")
        print(f"Fog of War: {fog_of_war}")
        
        self.config.fog_of_war = fog_of_war
        
        # Generate terrain
        self.world = WorldGenerator(
            width=self.config.width,
            height=self.config.height,
            seed=self.config.seed
        )
        self.world.generate_world(sea_level=self.config.sea_level)
        
        # Initialize climate
        self.climate = ClimateEngine(self.world)
        
        # Initialize vegetation
        self.vegetation = VegetationSystem(self.world)
        
        # Apply vegetation density multiplier
        if self.config.vegetation_density_multiplier != 1.0:
            self.vegetation.density *= self.config.vegetation_density_multiplier
            self.vegetation.density = np.clip(self.vegetation.density, 0, 1)
        
        # Establish vegetation (longer period)
        print(f"\nEstablishing ecosystem ({SPAWN_CONFIG['vegetation_establishment_years']} years)...")
        for _ in range(SPAWN_CONFIG['vegetation_establishment_years'] * 4):
            self.climate.advance_turn()
            self.vegetation.update(self.climate)
        
        # Initialize animal systems (but don't spawn yet)
        self.animals = AnimalSystem(self.world, self.vegetation)
        self.animals.set_logger(self.log_interaction)
        
        self.predators = PredatorSystem(self.world, self.vegetation, self.animals)
        self.predators.set_logger(self.log_interaction)
        
        self.ecology = EventsEcologySystem(self.world, self.vegetation, self.animals, self.predators)
        
        # Link ecology back to animal systems for insect consumption
        self.animals.ecology = self.ecology
        self.predators.ecology = self.ecology

        # Apply balance configurations
        print("\nApplying ecosystem balance...")
        apply_balance_to_game(self)
        
        # Spawn animals
        print("\nSpawning wildlife...")
        self.animals.spawn_initial_populations(
            population_per_species=self.config.herbivore_population
        )
        
        # Let herbivores establish (longer period)
        print(f"Herbivores establishing ({SPAWN_CONFIG['herbivore_establishment_years']} years)...")
        for _ in range(SPAWN_CONFIG['herbivore_establishment_years'] * 4):
            self.climate.advance_turn()
            self.vegetation.update(self.climate)
            self.animals.update(self.climate)
        
        # Check herbivore survival before spawning predators
        herbivore_count = len(self.animals.herbivores)
        print(f"Herbivore population check: {herbivore_count}")
        
        if herbivore_count < self.config.herbivore_population * 0.3:
            print("⚠️  WARNING: Low herbivore survival. Ecosystem may be unstable.")
        
        # Spawn predators (with delay)
        print(f"\nSpawning predators (after {SPAWN_CONFIG['predator_delay_years']} year delay)...")
        self.predators.spawn_initial_populations(
            population_per_species=self.config.predator_population
        )
        
        # Stabilize predator-prey
        print(f"Ecosystem stabilizing ({SPAWN_CONFIG['predator_delay_years']} years)...")
        for _ in range(SPAWN_CONFIG['predator_delay_years'] * 4):
            self.climate.advance_turn()
            self.vegetation.update(self.climate)
            self.animals.update(self.climate)
            self.predators.update(self.climate)
        
        # Add full ecology populations
        print("\nInitializing complete ecology...")
        self.ecology = EventsEcologySystem(
            self.world, self.vegetation, self.animals, self.predators
        )
        self.ecology.set_logger(self.log_interaction)
        
        # Re-link ecology back to animal systems
        self.animals.ecology = self.ecology
        self.predators.ecology = self.ecology
        
        self.ecology.spawn_scavengers(count=self.config.scavenger_population)
        self.ecology.spawn_avian_species(count=self.config.avian_population)
        self.ecology.spawn_aquatic_species(count=self.config.aquatic_population)
        
        # Apply event frequency modifiers
        self.ecology.disease_spawn_rate = self.config.disease_frequency
        self.ecology.disaster_spawn_rate = self.config.disaster_frequency
        
        # Generate Resources
        self._generate_resources()

        # Initialize Tribe
        print("\nInitializing Tribe...")
        self.tribe = Tribe(self.config.width, self.config.height, fog_of_war=self.config.fog_of_war)
        
        # Find a valid start location (land, preferably forest/grassland)
        start_x, start_y = self._find_start_location(preferred_biome)
        print(f"Tribe starting at {start_x}, {start_y}")
        
        # Spawn starting units
        if starting_units:
            print(f"Spawning custom units: {starting_units}")
            for unit_type_str, count in starting_units.items():
                try:
                    # Ensure valid unit type
                    u_type = UnitType(unit_type_str.lower())
                    for _ in range(count):
                        self.tribe.add_unit(Unit(start_x, start_y, u_type))
                except ValueError:
                    print(f"Warning: Invalid unit type '{unit_type_str}' requested.")
        else:
            self.tribe.add_unit(Unit(start_x, start_y, UnitType.GATHERER))
            self.tribe.add_unit(Unit(start_x, start_y, UnitType.GATHERER))
            self.tribe.add_unit(Unit(start_x, start_y, UnitType.HUNTER))
        
        # Initialize History for Turn 0
        if self.ecology:
            self.ecology.scavenger_history.append(len(self.ecology.scavengers))
            self.ecology.avian_history.append(len(self.ecology.avian_creatures))
            self.ecology.aquatic_history.append(len(self.ecology.aquatic_creatures))
            
        if self.tribe:
            counts = {'gatherer': 0, 'hunter': 0, 'crafter': 0, 'shaman': 0}
            for unit in self.tribe.units:
                if unit.type in counts:
                    counts[unit.type] += 1
            self.tribe.population_history['total'].append(len(self.tribe.units))
            for type_name, count in counts.items():
                self.tribe.population_history[type_name].append(count)

        self.turn = 0
        print("\n=== WORLD READY ===")
        self.print_status()
    
    def _find_start_location(self, preferred_biome=None):
        """Find a suitable starting location for the tribe"""
        # Try to find a spot with vegetation and not in ocean
        attempts = 0
        
        # Map biome names to IDs if string provided
        biome_map = {
            "grassland": [5],
            "forest": [7],
            "rainforest": [6],
            "savanna": [4],
            "desert": [3],
            "tundra": [9],
            "snow": [10],
            "beach": [2],
            "mountain": [11]
        }
        
        target_biomes = [4, 5, 6, 7] # Default: Savanna, Grassland, Rainforest, Temperate Forest
        
        if preferred_biome and preferred_biome.lower() in biome_map:
            target_biomes = biome_map[preferred_biome.lower()]
            print(f"Searching for start location in {preferred_biome}...")
        
        while attempts < 200:
            x = np.random.randint(0, self.config.width)
            y = np.random.randint(0, self.config.height)
            
            # Check if land (elevation > sea_level)
            if self.world.elevation[y, x] > self.config.sea_level:
                # Check biome
                biome = self.world.biomes[y, x]
                if biome in target_biomes:
                    return x, y
            attempts += 1
            
        # Fallback to default biomes if preferred not found
        if preferred_biome:
            print(f"Could not find {preferred_biome}, falling back to default biomes.")
            return self._find_start_location(None)
            
        # Fallback to center
        return self.config.width // 2, self.config.height // 2

    def _generate_resources(self):
        """Populate the world with resources based on terrain"""
        print("Generating natural resources...")
        self.resource_map = {}
        
        for y in range(self.config.height):
            for x in range(self.config.width):
                biome = self.world.biomes[y, x]
                veg = self.vegetation.density[y, x]
                
                resources = {}
                
                # Wood/Fiber from vegetation (Forests/Grasslands)
                if veg > 0.1:
                    # Wood primarily in forests (biomes 6, 7, 8)
                    if biome in [6, 7, 8]:
                        resources['wood'] = int(veg * 200)
                        resources['fiber'] = int(veg * 50)
                        if np.random.random() < 0.05:
                            resources['resin'] = np.random.randint(10, 30)
                    # Fiber primarily in grasslands/savanna (biomes 4, 5)
                    elif biome in [4, 5]:
                        resources['fiber'] = int(veg * 100)
                        if veg > 0.5:
                            resources['wood'] = int(veg * 20) # Sparse trees
                
                # Stone/Clay/Ore from Mountains/Hills
                if biome == 11: # Mountain
                    resources['stone'] = np.random.randint(500, 1000)
                    if np.random.random() < 0.15:
                        resources['clay'] = np.random.randint(100, 300)
                    if np.random.random() < 0.05:
                        resources['copper_ore'] = np.random.randint(50, 150)
                    if np.random.random() < 0.2:
                        resources['flint'] = np.random.randint(20, 50)
                
                # Stone in Desert/Tundra
                elif biome in [3, 9]:
                    resources['stone'] = np.random.randint(100, 400)
                    if np.random.random() < 0.1:
                        resources['flint'] = np.random.randint(10, 30)
                
                # Clay near water (Beach/River banks)
                if biome == 2: # Beach
                    if np.random.random() < 0.2:
                        resources['clay'] = np.random.randint(50, 150)
                    resources['sand'] = 999
                
                if resources:
                    self.resource_map[(x,y)] = resources

    def advance_turn(self):
        """Execute one turn of the simulation"""
        if not self.world:
            print("ERROR: World not initialized")
            return
        
        self.turn += 1
        self.statistics['total_turns'] += 1
        self.current_turn_log = [] # Clear log for new turn
        
        # Update all systems
        self.climate.advance_turn()
        
        # New Year - Food Consumption
        if self.climate.season == 0 and self.tribe:
            success, msg = self.tribe.consume_food()
            self.add_event_log(msg)
            if not success:
                print(f"⚠️ {msg}")

        self.vegetation.update(self.climate)
        
        # Get tribe units for interaction
        tribe_units = self.tribe.units if self.tribe else []
        predators_list = self.predators.predators if self.predators else []
        
        self.animals.update(self.climate, predators_list=predators_list, tribe_units=tribe_units)
        self.predators.update(self.climate, tribe_units=tribe_units)
        self.ecology.update(self.climate)
        
        # Cleanup dead units
        if self.tribe:
            dead_units = [u for u in self.tribe.units if u.hp <= 0]
            for u in dead_units:
                print(f"💀 Unit {u.name} has died!")
                self.add_event_log(f"Unit {u.name} was killed.")
            self.tribe.units = [u for u in self.tribe.units if u.hp > 0]
        
        # Update Tribe visibility
        if self.tribe:
            self.tribe.update_visibility()
            
            # Handle Structures (Bonfires)
            # Bonfires consume 1 wood per turn and restore energy to nearby units
            for structure in self.tribe.structures:
                if structure.type == StructureType.BONFIRE:
                    if self.tribe.stockpile.get("wood", 0) >= 1:
                        self.tribe.stockpile["wood"] -= 1
                        
                        # Restore energy to units in range 5
                        for unit in self.tribe.units:
                            dist = abs(unit.x - structure.x) + abs(unit.y - structure.y)
                            if dist <= 5:
                                unit.energy = min(100, unit.energy + 10)

            # Reset unit actions for next turn
            for unit in self.tribe.units:
                unit.reset_turn()
        
        # Track statistics
        self._update_statistics()
    
    def get_population_history(self):
        """Return historical population data for graphs"""
        history = {
            'herbivores': {},
            'predators': {},
            'scavengers': [],
            'avian': [],
            'aquatic': [],
            'tribe': {}
        }
        
        if self.animals:
            history['herbivores'] = self.animals.population_history
            
        if self.predators:
            history['predators'] = self.predators.population_history
            
        if self.ecology:
            history['scavengers'] = self.ecology.scavenger_history
            history['avian'] = self.ecology.avian_history
            history['aquatic'] = self.ecology.aquatic_history
            
        if self.tribe:
            history['tribe'] = self.tribe.population_history
            
        return history

    def log_interaction(self, type, actor, target=None, details=None):
        """Log an interaction between entities"""
        # Aggregation for stats
        if type == 'predation':
            predator = actor
            prey = target
            if predator not in self.statistics['food_chain']:
                self.statistics['food_chain'][predator] = {}
            if prey not in self.statistics['food_chain'][predator]:
                self.statistics['food_chain'][predator][prey] = 0
            self.statistics['food_chain'][predator][prey] += 1
            
        elif type == 'death':
            cause = details
            species = actor
            if species not in self.statistics['death_causes']:
                self.statistics['death_causes'][species] = {}
            if cause not in self.statistics['death_causes'][species]:
                self.statistics['death_causes'][species][cause] = 0
            self.statistics['death_causes'][species][cause] += 1
            self.statistics['total_deaths'] += 1
            
        elif type == 'attack':
            # Log attacks on units or by units
            # actor = attacker species, target = target name, details = damage info
            msg = f"{actor.capitalize()} attacked {target}! {details}"
            self.add_event_log(msg)
            print(f"⚔️ {msg}")
            
        elif type == 'kill':
            msg = f"{actor.capitalize()} killed {target}!"
            self.add_event_log(msg)
            print(f"💀 {msg}")

    def add_event_log(self, message):
        """Add a message to the event log"""
        if 'event_log' not in self.statistics:
            self.statistics['event_log'] = []
        
        timestamp = f"Y{self.climate.year} {self.climate._season_name()}"
        self.statistics['event_log'].append({'turn': self.turn, 'time': timestamp, 'msg': message})
        
        # Add to current turn log for immediate frontend display
        self.current_turn_log.append(message)
        
        # Keep log size manageable
        if len(self.statistics['event_log']) > 50:
            self.statistics['event_log'].pop(0)

    def _update_statistics(self):
        """Update game statistics"""
        # Check for extinctions
        herbivore_counts = self.animals.get_population_counts()
        predator_counts = self.predators.get_population_counts()
        
        for species, count in {**herbivore_counts, **predator_counts}.items():
            if count == 0 and species not in self.statistics['extinctions']:
                self.statistics['extinctions'].append(species)
                msg = f"⚠️ {species.capitalize()} has gone EXTINCT!"
                print(msg)
                self.add_event_log(msg)
        
        # Check for disasters/diseases (simplified check)
        if self.ecology:
            # Pull events from ecology system
            recent_events = self.ecology.get_recent_events()
            for event in recent_events:
                self.add_event_log(event)
    
    def get_current_statistics(self):
        """Return current world statistics"""
        stats = {
            'turn': self.turn,
            'year': self.climate.year if self.climate else 0,
            'season': self.climate._season_name() if self.climate else 'N/A',
            'vegetation_coverage': 0,
            'populations': {},
            'events': {},
            'food_chain': self.statistics.get('food_chain', {}),
            'death_causes': self.statistics.get('death_causes', {})
        }
        
        if self.vegetation:
            stats['vegetation_coverage'] = (
                np.sum(self.vegetation.density > 0.1) / self.vegetation.density.size * 100
            )
        
        if self.animals:
            stats['populations']['herbivores'] = self.animals.get_population_counts()
        
        if self.predators:
            stats['populations']['predators'] = self.predators.get_population_counts()
        
        if self.ecology:
            ecology_stats = self.ecology.get_statistics()
            stats['populations']['scavengers'] = ecology_stats['scavengers']
            stats['populations']['avian'] = ecology_stats['avian']
            stats['populations']['aquatic'] = ecology_stats['aquatic']
            stats['populations']['insects'] = ecology_stats['insects']
            stats['events'] = {
                'active_diseases': ecology_stats['active_diseases'],
                'active_disasters': ecology_stats['active_disasters'],
                'disease_deaths': ecology_stats['disease_deaths'],
                'disaster_deaths': ecology_stats['disaster_deaths']
            }
        
        return stats
    
    def print_status(self):
        """Print current game status to console"""
        stats = self.get_current_statistics()
        print(f"\n{'='*50}")
        print(f"Turn {stats['turn']} | Year {stats['year']} | {stats['season']}")
        print(f"Vegetation Coverage: {stats['vegetation_coverage']:.1f}%")
        
        if stats['populations'].get('herbivores'):
            print("\nHerbivores:")
            for species, count in stats['populations']['herbivores'].items():
                print(f"  {species.capitalize()}: {count}")
        
        if stats['populations'].get('predators'):
            print("\nPredators:")
            for species, count in stats['populations']['predators'].items():
                print(f"  {species.capitalize()}: {count}")
        
        print(f"\nScavengers: {stats['populations'].get('scavengers', 0)}")
        print(f"Avian: {stats['populations'].get('avian', 0)}")
        print(f"Aquatic: {stats['populations'].get('aquatic', 0)}")
        
        if stats['events']:
            print(f"\nActive Events:")
            print(f"  Diseases: {stats['events']['active_diseases']}")
            print(f"  Disasters: {stats['events']['active_disasters']}")
        
        print(f"{'='*50}\n")


class SaveSystem:
    """Handle saving and loading game states"""
    
    @staticmethod
    def save_game(game_state, filepath):
        """Save complete game state to file"""
        print(f"Saving game to {filepath}...")
        
        save_data = {
            'version': '0.3.0',
            'timestamp': datetime.now().isoformat(),
            'config': game_state.config.to_dict(),
            'turn': game_state.turn,
            'statistics': game_state.statistics,
            
            # Serialize numpy arrays and complex objects
            'world_elevation': game_state.world.elevation.tolist(),
            'world_biomes': game_state.world.biomes.tolist(),
            'base_temperature': game_state.climate.base_temperature.tolist(),
            'base_moisture': game_state.climate.base_moisture.tolist(),
            'current_temperature': game_state.world.temperature.tolist(),
            'current_moisture': game_state.world.moisture.tolist(),
            'vegetation_density': game_state.vegetation.density.tolist(),
            
            'climate_turn': game_state.climate.current_turn,
            'climate_season': game_state.climate.season,
            'climate_year': game_state.climate.year,
            
            # Animals (simplified - just counts and positions)
            'herbivores': [
                {
                    'species': h.species,
                    'x': h.x, 'y': h.y,
                    'energy': h.energy,
                    'age': h.age
                } for h in game_state.animals.herbivores
            ],
            'predators': [
                {
                    'species': p.species,
                    'x': p.x, 'y': p.y,
                    'energy': p.energy,
                    'age': p.age
                } for p in game_state.predators.predators
            ],
            'scavengers': [
                {
                    'x': s.x, 'y': s.y,
                    'energy': s.energy,
                    'age': s.age
                } for s in game_state.ecology.scavengers
            ],
            'avian': [
                {
                    'species': a.species,
                    'x': a.x, 'y': a.y,
                    'energy': a.energy,
                    'age': a.age
                } for a in game_state.ecology.avian_creatures
            ],
            'aquatic': [
                {
                    'species': a.species,
                    'x': a.x, 'y': a.y,
                    'energy': a.energy,
                    'age': a.age
                } for a in game_state.ecology.aquatic_creatures
            ],
            
            # Tribe
            'tribe': game_state.tribe.to_dict() if game_state.tribe else None,
            
            # History
            'history_scavengers': game_state.ecology.scavenger_history,
            'history_avian': game_state.ecology.avian_history,
            'history_aquatic': game_state.ecology.aquatic_history,
            'history_tribe': game_state.tribe.population_history if game_state.tribe else {},
            'history_herbivores': game_state.animals.population_history if game_state.animals else {},
            'history_predators': game_state.predators.population_history if game_state.predators else {}
        }
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2, cls=NumpyEncoder)
        
        print(f"✓ Game saved successfully")
    
    @staticmethod
    def load_game(filepath):
        """Load game state from file"""
        print(f"Loading game from {filepath}...")
        
        with open(filepath, 'r') as f:
            save_data = json.load(f)
        
        print(f"Save version: {save_data['version']}")
        print(f"Saved on: {save_data['timestamp']}")
        
        # Create new game state
        config = WorldConfig.from_dict(save_data['config'])
        game_state = GameState(config)
        
        # Restore world
        game_state.world = WorldGenerator(
            width=config.width,
            height=config.height,
            seed=config.seed
        )
        game_state.world.elevation = np.array(save_data['world_elevation'])
        game_state.world.biomes = np.array(save_data['world_biomes'])
        game_state.world.temperature = np.array(save_data['current_temperature'])
        game_state.world.moisture = np.array(save_data['current_moisture'])
        
        # Restore climate
        game_state.climate = ClimateEngine(game_state.world)
        game_state.climate.base_temperature = np.array(save_data['base_temperature'])
        game_state.climate.base_moisture = np.array(save_data['base_moisture'])
        game_state.climate.current_turn = save_data['climate_turn']
        game_state.climate.season = save_data['climate_season']
        game_state.climate.year = save_data['climate_year']
        
        # Restore vegetation
        game_state.vegetation = VegetationSystem(game_state.world)
        game_state.vegetation.density = np.array(save_data['vegetation_density'])
        
        # Restore animals
        game_state.animals = AnimalSystem(game_state.world, game_state.vegetation)
        game_state.animals.herbivores = []
        for h_data in save_data['herbivores']:
            from animal_system import Animal
            h = Animal(h_data['x'], h_data['y'], h_data['species'])
            h.energy = h_data['energy']
            h.age = h_data['age']
            game_state.animals.herbivores.append(h)
        
        # Restore predators
        game_state.predators = PredatorSystem(
            game_state.world, game_state.vegetation, game_state.animals
        )
        game_state.predators.predators = []
        for p_data in save_data['predators']:
            from predator_system import Predator
            p = Predator(p_data['x'], p_data['y'], p_data['species'])
            p.energy = p_data['energy']
            p.age = p_data['age']
            game_state.predators.predators.append(p)
        
        # Restore ecology
        game_state.ecology = EventsEcologySystem(
            game_state.world, game_state.vegetation, 
            game_state.animals, game_state.predators
        )
        game_state.ecology.set_logger(game_state.log_interaction)
        
        for s_data in save_data['scavengers']:
            from events_ecology import Scavenger
            s = Scavenger(s_data['x'], s_data['y'], 'scavenger')
            s.energy = s_data['energy']
            s.age = s_data['age']
            game_state.ecology.scavengers.append(s)
        
        for a_data in save_data['avian']:
            from events_ecology import AvianCreature
            a = AvianCreature(a_data['x'], a_data['y'], a_data['species'])
            a.energy = a_data['energy']
            a.age = a_data['age']
            game_state.ecology.avian_creatures.append(a)
        
        for aq_data in save_data['aquatic']:
            from events_ecology import AquaticCreature
            aq = AquaticCreature(aq_data['x'], aq_data['y'], aq_data['species'])
            aq.energy = aq_data['energy']
            aq.age = aq_data['age']
            game_state.ecology.aquatic_creatures.append(aq)
            
        # Restore Ecology History
        if 'history_scavengers' in save_data:
            game_state.ecology.scavenger_history = save_data['history_scavengers']
        if 'history_avian' in save_data:
            game_state.ecology.avian_history = save_data['history_avian']
        if 'history_aquatic' in save_data:
            game_state.ecology.aquatic_history = save_data['history_aquatic']
            
        # Restore Animal History
        if 'history_herbivores' in save_data and game_state.animals:
            game_state.animals.population_history = save_data['history_herbivores']
            
        if 'history_predators' in save_data and game_state.predators:
            game_state.predators.population_history = save_data['history_predators']
        
        # Restore Tribe
        if 'tribe' in save_data and save_data['tribe']:
            from tribe_system import Tribe, Unit, Structure, UnitType, StructureType
            t_data = save_data['tribe']
            game_state.tribe = Tribe(config.width, config.height)
            game_state.tribe.name = t_data['name']
            game_state.tribe.stockpile = t_data['stockpile']
            game_state.tribe.culture = t_data.get('culture', 0)
            game_state.tribe.culture_rate = t_data.get('culture_rate', 0)
            game_state.tribe.tech_tree = t_data['tech_tree']
            game_state.tribe.research_levels = t_data.get('research_levels', {})
            game_state.tribe.training_queue = t_data.get('training_queue', [])
            
            # Restore Units
            for u_data in t_data['units']:
                u = Unit(u_data['x'], u_data['y'], UnitType(u_data['type']))
                u.id = u_data['id']
                u.hp = u_data['hp']
                u.max_hp = u_data['max_hp']
                u.energy = u_data['energy']
                u.max_energy = u_data['max_energy']
                u.name = u_data['name']
                u.has_moved = u_data['has_moved']
                u.has_acted = u_data['has_acted']
                u.is_working = u_data.get('is_working', False)
                game_state.tribe.units.append(u)
                
            # Restore Structures
            for s_data in t_data['structures']:
                s = Structure(s_data['x'], s_data['y'], StructureType(s_data['type']))
                s.id = s_data['id']
                s.hp = s_data['hp']
                s.max_hp = s_data['max_hp']
                s.stationed_unit_id = s_data['stationed_unit_id']
                s.is_complete = s_data['is_complete']
                s.construction_turns_left = s_data['construction_turns_left']
                s.max_construction_turns = s_data['max_construction_turns']
                game_state.tribe.structures.append(s)
            
            # Restore Fog
            if 'fog_map' in t_data:
                game_state.tribe.fog_map = np.array(t_data['fog_map'])
            else:
                game_state.tribe.update_visibility()
                
            # Restore Tribe History
            if 'history_tribe' in save_data:
                game_state.tribe.population_history = save_data['history_tribe']
        
        # Restore game state
        game_state.turn = save_data['turn']
        game_state.statistics = save_data['statistics']
        
        return game_state


# Simple CLI test
if __name__ == "__main__":
    import sys
    
    # Create game with default config
    config = WorldConfig()
    config.width = 100
    config.height = 60
    config.seed = 123
    
    game = GameState(config)
    game.initialize_world()
    
    # Run for a few turns
    for i in range(10):
        print(f"\n>>> Advancing to turn {game.turn + 1}...")
        game.advance_turn()
        if i % 4 == 3:  # Every year
            game.print_status()
    
    # Test save
    SaveSystem.save_game(game, 'test_save.json')
    
    # Test load
    loaded_game = SaveSystem.load_game('test_save.json')
    loaded_game.print_status()
    
    print("\n✓ Game controller and save system working!")
