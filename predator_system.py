import numpy as np
import matplotlib.pyplot as plt

class Predator:
    """Carnivore that hunts herbivores"""
    def __init__(self, x, y, species_name):
        self.x = x
        self.y = y
        self.species = species_name
        self.energy = 1.0
        self.age = 0
        self.reproductive_cooldown = 0
        self.hunt_cooldown = 0  # Cooldown after successful kill
    
    def move(self, dx, dy, world_width, world_height):
        self.x = (self.x + dx) % world_width
        self.y = (self.y + dy) % world_height
    
    def consume_energy(self, amount):
        self.energy = max(0, self.energy - amount)
    
    def gain_energy(self, amount):
        self.energy = min(1.0, self.energy + amount)
    
    def is_alive(self):
        return self.energy > 0
    
    def can_reproduce(self):
        return self.energy > 0.7 and self.reproductive_cooldown == 0 and self.age > 3
    
    def can_hunt(self):
        return self.hunt_cooldown == 0 and self.energy > 0.2


class PredatorSpecies:
    """Defines characteristics of a predator species"""
    def __init__(self, name, preferred_biomes, temp_range, hunt_success_rate,
                 kill_energy_gain, metabolism, max_age, pack_hunter, 
                 hunting_range, prey_preferences):
        self.name = name
        self.preferred_biomes = preferred_biomes
        self.temp_range = temp_range
        self.hunt_success_rate = hunt_success_rate  # Base chance to kill prey
        self.kill_energy_gain = kill_energy_gain  # Energy from successful kill
        self.metabolism = metabolism
        self.max_age = max_age
        self.pack_hunter = pack_hunter  # Gets bonus with nearby pack members
        self.hunting_range = hunting_range  # How far they can detect/chase prey
        self.prey_preferences = prey_preferences  # Dict of prey: preference_weight


class PredatorSystem:
    def __init__(self, world_generator, vegetation_system, animal_system):
        self.world = world_generator
        self.vegetation = vegetation_system
        self.herbivores = animal_system  # Reference to herbivore system
        self.width = world_generator.width
        self.height = world_generator.height
        
        self.predators = []
        
        # Define predator species
        self.predator_species = {
            'wolf': PredatorSpecies(
                name='Wolf',
                preferred_biomes=[5, 7, 8],  # Grassland, Forest, Taiga
                temp_range=(0.2, 0.7),
                hunt_success_rate=0.25,  # 25% base success
                kill_energy_gain=0.6,
                metabolism=0.12,  # High metabolism
                max_age=50,
                pack_hunter=True,
                hunting_range=5,
                prey_preferences={'deer': 1.0, 'caribou': 0.8, 'bison': 0.6}
            ),
            'lion': PredatorSpecies(
                name='Lion',
                preferred_biomes=[4],  # Savanna
                temp_range=(0.6, 0.95),
                hunt_success_rate=0.30,
                kill_energy_gain=0.7,
                metabolism=0.13,
                max_age=45,
                pack_hunter=True,
                hunting_range=4,
                prey_preferences={'gazelle': 1.0, 'elephant': 0.4}  # Elephants risky
            ),
            'bear': PredatorSpecies(
                name='Bear',
                preferred_biomes=[7, 8],  # Forest, Taiga
                temp_range=(0.2, 0.6),
                hunt_success_rate=0.20,  # Less efficient hunter (omnivore)
                kill_energy_gain=0.5,
                metabolism=0.10,  # Can supplement with vegetation
                max_age=60,
                pack_hunter=False,
                hunting_range=3,
                prey_preferences={'deer': 0.8, 'caribou': 0.7}
            ),
            'leopard': PredatorSpecies(
                name='Leopard',
                preferred_biomes=[4, 6, 7],  # Savanna, Rainforest, Forest
                temp_range=(0.5, 0.9),
                hunt_success_rate=0.35,  # Ambush specialist
                kill_energy_gain=0.5,
                metabolism=0.11,
                max_age=40,
                pack_hunter=False,
                hunting_range=4,
                prey_preferences={'gazelle': 1.0, 'deer': 0.9}
            ),
            'arctic_fox': PredatorSpecies(
                name='Arctic Fox',
                preferred_biomes=[9, 10],  # Tundra, Snow
                temp_range=(0.0, 0.3),
                hunt_success_rate=0.40,  # Small prey, high success
                kill_energy_gain=0.3,  # Small meals
                metabolism=0.08,
                max_age=35,
                pack_hunter=False,
                hunting_range=3,
                prey_preferences={'caribou': 0.5}  # Opportunistic
            )
        }
        
        self.population_history = {species: [] for species in self.predator_species.keys()}
        self.kill_history = {species: [] for species in self.predator_species.keys()}
    
    def spawn_initial_populations(self, population_per_species=20):
        """Spawn predators in suitable habitats with prey nearby"""
        for species_name, species_data in self.predator_species.items():
            spawned = 0
            attempts = 0
            max_attempts = population_per_species * 20
            
            while spawned < population_per_species and attempts < max_attempts:
                attempts += 1
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                
                biome = self.world.biomes[y, x]
                temp = self.world.temperature[y, x]
                
                # Check habitat suitability
                if (biome in species_data.preferred_biomes and
                    species_data.temp_range[0] <= temp <= species_data.temp_range[1]):
                    
                    # Check for nearby prey
                    prey_nearby = self._count_nearby_prey(x, y, species_data.hunting_range * 2)
                    
                    if prey_nearby > 0:
                        predator = Predator(x, y, species_name)
                        predator.energy = np.random.uniform(0.5, 0.8)
                        self.predators.append(predator)
                        spawned += 1
            
            print(f"  🐺 Spawned {spawned} {species_name}")
    
    def update(self, climate_engine):
        """Update all predator behaviors"""
        kills_this_turn = {species: 0 for species in self.predator_species.keys()}
        
        # Age and metabolism
        for predator in self.predators:
            predator.age += 1
            species_data = self.predator_species[predator.species]
            
            # Metabolism
            predator.consume_energy(species_data.metabolism)
            
            # Bears can eat vegetation as backup (omnivores)
            if predator.species == 'bear' and predator.energy < 0.4:
                veg = self.vegetation.density[predator.y, predator.x]
                if veg > 0.1:
                    consumption = min(0.15, veg)
                    self.vegetation.density[predator.y, predator.x] -= consumption
                    predator.gain_energy(consumption * 0.3)  # Less efficient than meat
            
            # Age death
            if predator.age > species_data.max_age:
                predator.energy = 0
            
            # Cooldowns
            if predator.reproductive_cooldown > 0:
                predator.reproductive_cooldown -= 1
            if predator.hunt_cooldown > 0:
                predator.hunt_cooldown -= 1
        
        # Behavior phase
        for predator in list(self.predators):
            if not predator.is_alive():
                continue
            
            species_data = self.predator_species[predator.species]
            
            # 1. Hunt (if able)
            if predator.can_hunt():
                kill_made = self._attempt_hunt(predator, species_data)
                if kill_made:
                    kills_this_turn[predator.species] += 1
            
            # 2. Move toward prey or better habitat
            self._move_predator(predator, species_data, climate_engine)
            
            # 3. Reproduce
            if predator.can_reproduce():
                self._reproduce_predator(predator, species_data)
        
        # Remove dead predators
        initial_count = len(self.predators)
        self.predators = [p for p in self.predators if p.is_alive()]
        deaths = initial_count - len(self.predators)
        
        if deaths > 0:
            print(f"  💀 {deaths} predators died")
        
        # Track statistics
        for species_name in self.predator_species.keys():
            count = sum(1 for p in self.predators if p.species == species_name)
            self.population_history[species_name].append(count)
            self.kill_history[species_name].append(kills_this_turn[species_name])
    
    def _count_nearby_prey(self, x, y, radius):
        """Count herbivores within radius"""
        count = 0
        for herbivore in self.herbivores.herbivores:
            dx = min(abs(herbivore.x - x), self.width - abs(herbivore.x - x))
            dy = min(abs(herbivore.y - y), self.height - abs(herbivore.y - y))
            dist = np.sqrt(dx*dx + dy*dy)
            if dist <= radius:
                count += 1
        return count
    
    def _attempt_hunt(self, predator, species_data):
        """Predator tries to kill nearby prey"""
        # Find prey in hunting range
        potential_prey = []
        
        for herbivore in self.herbivores.herbivores:
            dx = min(abs(herbivore.x - predator.x), self.width - abs(herbivore.x - predator.x))
            dy = min(abs(herbivore.y - predator.y), self.height - abs(herbivore.y - predator.y))
            dist = np.sqrt(dx*dx + dy*dy)
            
            if dist <= species_data.hunting_range:
                # Check if this prey type is preferred
                preference = species_data.prey_preferences.get(herbivore.species, 0.1)
                potential_prey.append((herbivore, preference, dist))
        
        if not potential_prey:
            return False
        
        # Choose prey (weighted by preference and proximity)
        weights = [pref / (1 + dist * 0.2) for _, pref, dist in potential_prey]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return False
        
        weights = [w / total_weight for w in weights]
        target_idx = np.random.choice(len(potential_prey), p=weights)
        target_herbivore, _, _ = potential_prey[target_idx]
        
        # Calculate hunt success
        base_success = species_data.hunt_success_rate
        
        # Pack hunting bonus
        if species_data.pack_hunter:
            nearby_pack = sum(1 for p in self.predators 
                            if p.species == predator.species and p is not predator
                            and np.sqrt((p.x - predator.x)**2 + (p.y - predator.y)**2) < 3)
            base_success += nearby_pack * 0.1  # +10% per pack member
        
        # Prey health affects difficulty
        prey_escape_chance = target_herbivore.energy * 0.3  # Healthy prey harder to catch
        success_chance = min(0.8, base_success * (1 - prey_escape_chance))
        
        if np.random.random() < success_chance:
            # Successful kill!
            target_herbivore.energy = 0  # Prey dies
            predator.gain_energy(species_data.kill_energy_gain)
            predator.hunt_cooldown = 2  # Rest after kill
            return True
        else:
            # Failed hunt
            predator.consume_energy(0.05)  # Chase cost
            return False
    
    def _move_predator(self, predator, species_data, climate_engine):
        """Move toward prey or better habitat"""
        # Find direction with most prey
        best_prey_count = 0
        best_dx, best_dy = 0, 0
        
        search_directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        # Check current biome suitability
        current_biome = self.world.biomes[predator.y, predator.x]
        current_temp = self.world.temperature[predator.y, predator.x]
        
        biome_suitable = current_biome in species_data.preferred_biomes
        temp_suitable = species_data.temp_range[0] <= current_temp <= species_data.temp_range[1]
        
        # If in bad habitat, prioritize moving to good habitat unless starving
        seeking_habitat = (not biome_suitable or not temp_suitable) and predator.energy > 0.3
        
        for dx, dy in search_directions:
            nx = (predator.x + dx * 3) % self.width  # Look 3 cells ahead
            ny = (predator.y + dy * 3) % self.height
            
            # Check prey
            prey_count = self._count_nearby_prey(nx, ny, species_data.hunting_range)
            
            # Check habitat at destination
            dest_biome = self.world.biomes[ny, nx]
            dest_temp = self.world.temperature[ny, nx]
            dest_suitable = (dest_biome in species_data.preferred_biomes and 
                           species_data.temp_range[0] <= dest_temp <= species_data.temp_range[1])
            
            score = prey_count
            if seeking_habitat and dest_suitable:
                score += 2  # Bonus for finding good habitat
            elif not dest_suitable:
                score -= 1  # Penalty for bad habitat
            
            if score > best_prey_count:
                best_prey_count = score
                best_dx, best_dy = dx, dy
        
        # Move if target found
        if best_dx != 0 or best_dy != 0:
            predator.move(best_dx, best_dy, self.width, self.height)
            predator.consume_energy(0.03)  # Movement cost
        elif predator.energy < 0.3:  # Desperately searching
            wander_dx = np.random.choice([-1, 0, 1])
            wander_dy = np.random.choice([-1, 0, 1])
            if wander_dx != 0 or wander_dy != 0:
                predator.move(wander_dx, wander_dy, self.width, self.height)
                predator.consume_energy(0.02)
    
    def _reproduce_predator(self, predator, species_data):
        """Predator produces offspring"""
        # Need mate nearby (for sexual reproduction)
        mate_nearby = False
        for other in self.predators:
            if other.species == predator.species and other is not predator:
                dist = np.sqrt((other.x - predator.x)**2 + (other.y - predator.y)**2)
                if dist < 4:
                    mate_nearby = True
                    break
        
        if mate_nearby:
            # Litter size varies by species
            litter_size = 2 if species_data.pack_hunter else 1
            
            for _ in range(litter_size):
                if np.random.random() < 0.6:  # 60% offspring survival
                    offspring = Predator(predator.x, predator.y, predator.species)
                    offspring.energy = 0.5
                    self.predators.append(offspring)
            
            predator.consume_energy(0.4)  # High reproduction cost
            predator.reproductive_cooldown = 6  # Longer cooldown than herbivores
    
    def get_population_counts(self):
        """Return current populations"""
        counts = {species: 0 for species in self.predator_species.keys()}
        for pred in self.predators:
            counts[pred.species] += 1
        return counts
    
    def visualize(self, show_populations=True):
        """Display predator distribution and dynamics"""
        if show_populations:
            fig = plt.figure(figsize=(15, 12))
            gs = fig.add_gridspec(3, 2, height_ratios=[2, 1, 1])
            
            # Map view with both predators and prey
            ax_map = fig.add_subplot(gs[0, :])
            ax_map.imshow(self.vegetation.density, cmap='YlGn', alpha=0.4, vmin=0, vmax=1)
            
            # Herbivores (smaller, lighter)
            herbivore_colors = {
                'deer': 'tan', 'bison': 'wheat', 'caribou': 'lightgray',
                'gazelle': 'gold', 'elephant': 'plum'
            }
            for herb in self.herbivores.herbivores:
                color = herbivore_colors.get(herb.species, 'lightblue')
                ax_map.plot(herb.x, herb.y, 'o', color=color, markersize=2, alpha=0.5)
            
            # Predators (larger, darker)
            predator_colors = {
                'wolf': 'darkred', 'lion': 'orange', 'bear': 'brown',
                'leopard': 'gold', 'arctic_fox': 'white'
            }
            for pred in self.predators:
                color = predator_colors.get(pred.species, 'black')
                ax_map.plot(pred.x, pred.y, '^', color=color, markersize=6, 
                          alpha=0.8, markeredgecolor='black', markeredgewidth=0.5)
            
            ax_map.set_title('Ecosystem Overview (triangles=predators, circles=herbivores)')
            ax_map.axis('off')
            
            # Predator populations
            ax_pred_pop = fig.add_subplot(gs[1, 0])
            for species, color in predator_colors.items():
                if len(self.population_history[species]) > 0:
                    ax_pred_pop.plot(self.population_history[species], 
                                   label=species.capitalize(), color=color)
            ax_pred_pop.set_xlabel('Turn')
            ax_pred_pop.set_ylabel('Population')
            ax_pred_pop.set_title('Predator Populations')
            ax_pred_pop.legend()
            ax_pred_pop.grid(True, alpha=0.3)
            
            # Herbivore populations (for comparison)
            ax_herb_pop = fig.add_subplot(gs[1, 1])
            for species in self.herbivores.population_history.keys():
                if len(self.herbivores.population_history[species]) > 0:
                    color = herbivore_colors.get(species, 'blue')
                    ax_herb_pop.plot(self.herbivores.population_history[species],
                                   label=species.capitalize(), color=color)
            ax_herb_pop.set_xlabel('Turn')
            ax_herb_pop.set_ylabel('Population')
            ax_herb_pop.set_title('Herbivore Populations')
            ax_herb_pop.legend()
            ax_herb_pop.grid(True, alpha=0.3)
            
            # Kill rates
            ax_kills = fig.add_subplot(gs[2, :])
            for species, color in predator_colors.items():
                if len(self.kill_history[species]) > 0:
                    # Moving average for smoothing
                    if len(self.kill_history[species]) > 4:
                        smoothed = np.convolve(self.kill_history[species], 
                                             np.ones(4)/4, mode='valid')
                        ax_kills.plot(range(len(smoothed)), smoothed,
                                    label=species.capitalize(), color=color)
            ax_kills.set_xlabel('Turn')
            ax_kills.set_ylabel('Kills per Turn (4-turn avg)')
            ax_kills.set_title('Predation Pressure')
            ax_kills.legend()
            ax_kills.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()


# Full ecosystem simulation
if __name__ == "__main__":
    from terrain_generator import WorldGenerator
    from climate_engine import ClimateEngine
    from vegetation_system import VegetationSystem
    from animal_system import AnimalSystem
    
    print("=== WORLD GENESIS ===")
    world = WorldGenerator(width=150, height=100, seed=42)
    world.generate_world(sea_level=0.42)
    
    climate = ClimateEngine(world)
    vegetation = VegetationSystem(world)
    
    # Establish vegetation (5 years)
    print("\n=== VEGETATION ESTABLISHMENT ===")
    for turn in range(20):
        climate.advance_turn()
        vegetation.update(climate)
    
    # Spawn herbivores
    print("\n=== SPAWNING HERBIVORES ===")
    animals = AnimalSystem(world, vegetation)
    animals.spawn_initial_populations(population_per_species=100)  # More prey
    
    # Let herbivores establish (3 years)
    print("\n=== HERBIVORE ESTABLISHMENT ===")
    for turn in range(12):
        climate.advance_turn()
        vegetation.update(climate)
        animals.update(climate)
    
    # Spawn predators
    print("\n=== UNLEASHING PREDATORS ===")
    predators = PredatorSystem(world, vegetation, animals)
    predators.spawn_initial_populations(population_per_species=15)  # Fewer predators
    
    # Full ecosystem simulation (15 years)
    print("\n=== FULL ECOSYSTEM SIMULATION ===")
    for turn in range(60):
        climate.advance_turn()
        vegetation.update(climate)
        animals.update(climate)
        predators.update(climate)
        
        # Report every 2 years
        if turn % 8 == 7:
            print(f"\n--- Year {climate.year} Ecosystem Report ---")
            print("Herbivores:")
            for species, count in animals.get_population_counts().items():
                print(f"  {species.capitalize()}: {count}")
            print("Predators:")
            for species, count in predators.get_population_counts().items():
                print(f"  {species.capitalize()}: {count}")
            
            # Visualize every 4 years
            if climate.year % 4 == 0:
                predators.visualize()
    
    print("\n=== SIMULATION COMPLETE ===")
