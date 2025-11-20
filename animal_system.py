import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

class Animal:
    """Base class for all animal species"""
    def __init__(self, x, y, species_name):
        self.x = x
        self.y = y
        self.species = species_name
        self.energy = 1.0  # 0.0 = death, 1.0 = full health
        self.age = 0
        self.reproductive_cooldown = 0
    
    def move(self, dx, dy, world_width, world_height):
        """Move with wrapping at world edges"""
        self.x = (self.x + dx) % world_width
        self.y = (self.y + dy) % world_height
    
    def consume_energy(self, amount):
        """Reduce energy (metabolism, movement cost)"""
        self.energy = max(0, self.energy - amount)
    
    def gain_energy(self, amount):
        """Increase energy (from eating)"""
        self.energy = min(1.0, self.energy + amount)
    
    def is_alive(self):
        return self.energy > 0
    
    def can_reproduce(self):
        return self.energy > 0.6 and self.reproductive_cooldown == 0 and self.age > 2


class HerbivoreSpecies:
    """Defines characteristics of a herbivore species"""
    def __init__(self, name, preferred_biomes, temp_range, food_efficiency, 
                 reproduction_rate, metabolism, max_age, migration_tendency):
        self.name = name
        self.preferred_biomes = preferred_biomes  # List of biome IDs
        self.temp_range = temp_range  # (min, max) comfortable temperature
        self.food_efficiency = food_efficiency  # Energy gained per vegetation consumed
        self.reproduction_rate = reproduction_rate  # Offspring per breeding event
        self.metabolism = metabolism  # Energy consumed per turn
        self.max_age = max_age  # Lifespan in turns
        self.migration_tendency = migration_tendency  # How likely to move (0-1)


class AnimalSystem:
    def __init__(self, world_generator, vegetation_system):
        self.world = world_generator
        self.vegetation = vegetation_system
        self.width = world_generator.width
        self.height = world_generator.height
        
        # Animal populations
        self.herbivores = []
        
        # Define herbivore species
        self.herbivore_species = {
            'deer': HerbivoreSpecies(
                name='Deer',
                preferred_biomes=[5, 7],  # Grassland, Temperate Forest
                temp_range=(0.3, 0.7),
                food_efficiency=0.15,
                reproduction_rate=2,
                metabolism=0.08,
                max_age=40,
                migration_tendency=0.3
            ),
            'bison': HerbivoreSpecies(
                name='Bison',
                preferred_biomes=[5],  # Grassland
                temp_range=(0.3, 0.8),
                food_efficiency=0.12,
                reproduction_rate=1,
                metabolism=0.10,
                max_age=50,
                migration_tendency=0.5
            ),
            'caribou': HerbivoreSpecies(
                name='Caribou',
                preferred_biomes=[8, 9],  # Taiga, Tundra
                temp_range=(0.0, 0.4),
                food_efficiency=0.10,
                reproduction_rate=1,
                metabolism=0.07,
                max_age=45,
                migration_tendency=0.7  # Highly migratory
            ),
            'gazelle': HerbivoreSpecies(
                name='Gazelle',
                preferred_biomes=[4],  # Savanna
                temp_range=(0.5, 0.9),
                food_efficiency=0.13,
                reproduction_rate=2,
                metabolism=0.09,
                max_age=35,
                migration_tendency=0.6
            ),
            'elephant': HerbivoreSpecies(
                name='Elephant',
                preferred_biomes=[4, 6],  # Savanna, Rainforest
                temp_range=(0.6, 1.0),
                food_efficiency=0.08,
                reproduction_rate=1,
                metabolism=0.12,  # Large = high metabolism
                max_age=80,
                migration_tendency=0.4
            )
        }
        
        # Statistics tracking
        self.population_history = {species: [] for species in self.herbivore_species.keys()}
        
    def spawn_initial_populations(self, population_per_species=50):
        """Place initial herbivore populations in suitable habitats"""
        for species_name, species_data in self.herbivore_species.items():
            spawned = 0
            attempts = 0
            max_attempts = population_per_species * 10
            
            while spawned < population_per_species and attempts < max_attempts:
                attempts += 1
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                
                biome = self.world.biomes[y, x]
                temp = self.world.temperature[y, x]
                veg_density = self.vegetation.density[y, x]
                
                # Check if location is suitable
                if (biome in species_data.preferred_biomes and
                    species_data.temp_range[0] <= temp <= species_data.temp_range[1] and
                    veg_density > 0.2):  # Need some food
                    
                    animal = Animal(x, y, species_name)
                    animal.energy = np.random.uniform(0.5, 0.8)
                    self.herbivores.append(animal)
                    spawned += 1
            
            print(f"  🦌 Spawned {spawned} {species_name}")
    
    def update(self, climate_engine):
        """Update all animal behaviors for one turn"""
        # Age and metabolism
        for animal in self.herbivores:
            animal.age += 1
            species_data = self.herbivore_species[animal.species]
            
            # Base metabolism cost
            animal.consume_energy(species_data.metabolism)
            
            # Age-related death
            if animal.age > species_data.max_age:
                animal.energy = 0
            
            # Cooldown
            if animal.reproductive_cooldown > 0:
                animal.reproductive_cooldown -= 1
        
        # Behavior phase
        for animal in list(self.herbivores):  # Copy list since we may add offspring
            if not animal.is_alive():
                continue
            
            species_data = self.herbivore_species[animal.species]
            
            # 1. Movement decision
            self._move_animal(animal, species_data, climate_engine)
            
            # 2. Feeding
            self._feed_animal(animal, species_data)
            
            # 3. Reproduction
            if animal.can_reproduce():
                self._reproduce_animal(animal, species_data)
        
        # Remove dead animals
        initial_count = len(self.herbivores)
        self.herbivores = [a for a in self.herbivores if a.is_alive()]
        deaths = initial_count - len(self.herbivores)
        
        if deaths > 0:
            print(f"  💀 {deaths} herbivores died")
        
        # Track populations
        for species_name in self.herbivore_species.keys():
            count = sum(1 for a in self.herbivores if a.species == species_name)
            self.population_history[species_name].append(count)
    
    def _move_animal(self, animal, species_data, climate_engine):
        """Decide if and where animal moves"""
        # Check current location suitability
        current_biome = self.world.biomes[animal.y, animal.x]
        current_temp = self.world.temperature[animal.y, animal.x]
        current_food = self.vegetation.density[animal.y, animal.x]
        
        # Migration pressure increases with:
        # - Wrong biome
        # - Uncomfortable temperature
        # - Low food
        # - Species migration tendency
        
        biome_match = 1.0 if current_biome in species_data.preferred_biomes else 0.3
        temp_comfort = 1.0 if species_data.temp_range[0] <= current_temp <= species_data.temp_range[1] else 0.5
        food_availability = current_food
        
        habitat_quality = biome_match * temp_comfort * (0.5 + 0.5 * food_availability)
        
        # Decide to move
        move_chance = species_data.migration_tendency * (1.0 - habitat_quality)
        
        if np.random.random() < move_chance:
            # Look for better location nearby
            best_score = habitat_quality
            best_dx, best_dy = 0, 0
            
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    
                    nx = (animal.x + dx) % self.width
                    ny = (animal.y + dy) % self.height
                    
                    neighbor_biome = self.world.biomes[ny, nx]
                    neighbor_temp = self.world.temperature[ny, nx]
                    neighbor_food = self.vegetation.density[ny, nx]
                    
                    n_biome_match = 1.0 if neighbor_biome in species_data.preferred_biomes else 0.3
                    n_temp_comfort = 1.0 if species_data.temp_range[0] <= neighbor_temp <= species_data.temp_range[1] else 0.5
                    
                    neighbor_quality = n_biome_match * n_temp_comfort * (0.5 + 0.5 * neighbor_food)
                    
                    if neighbor_quality > best_score:
                        best_score = neighbor_quality
                        best_dx, best_dy = dx, dy
            
            # Move to best location (or stay if current is best)
            if best_dx != 0 or best_dy != 0:
                animal.move(best_dx, best_dy, self.width, self.height)
                animal.consume_energy(0.02)  # Movement cost
    
    def _feed_animal(self, animal, species_data):
        """Animal attempts to eat vegetation"""
        veg_density = self.vegetation.density[animal.y, animal.x]
        
        if veg_density > 0.05:  # Minimum vegetation to graze
            # Consume vegetation (proportional to hunger)
            hunger = 1.0 - animal.energy
            consumption = min(veg_density, hunger * 0.3)  # Eat up to 30% of available
            
            self.vegetation.density[animal.y, animal.x] -= consumption
            
            # Gain energy from food
            energy_gain = consumption * species_data.food_efficiency
            animal.gain_energy(energy_gain)
    
    def _reproduce_animal(self, animal, species_data):
        """Animal produces offspring"""
        # Check for nearby mates (simple proximity check)
        mate_nearby = False
        for other in self.herbivores:
            if other.species == animal.species and other is not animal:
                dist = np.sqrt((other.x - animal.x)**2 + (other.y - animal.y)**2)
                if dist < 3:
                    mate_nearby = True
                    break
        
        if mate_nearby or np.random.random() < 0.3:  # 30% chance solo reproduction (parthenogenesis-like)
            # Create offspring
            for _ in range(species_data.reproduction_rate):
                if np.random.random() < 0.7:  # 70% offspring survival
                    offspring = Animal(animal.x, animal.y, animal.species)
                    offspring.energy = 0.5
                    self.herbivores.append(offspring)
            
            # Reproduction cost
            animal.consume_energy(0.3)
            animal.reproductive_cooldown = 4  # Can't reproduce for 4 turns
    
    def get_population_counts(self):
        """Return current population by species"""
        counts = {species: 0 for species in self.herbivore_species.keys()}
        for animal in self.herbivores:
            counts[animal.species] += 1
        return counts
    
    def visualize(self, show_populations=True):
        """Display animal distribution and population graphs"""
        if show_populations:
            fig = plt.figure(figsize=(15, 10))
            gs = fig.add_gridspec(2, 2, height_ratios=[2, 1])
            
            # Map view
            ax_map = fig.add_subplot(gs[0, :])
            
            # Show vegetation as background
            ax_map.imshow(self.vegetation.density, cmap='YlGn', alpha=0.6, vmin=0, vmax=1)
            
            # Overlay animals
            species_colors = {
                'deer': 'brown',
                'bison': 'darkred',
                'caribou': 'gray',
                'gazelle': 'orange',
                'elephant': 'purple'
            }
            
            for animal in self.herbivores:
                color = species_colors.get(animal.species, 'black')
                ax_map.plot(animal.x, animal.y, 'o', color=color, markersize=3, alpha=0.7)
            
            ax_map.set_title('Animal Distribution (vegetation density shown)')
            ax_map.axis('off')
            
            # Population graphs
            ax_pop1 = fig.add_subplot(gs[1, 0])
            ax_pop2 = fig.add_subplot(gs[1, 1])
            
            # Split species across two graphs for readability
            species_list = list(self.herbivore_species.keys())
            mid = len(species_list) // 2
            
            for i, species in enumerate(species_list[:mid]):
                if len(self.population_history[species]) > 0:
                    ax_pop1.plot(self.population_history[species], 
                               label=species.capitalize(), 
                               color=species_colors[species])
            
            for species in species_list[mid:]:
                if len(self.population_history[species]) > 0:
                    ax_pop2.plot(self.population_history[species], 
                               label=species.capitalize(),
                               color=species_colors[species])
            
            ax_pop1.set_xlabel('Turn')
            ax_pop1.set_ylabel('Population')
            ax_pop1.set_title('Population Dynamics (Group 1)')
            ax_pop1.legend()
            ax_pop1.grid(True, alpha=0.3)
            
            ax_pop2.set_xlabel('Turn')
            ax_pop2.set_ylabel('Population')
            ax_pop2.set_title('Population Dynamics (Group 2)')
            ax_pop2.legend()
            ax_pop2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
        else:
            # Simple map view
            plt.figure(figsize=(12, 8))
            plt.imshow(self.vegetation.density, cmap='YlGn', alpha=0.6)
            
            species_colors = {
                'deer': 'brown', 'bison': 'darkred', 'caribou': 'gray',
                'gazelle': 'orange', 'elephant': 'purple'
            }
            
            for animal in self.herbivores:
                color = species_colors.get(animal.species, 'black')
                plt.plot(animal.x, animal.y, 'o', color=color, markersize=3, alpha=0.7)
            
            plt.title('Herbivore Distribution')
            plt.axis('off')
            plt.show()


# Integrated simulation
if __name__ == "__main__":
    from terrain_generator import WorldGenerator
    from climate_engine import ClimateEngine
    from vegetation_system import VegetationSystem
    
    # Generate world
    print("=== WORLD GENESIS ===")
    world = WorldGenerator(width=150, height=100, seed=42)
    world.generate_world(sea_level=0.42)
    
    # Initialize systems
    climate = ClimateEngine(world)
    vegetation = VegetationSystem(world)
    
    # Let vegetation establish for a few years
    print("\n=== VEGETATION ESTABLISHMENT (5 years) ===")
    for turn in range(20):
        climate.advance_turn()
        vegetation.update(climate)
    
    # Spawn animals
    print("\n=== SPAWNING HERBIVORES ===")
    animals = AnimalSystem(world, vegetation)
    animals.spawn_initial_populations(population_per_species=50)
    
    print(f"\nTotal herbivores: {len(animals.herbivores)}")
    
    # Run ecosystem simulation
    print("\n=== ECOSYSTEM SIMULATION (10 years) ===")
    for turn in range(40):
        climate.advance_turn()
        vegetation.update(climate)
        animals.update(climate)
        
        # Report every year
        if turn % 4 == 3:
            counts = animals.get_population_counts()
            print(f"\n--- Year {climate.year} Population Report ---")
            for species, count in counts.items():
                print(f"  {species.capitalize()}: {count}")
            
            # Visualize every 2 years
            if climate.year % 2 == 0:
                animals.visualize()
    
    print("\n=== SIMULATION COMPLETE ===")
