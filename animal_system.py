import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from srpg_stats import create_stats_from_template, HERBIVORE_STATS
from srpg_combat import CombatResolver
from balance_config import HERBIVORE_CONFIG
import uuid

class Animal:
    """Base class for all animal species"""
    def __init__(self, x, y, species_name):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.species = species_name
        
        # Initialize stats from template
        template = HERBIVORE_STATS.get(species_name, HERBIVORE_STATS['deer'])
        self.combat_stats = create_stats_from_template(template)
        self.movement_stats = template['movement']
        self.env_stats = template.get('environment', None)
        
        self.age = 0
        self.reproductive_cooldown = 0
        self.cause_of_death = None
    
    @property
    def energy(self):
        return self.combat_stats.hp_percentage()
    
    @energy.setter
    def energy(self, value):
        self.combat_stats.current_hp = int(max(0, min(1.0, value)) * self.combat_stats.max_hp)
    
    def move(self, dx, dy, world_width, world_height):
        """Move with wrapping at world edges"""
        self.x = (self.x + dx) % world_width
        self.y = (self.y + dy) % world_height
    
    def consume_energy(self, amount):
        """Reduce HP (metabolism)"""
        # Convert float amount (0.0-1.0) to HP damage roughly
        # 0.1 energy ~= 10% HP
        damage = int(amount * self.combat_stats.max_hp)
        if damage > 0:
            self.combat_stats.take_damage(damage)
    
    def gain_energy(self, amount):
        """Increase HP (from eating)"""
        heal = int(amount * self.combat_stats.max_hp)
        self.combat_stats.heal(heal)
    
    def is_alive(self):
        return self.combat_stats.is_alive()
    
    def can_reproduce(self):
        template = HERBIVORE_STATS.get(self.species, HERBIVORE_STATS['deer'])
        threshold = template.get('reproduction_threshold', 20)
        return (self.combat_stats.current_hp >= threshold and 
                self.reproductive_cooldown == 0 and 
                self.age > 8)  # Increased age requirement


class AnimalSystem:
    def __init__(self, world_generator, vegetation_system, ecology_system=None):
        self.world = world_generator
        self.vegetation = vegetation_system
        self.ecology = ecology_system
        self.width = world_generator.width
        self.height = world_generator.height
        self.combat_resolver = CombatResolver(world_generator)
        
        # Animal populations
        self.herbivores = []
        self.logger_callback = None # Function to call for logging interactions
        
        # Use SRPG stats instead of local definitions
        self.herbivore_species = HERBIVORE_STATS
        
        # Statistics tracking
        self.population_history = {species: [] for species in self.herbivore_species.keys()}
        self.recent_deaths = {} # Stores death counts by cause for the last update
        
    def set_logger(self, callback):
        """Set callback for logging interactions"""
        self.logger_callback = callback

    def spawn_initial_populations(self, population_per_species=50):
        """Place initial herbivore populations in suitable habitats"""
        for species_name, species_data in self.herbivore_species.items():
            spawned = 0
            attempts = 0
            max_attempts = population_per_species * 10
            
            movement_stats = species_data['movement']
            preferred_biomes = [b for b, m in movement_stats.terrain_preferences.items() if m >= 0.8]
            
            while spawned < population_per_species and attempts < max_attempts:
                attempts += 1
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                
                biome = self.world.biomes[y, x]
                veg_density = self.vegetation.density[y, x]
                
                # Check if location is suitable
                if (biome in preferred_biomes and veg_density > 0.2):
                    animal = Animal(x, y, species_name)
                    # Start with 80-100% HP
                    start_hp_percent = np.random.uniform(0.8, 1.0)
                    animal.combat_stats.current_hp = int(animal.combat_stats.max_hp * start_hp_percent)
                    self.herbivores.append(animal)
                    spawned += 1
            
            print(f"  🦌 Spawned {spawned} {species_name}")
        
        # Initialize history
        for species_name in self.herbivore_species.keys():
            count = sum(1 for a in self.herbivores if a.species == species_name)
            self.population_history[species_name].append(count)
    
    def update(self, climate_engine, predators_list=None, tribe_units=None):
        """Update all animal behaviors for one turn"""
        # Build spatial map for fast neighbor lookups
        # Key: (x, y), Value: list of animals
        self.spatial_map = {}
        for animal in self.herbivores:
            pos = (animal.x, animal.y)
            if pos not in self.spatial_map:
                self.spatial_map[pos] = []
            self.spatial_map[pos].append(animal)

        # Build predator map if provided
        predator_map = {}
        if predators_list:
            for p in predators_list:
                pos = (p.x, p.y)
                if pos not in predator_map:
                    predator_map[pos] = []
                predator_map[pos].append(p)
        
        # Add tribe units to predator map (as threats)
        if tribe_units:
            for u in tribe_units:
                pos = (u.x, u.y)
                if pos not in predator_map:
                    predator_map[pos] = []
                predator_map[pos].append(u)

        # Age and metabolism
        for animal in self.herbivores:
            if not animal.is_alive(): continue

            animal.age += 1
            
            # Base metabolism cost (1 HP per turn + age factor)
            base_cost = 1
            multiplier = HERBIVORE_CONFIG.get('metabolism_multiplier', 1.0)
            
            # Apply multiplier (probabilistic for fractional values)
            cost_float = base_cost * multiplier
            metabolism_cost = int(cost_float)
            if np.random.random() < (cost_float - metabolism_cost):
                metabolism_cost += 1
            
            # Mortality check (Old Age)
            if animal.env_stats and animal.age > animal.env_stats.max_age:
                # Chance to die increases with years past max age
                over_age = animal.age - animal.env_stats.max_age
                death_chance = 0.05 + (over_age * 0.02)
                if np.random.random() < death_chance:
                    animal.combat_stats.current_hp = 0
                    animal.cause_of_death = 'old_age'
                    continue
            
            # Legacy age penalty (keep for non-env stats animals if any)
            elif animal.age > 40:  
                metabolism_cost += 1
            
            # Environmental checks
            if animal.env_stats:
                # Temperature check
                local_temp = climate_engine.world.temperature[animal.y, animal.x]
                
                # Cold stress
                if local_temp < animal.env_stats.min_temp:
                    diff = animal.env_stats.min_temp - local_temp
                    damage = int(diff * 20) # Significant damage
                    if animal.env_stats.cold_blooded:
                        damage = int(damage * 2.0) # Cold blooded suffer double
                    
                    if damage > 0:
                        animal.combat_stats.take_damage(damage)
                        if not animal.is_alive() and animal.cause_of_death is None:
                            animal.cause_of_death = 'cold'
                
                # Heat stress
                if local_temp > animal.env_stats.max_temp:
                    diff = local_temp - animal.env_stats.max_temp
                    damage = int(diff * 20)
                    if damage > 0:
                        animal.combat_stats.take_damage(damage)
                        if not animal.is_alive() and animal.cause_of_death is None:
                            animal.cause_of_death = 'heat'

            if animal.is_alive():
                animal.combat_stats.take_damage(metabolism_cost)
                if not animal.is_alive() and animal.cause_of_death is None:
                    animal.cause_of_death = 'starvation'
            
            # Cooldown
            if animal.reproductive_cooldown > 0:
                animal.reproductive_cooldown -= 1
        
        # Behavior phase
        new_offspring = []
        for animal in self.herbivores:
            if not animal.is_alive():
                continue
            
            species_data = self.herbivore_species[animal.species]
            
            # 1. Movement decision
            self._move_animal(animal, species_data, climate_engine, predator_map if predators_list else None)
            
            # Update spatial map after move (remove from old, add to new)
            # Note: For strict correctness we should update the map, but for performance
            # we can accept using the start-of-turn map for reproduction checks
            # or just rebuild it if we really need to. 
            # Actually, reproduction happens after movement, so using old map is slightly wrong.
            # But rebuilding is expensive. Let's just use the old map for "nearby" checks
            # since animals don't move far (1-2 tiles).
            
            # 2. Feeding
            self._feed_animal(animal, species_data)
            
            # 3. Reproduction
            if animal.can_reproduce():
                offspring = self._reproduce_animal(animal, species_data)
                if offspring:
                    new_offspring.extend(offspring)
        
        # Add new offspring
        self.herbivores.extend(new_offspring)
        
        # Remove dead animals
        initial_count = len(self.herbivores)
        
        # Collect death stats
        self.recent_deaths = {}
        dead_animals = [a for a in self.herbivores if not a.is_alive()]
        for a in dead_animals:
            cause = a.cause_of_death if a.cause_of_death else 'unknown'
            if cause not in self.recent_deaths:
                self.recent_deaths[cause] = 0
            self.recent_deaths[cause] += 1
            
            if self.logger_callback:
                self.logger_callback('death', a.species, details=cause)
            
        self.herbivores = [a for a in self.herbivores if a.is_alive()]
        deaths = initial_count - len(self.herbivores)
        
        if deaths > 0:
            # print(f"  💀 {deaths} herbivores died") # Suppress detailed print here, let simulation handle it
            pass
        
        # Track populations
        for species_name in self.herbivore_species.keys():
            count = sum(1 for a in self.herbivores if a.species == species_name)
            self.population_history[species_name].append(count)
    
    def _move_animal(self, animal, species_data, climate_engine, predator_map=None):
        """Decide if and where animal moves"""
        movement_stats = animal.movement_stats
        
        # Check current location suitability
        current_biome = self.world.biomes[animal.y, animal.x]
        current_food = self.vegetation.density[animal.y, animal.x]
        
        # Habitat quality based on terrain preference
        biome_pref = movement_stats.terrain_preferences.get(current_biome, 0.3)
        habitat_quality = biome_pref * (0.5 + 0.5 * current_food)
        
        # Check for predators nearby
        nearby_predators = []
        if predator_map:
            scan_radius = 4
            for dy in range(-scan_radius, scan_radius + 1):
                for dx in range(-scan_radius, scan_radius + 1):
                    nx = (animal.x + dx) % self.width
                    ny = (animal.y + dy) % self.height
                    if (nx, ny) in predator_map:
                        nearby_predators.append((nx, ny))
        
        # Flee if predators are close
        is_fleeing = len(nearby_predators) > 0
        
        # Move if habitat is poor or hungry OR fleeing
        should_move = habitat_quality < 0.6 or animal.combat_stats.hp_percentage() < 0.6 or is_fleeing
        
        if should_move or np.random.random() < 0.3:
            # Look for better location nearby
            best_score = -999 if is_fleeing else habitat_quality
            best_dx, best_dy = 0, 0
            
            # Scan radius based on movement range
            scan_radius = movement_stats.movement_range
            
            for dy in range(-scan_radius, scan_radius + 1):
                for dx in range(-scan_radius, scan_radius + 1):
                    if dx == 0 and dy == 0:
                        continue
                    
                    nx = (animal.x + dx) % self.width
                    ny = (animal.y + dy) % self.height
                    
                    neighbor_biome = self.world.biomes[ny, nx]
                    
                    # Check for water traversal
                    if not movement_stats.can_swim and neighbor_biome in [0, 1]:
                        continue
                        
                    neighbor_food = self.vegetation.density[ny, nx]
                    
                    n_biome_pref = movement_stats.terrain_preferences.get(neighbor_biome, 0.3)
                    
                    # Distance penalty
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist > movement_stats.movement_range:
                        continue
                        
                    dist_penalty = 1.0 / (1.0 + dist * 0.2)
                    
                    neighbor_quality = n_biome_pref * (0.5 + 0.5 * neighbor_food) * dist_penalty
                    
                    # Predator avoidance score
                    predator_penalty = 0
                    if is_fleeing:
                        # Calculate distance to nearest predator from this potential spot
                        min_pred_dist = 999
                        for px, py in nearby_predators:
                            # Simple distance (ignoring wrap for speed in this loop, or handle it?)
                            # Let's just use simple euclidean for local avoidance
                            p_dist = np.sqrt((nx - px)**2 + (ny - py)**2)
                            if p_dist < min_pred_dist:
                                min_pred_dist = p_dist
                        
                        # Reward being far from predators
                        # If spot is closer than 2 units, massive penalty
                        if min_pred_dist < 2:
                            predator_penalty = 100
                        else:
                            # Bonus for distance
                            neighbor_quality += min_pred_dist * 2
                    
                    final_score = neighbor_quality - predator_penalty
                    
                    if final_score > best_score:
                        best_score = final_score
                        best_dx, best_dy = dx, dy
            
            # Move to best location
            if best_dx != 0 or best_dy != 0:
                animal.move(best_dx, best_dy, self.width, self.height)
                # Movement costs HP? Maybe small amount
                # animal.combat_stats.take_damage(1)
    
    def _feed_animal(self, animal, species_data):
        """Animal attempts to eat vegetation or insects"""
        # Insectivores (like frogs) eat insects if available
        if animal.species == 'frog' and self.ecology and self.ecology.insects:
            consumed = self.ecology.insects.consume(animal.x, animal.y, amount=0.1)
            if consumed > 0:
                animal.gain_energy(consumed * 2.0) # Insects are very nutritious for frogs
                return

        veg_density = self.vegetation.density[animal.y, animal.x]
        
        # Use combat resolver for feeding
        consumed = self.combat_resolver.resolve_herbivore_feeding(
            animal, veg_density, species_data
        )
        
        if consumed > 0:
            self.vegetation.density[animal.y, animal.x] -= consumed
    
    def _reproduce_animal(self, animal, species_data):
        """Animal produces offspring"""
        # Check for nearby mates using spatial map
        mate_nearby = False
        search_radius = 3
        
        # Check cells in radius
        for dy in range(-search_radius, search_radius + 1):
            for dx in range(-search_radius, search_radius + 1):
                nx = (animal.x + dx) % self.width
                ny = (animal.y + dy) % self.height
                
                if (nx, ny) in self.spatial_map:
                    for other in self.spatial_map[(nx, ny)]:
                        if other.species == animal.species and other is not animal:
                            mate_nearby = True
                            break
                if mate_nearby:
                    break
            if mate_nearby:
                break
        
        offspring_list = []
        if mate_nearby:
            offspring_count = species_data.get('offspring_count', 1)
            
            for _ in range(offspring_count):
                if np.random.random() < 0.8:  # 80% survival
                    offspring = Animal(animal.x, animal.y, animal.species)
                    # Offspring start with 50% HP
                    offspring.combat_stats.current_hp = int(offspring.combat_stats.max_hp * 0.5)
                    offspring_list.append(offspring)
            
            # Reproduction cost (HP)
            cost = int(animal.combat_stats.max_hp * 0.3)
            animal.combat_stats.take_damage(cost)
            animal.reproductive_cooldown = 6
            
        return offspring_list
    
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
                'elephant': 'purple',
                'rabbit': 'white'
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
                'gazelle': 'orange', 'elephant': 'purple', 'rabbit': 'white'
            }
            
            for animal in self.herbivores:
                color = species_colors.get(animal.species, 'black')
                plt.plot(animal.x, animal.y, 'o', color=color, markersize=3, alpha=0.7)
            
            plt.title('Herbivore Distribution')
            plt.axis('off')
            plt.show()
    
    def spawn_migrants(self, species_name, count=5):
        """Spawn new individuals at map edges (migration)"""
        spawned = 0
        attempts = 0
        max_attempts = count * 10
        
        species_data = self.herbivore_species[species_name]
        movement_stats = species_data['movement']
        preferred_biomes = [b for b, m in movement_stats.terrain_preferences.items() if m >= 0.6]
        
        while spawned < count and attempts < max_attempts:
            attempts += 1
            # Pick an edge
            if np.random.random() < 0.5:
                x = np.random.choice([0, self.width - 1])
                y = np.random.randint(0, self.height)
            else:
                x = np.random.randint(0, self.width)
                y = np.random.choice([0, self.height - 1])
            
            biome = self.world.biomes[y, x]
            veg_density = self.vegetation.density[y, x]
            
            # Check if location is suitable
            if (biome in preferred_biomes and veg_density > 0.1):
                animal = Animal(x, y, species_name)
                # Migrants are usually healthy
                animal.combat_stats.current_hp = int(animal.combat_stats.max_hp * 0.9)
                self.herbivores.append(animal)
                spawned += 1
        
        if spawned > 0:
            print(f"  🦌 {spawned} {species_name} migrated into the area")


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
