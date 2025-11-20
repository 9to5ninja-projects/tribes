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
            'weather_intensity': self.weather_intensity
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
        
        # Game state
        self.turn = 0
        self.paused = True
        self.game_speed = 1  # Turns per second when running
        
        # Statistics tracking
        self.statistics = {
            'total_turns': 0,
            'total_births': 0,
            'total_deaths': 0,
            'extinctions': []
        }
    
    def initialize_world(self):
        """Generate new world from config"""
        print("=== WORLD GENERATION ===")
        print(f"Dimensions: {self.config.width}x{self.config.height}")
        print(f"Sea level: {self.config.sea_level}")
        print(f"Seed: {self.config.seed if self.config.seed else 'Random'}")
        
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
        self.predators = PredatorSystem(self.world, self.vegetation, self.animals)
        self.ecology = EventsEcologySystem(self.world, self.vegetation, self.animals, self.predators)

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
        self.ecology.spawn_scavengers(count=self.config.scavenger_population)
        self.ecology.spawn_avian_species(count=self.config.avian_population)
        self.ecology.spawn_aquatic_species(count=self.config.aquatic_population)
        
        # Apply event frequency modifiers
        self.ecology.disease_spawn_rate = self.config.disease_frequency
        self.ecology.disaster_spawn_rate = self.config.disaster_frequency
        
        self.turn = 0
        print("\n=== WORLD READY ===")
        self.print_status()
    
    def advance_turn(self):
        """Execute one turn of the simulation"""
        if not self.world:
            print("ERROR: World not initialized")
            return
        
        self.turn += 1
        self.statistics['total_turns'] += 1
        
        # Update all systems
        self.climate.advance_turn()
        self.vegetation.update(self.climate)
        self.animals.update(self.climate)
        self.predators.update(self.climate)
        self.ecology.update(self.climate)
        
        # Track statistics
        self._update_statistics()
    
    def _update_statistics(self):
        """Update game statistics"""
        # Check for extinctions
        herbivore_counts = self.animals.get_population_counts()
        predator_counts = self.predators.get_population_counts()
        
        for species, count in {**herbivore_counts, **predator_counts}.items():
            if count == 0 and species not in self.statistics['extinctions']:
                self.statistics['extinctions'].append(species)
                print(f"⚠️  {species.capitalize()} has gone EXTINCT!")
    
    def get_current_statistics(self):
        """Return current world statistics"""
        stats = {
            'turn': self.turn,
            'year': self.climate.year if self.climate else 0,
            'season': self.climate._season_name() if self.climate else 'N/A',
            'vegetation_coverage': 0,
            'populations': {},
            'events': {}
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
            ]
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
        
        # Restore game state
        game_state.turn = save_data['turn']
        game_state.statistics = save_data['statistics']
        
        print(f"✓ Game loaded successfully (Turn {game_state.turn})")
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
