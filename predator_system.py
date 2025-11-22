import numpy as np
import matplotlib.pyplot as plt
from srpg_stats import create_stats_from_template, PREDATOR_STATS
from srpg_combat import CombatResolver
import uuid

class Predator:
    """Carnivore that hunts herbivores"""
    def __init__(self, x, y, species_name):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.species = species_name
        
        # Initialize stats from template
        template = PREDATOR_STATS.get(species_name, PREDATOR_STATS['wolf'])
        self.combat_stats = create_stats_from_template(template)
        self.movement_stats = template['movement']
        self.env_stats = template.get('environment', None)
        
        self.age = 0
        self.reproductive_cooldown = 0
        self.hunt_cooldown = 0  # Cooldown after successful kill
        self.cause_of_death = None
    
    @property
    def energy(self):
        return self.combat_stats.hp_percentage()
    
    @energy.setter
    def energy(self, value):
        self.combat_stats.current_hp = int(max(0, min(1.0, value)) * self.combat_stats.max_hp)
    
    def move(self, dx, dy, world_width, world_height):
        self.x = (self.x + dx) % world_width
        self.y = (self.y + dy) % world_height
    
    def consume_energy(self, amount):
        """Reduce HP (metabolism)"""
        damage = int(amount * self.combat_stats.max_hp)
        if damage > 0:
            self.combat_stats.take_damage(damage)
    
    def gain_energy(self, amount):
        """Increase HP (eating)"""
        heal = int(amount * self.combat_stats.max_hp)
        self.combat_stats.heal(heal)
    
    def is_alive(self):
        return self.combat_stats.is_alive()
    
    def can_reproduce(self):
        template = PREDATOR_STATS.get(self.species, PREDATOR_STATS['wolf'])
        threshold = template.get('reproduction_threshold', 30)
        return (self.combat_stats.current_hp >= threshold and 
                self.reproductive_cooldown == 0 and 
                self.age > 10)
    
    def can_hunt(self):
        return self.hunt_cooldown == 0 and self.combat_stats.current_hp > 5


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
        self.combat_resolver = CombatResolver(world_generator)
        
        self.predators = []
        self.logger_callback = None # Function to call for logging interactions
        
        # Use SRPG stats
        self.predator_species = PREDATOR_STATS
        
        self.population_history = {species: [] for species in self.predator_species.keys()}
        self.kill_history = {species: [] for species in self.predator_species.keys()}
        self.recent_deaths = {}
    
    def set_logger(self, callback):
        """Set callback for logging interactions"""
        self.logger_callback = callback

    def _build_prey_map(self):
        """Build or retrieve spatial map of prey"""
        if hasattr(self.herbivores, 'spatial_map') and self.herbivores.spatial_map:
            self.prey_map = self.herbivores.spatial_map
        else:
            self.prey_map = {}
            for h in self.herbivores.herbivores:
                pos = (h.x, h.y)
                if pos not in self.prey_map:
                    self.prey_map[pos] = []
                self.prey_map[pos].append(h)

    def spawn_initial_populations(self, population_per_species=20):
        """Spawn predators in suitable habitats with prey nearby"""
        # Build prey map for efficient lookups
        self._build_prey_map()
        
        for species_name, species_data in self.predator_species.items():
            spawned = 0
            attempts = 0
            max_attempts = population_per_species * 20
            
            movement_stats = species_data['movement']
            preferred_biomes = [b for b, m in movement_stats.terrain_preferences.items() if m >= 0.8]
            
            while spawned < population_per_species and attempts < max_attempts:
                attempts += 1
                x = np.random.randint(0, self.width)
                y = np.random.randint(0, self.height)
                
                biome = self.world.biomes[y, x]
                
                # Check habitat suitability
                if biome in preferred_biomes:
                    
                    # Check for nearby prey
                    prey_nearby = self._count_nearby_prey(x, y, 10)
                    
                    if prey_nearby > 0:
                        predator = Predator(x, y, species_name)
                        # Start with 80-100% HP
                        start_hp_percent = np.random.uniform(0.8, 1.0)
                        predator.combat_stats.current_hp = int(predator.combat_stats.max_hp * start_hp_percent)
                        self.predators.append(predator)
                        spawned += 1
            
            print(f"  🐺 Spawned {spawned} {species_name}")
        
        # Initialize history
        for species_name in self.predator_species.keys():
            count = sum(1 for p in self.predators if p.species == species_name)
            self.population_history[species_name].append(count)
            self.kill_history[species_name].append(0)
    
    def update(self, climate_engine, tribe_units=None):
        """Update all predator behaviors"""
        kills_this_turn = {species: 0 for species in self.predator_species.keys()}
        
        # Build spatial map for predators
        self.spatial_map = {}
        for pred in self.predators:
            pos = (pred.x, pred.y)
            if pos not in self.spatial_map:
                self.spatial_map[pos] = []
            self.spatial_map[pos].append(pred)
            
        # Build prey map
        self._build_prey_map()
        
        # Age and metabolism
        for predator in self.predators:
            if not predator.is_alive(): continue

            predator.age += 1
            
            # Metabolism cost
            metabolism_cost = 1
            
            # Mortality check (Old Age)
            if predator.env_stats and predator.age > predator.env_stats.max_age:
                over_age = predator.age - predator.env_stats.max_age
                death_chance = 0.05 + (over_age * 0.02)
                if np.random.random() < death_chance:
                    predator.combat_stats.current_hp = 0
                    predator.cause_of_death = 'old_age'
                    continue
            
            # Legacy age penalty
            elif predator.age > 40:
                metabolism_cost += 1
            
            # Environmental checks
            if predator.env_stats:
                local_temp = climate_engine.world.temperature[predator.y, predator.x]
                
                # Cold stress
                if local_temp < predator.env_stats.min_temp:
                    diff = predator.env_stats.min_temp - local_temp
                    damage = int(diff * 20)
                    if predator.env_stats.cold_blooded:
                        damage = int(damage * 2.0)
                    if damage > 0:
                        predator.combat_stats.take_damage(damage)
                        if not predator.is_alive() and predator.cause_of_death is None:
                            predator.cause_of_death = 'cold'
                
                # Heat stress
                if local_temp > predator.env_stats.max_temp:
                    diff = local_temp - predator.env_stats.max_temp
                    damage = int(diff * 20)
                    if damage > 0:
                        predator.combat_stats.take_damage(damage)
                        if not predator.is_alive() and predator.cause_of_death is None:
                            predator.cause_of_death = 'heat'

            # Competition penalty
            # Check local density (simplified check using spatial map)
            pos = (predator.x, predator.y)
            local_density = len(self.spatial_map.get(pos, []))
            if local_density > 2:
                metabolism_cost += (local_density - 2) * 2
            
            if predator.is_alive():
                predator.combat_stats.take_damage(metabolism_cost)
                if not predator.is_alive() and predator.cause_of_death is None:
                    predator.cause_of_death = 'starvation'
            
            # Bears can eat vegetation as backup (omnivores)
            if predator.species == 'bear' and predator.combat_stats.hp_percentage() < 0.4:
                veg = self.vegetation.density[predator.y, predator.x]
                if veg > 0.1:
                    consumption = min(0.10, veg) # Reduced from 0.15
                    self.vegetation.density[predator.y, predator.x] -= consumption
                    predator.gain_energy(consumption * 0.2)  # Reduced efficiency from 0.3
            
            # Cooldowns
            if predator.reproductive_cooldown > 0:
                predator.reproductive_cooldown -= 1
            if predator.hunt_cooldown > 0:
                predator.hunt_cooldown -= 1
        
        # Behavior phase
        new_offspring = []
        for predator in self.predators:
            if not predator.is_alive():
                continue
            
            species_data = self.predator_species[predator.species]
            
            # 1. Move toward prey or better habitat
            self._move_predator(predator, species_data, climate_engine)
            
            # 2. Hunt (if able)
            if predator.can_hunt():
                kill_made = self._attempt_hunt(predator, species_data, tribe_units)
                if kill_made:
                    kills_this_turn[predator.species] += 1
            
            # 3. Reproduce
            if predator.can_reproduce():
                offspring = self._reproduce_predator(predator, species_data)
                if offspring:
                    new_offspring.extend(offspring)
        
        # Add offspring
        self.predators.extend(new_offspring)
        
        # Remove dead predators
        initial_count = len(self.predators)
        
        # Collect death stats
        self.recent_deaths = {}
        dead_predators = [p for p in self.predators if not p.is_alive()]
        for p in dead_predators:
            cause = p.cause_of_death if p.cause_of_death else 'unknown'
            if cause not in self.recent_deaths:
                self.recent_deaths[cause] = 0
            self.recent_deaths[cause] += 1
            
            if self.logger_callback:
                self.logger_callback('death', p.species, details=cause)
            
        self.predators = [p for p in self.predators if p.is_alive()]
        deaths = initial_count - len(self.predators)
        
        if deaths > 0:
            # print(f"  💀 {deaths} predators died")
            pass
        
        # Track statistics
        for species_name in self.predator_species.keys():
            count = sum(1 for p in self.predators if p.species == species_name)
            self.population_history[species_name].append(count)
            self.kill_history[species_name].append(kills_this_turn[species_name])
    
    def _count_nearby_prey(self, x, y, radius):
        """Count herbivores within radius using spatial map"""
        count = 0
        # Optimization: Check square area first
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                
                if (nx, ny) in self.prey_map:
                    # Check exact distance if needed, or just use square approximation for speed
                    # Using square approximation for movement logic is usually fine and much faster
                    count += len(self.prey_map[(nx, ny)])
        return count
    
    def _attempt_hunt(self, predator, species_data, tribe_units=None):
        """Predator tries to kill nearby prey using CombatResolver"""
        # Find prey in hunting range using spatial map
        # Reduced range because we now move BEFORE hunting
        hunting_range = 2  
        
        potential_prey = []
        
        # Check herbivores
        for dy in range(-hunting_range, hunting_range + 1):
            for dx in range(-hunting_range, hunting_range + 1):
                nx = (predator.x + dx) % self.width
                ny = (predator.y + dy) % self.height
                
                if (nx, ny) in self.prey_map:
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist <= hunting_range:
                        for herbivore in self.prey_map[(nx, ny)]:
                            potential_prey.append((herbivore, dist, 'herbivore'))

        # Check tribe units
        if tribe_units:
            for unit in tribe_units:
                # Simple distance check (ignoring wrap for now for units, or handle it?)
                # Units are usually few, so iterating all is fine
                dx = unit.x - predator.x
                dy = unit.y - predator.y
                # Handle wrapping for distance calculation
                if abs(dx) > self.width / 2: dx -= np.sign(dx) * self.width
                if abs(dy) > self.height / 2: dy -= np.sign(dy) * self.height
                
                dist = np.sqrt(dx*dx + dy*dy)
                if dist <= hunting_range:
                    potential_prey.append((unit, dist, 'unit'))
        
        if not potential_prey:
            return False
        
        # Choose closest prey
        potential_prey.sort(key=lambda x: x[1])
        target, dist, target_type = potential_prey[0]
        
        # Check for pack members nearby using spatial map
        pack_members = 0
        if species_data.get('pack_bonus', 0) > 0:
            # Check immediate vicinity (radius 3)
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    nx = (predator.x + dx) % self.width
                    ny = (predator.y + dy) % self.height
                    
                    if (nx, ny) in self.spatial_map:
                        for p in self.spatial_map[(nx, ny)]:
                            if p.species == predator.species and p is not predator:
                                pack_members += 1
        
        if target_type == 'herbivore':
            # Resolve combat with herbivore
            kill, damage = self.combat_resolver.resolve_predator_hunt(
                predator, target,
                species_data,
                self.herbivores.herbivore_species[target.species],
                pack_members=pack_members
            )
            
            if kill:
                # Heal predator on kill (large meal)
                heal_amount = int(predator.combat_stats.max_hp * 0.4)
                predator.combat_stats.heal(heal_amount)
                predator.hunt_cooldown = 2  # Rest after kill
                
                # Mark prey as killed by predation
                target.cause_of_death = 'predation'
                
                if self.logger_callback:
                    self.logger_callback('predation', predator.species, target.species)
                
                return True
            elif damage > 0:
                # Small heal on hit (nibble?) or just exertion
                predator.consume_energy(0.02) # Exertion
                return False
            else:
                # Failed hunt
                predator.consume_energy(0.05)  # Chase cost
                return False
                
        elif target_type == 'unit':
            # Resolve combat with Unit
            # Simple logic for now: 50% chance to hit, damage based on predator size
            hit_chance = 0.6 + (pack_members * 0.1)
            if np.random.random() < hit_chance:
                damage = int(predator.combat_stats.attack * 0.5) # Units are tough?
                target.hp -= damage
                if self.logger_callback:
                    self.logger_callback('attack', predator.species, target.name, f"Damage: {damage}")
                
                if target.hp <= 0:
                    # Unit killed
                    if self.logger_callback:
                        self.logger_callback('kill', predator.species, target.name)
                    
                    # Heal predator
                    heal_amount = int(predator.combat_stats.max_hp * 0.5)
                    predator.combat_stats.heal(heal_amount)
                    predator.hunt_cooldown = 3
                    return True
            else:
                # Miss
                if self.logger_callback:
                    self.logger_callback('attack', predator.species, target.name, "Missed!")
                predator.consume_energy(0.05)
            return False
    
    def _move_predator(self, predator, species_data, climate_engine):
        """Move toward prey or better habitat"""
        movement_stats = predator.movement_stats
        move_range = movement_stats.movement_range
        
        # Optimization: If not hungry and in good habitat, mostly stay put or wander slowly
        is_hungry = predator.combat_stats.hp_percentage() < 0.7
        
        current_biome = self.world.biomes[predator.y, predator.x]
        biome_pref = movement_stats.terrain_preferences.get(current_biome, 0.3)
        good_habitat = biome_pref >= 0.6
        
        if not is_hungry and good_habitat:
            if np.random.random() < 0.7:
                return # Lazy predator
            # Wander randomly
            dx = np.random.choice([-1, 0, 1])
            dy = np.random.choice([-1, 0, 1])
            if dx != 0 or dy != 0:
                predator.move(dx, dy, self.width, self.height)
            return

        # --- HUNTING MOVEMENT ---
        # Scan for prey with high detection range
        detection_range = 12 # Can see/smell far
        
        best_prey_dist = 999
        target_dx, target_dy = 0, 0
        found_prey = False
        
        # Optimization: Scan in expanding rings or just check prey map?
        # Checking prey map is faster if sparse, but we don't have a global list of prey positions easily accessible 
        # except via self.prey_map which is hashed by position.
        # Iterating 12x12 area is 144 checks. Acceptable.
        
        if is_hungry:
            # Look for closest prey
            for dy in range(-detection_range, detection_range + 1):
                for dx in range(-detection_range, detection_range + 1):
                    nx = (predator.x + dx) % self.width
                    ny = (predator.y + dy) % self.height
                    
                    if (nx, ny) in self.prey_map:
                        dist = dx*dx + dy*dy # Squared distance
                        if dist < best_prey_dist:
                            best_prey_dist = dist
                            target_dx, target_dy = dx, dy
                            found_prey = True
        
        if found_prey:
            # Move towards prey at full speed
            dist = np.sqrt(best_prey_dist)
            if dist > 0:
                # Calculate how far we can move
                scale = min(1.0, move_range / dist)
                move_dx = int(target_dx * scale)
                move_dy = int(target_dy * scale)
                
                # Ensure movement if close enough
                if move_dx == 0 and move_dy == 0 and dist > 0:
                    move_dx = int(np.sign(target_dx))
                    move_dy = int(np.sign(target_dy))
                
                # Check if move is valid (not into water)
                nx = (predator.x + move_dx) % self.width
                ny = (predator.y + move_dy) % self.height
                n_biome = self.world.biomes[ny, nx]
                
                if movement_stats.can_swim or n_biome not in [0, 1]:
                    predator.move(move_dx, move_dy, self.width, self.height)
                return

        # --- HABITAT SEEKING (If no prey found) ---
        # Find direction with best habitat
        best_score = -1
        best_dx, best_dy = 0, 0
        
        search_directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dx, dy in search_directions:
            # Look ahead by move_range
            nx = (predator.x + dx * move_range) % self.width
            ny = (predator.y + dy * move_range) % self.height
            
            dest_biome = self.world.biomes[ny, nx]
            
            # Check water
            if not movement_stats.can_swim and dest_biome in [0, 1]:
                continue
                
            dest_pref = movement_stats.terrain_preferences.get(dest_biome, 0.3)
            
            if dest_pref > best_score:
                best_score = dest_pref
                best_dx, best_dy = dx * move_range, dy * move_range
        
        if best_dx != 0 or best_dy != 0:
            predator.move(best_dx, best_dy, self.width, self.height)
        else:
            # Wander (carefully)
            valid_moves = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    nx = (predator.x + dx) % self.width
                    ny = (predator.y + dy) % self.height
                    n_biome = self.world.biomes[ny, nx]
                    if movement_stats.can_swim or n_biome not in [0, 1]:
                        valid_moves.append((dx, dy))
            
            if valid_moves:
                dx, dy = valid_moves[np.random.randint(len(valid_moves))]
                predator.move(dx, dy, self.width, self.height)
    
    def _reproduce_predator(self, predator, species_data):
        """Predator produces offspring"""
        # Need mate nearby (for sexual reproduction)
        mate_nearby = False
        neighbors = 0
        search_radius = 3
        
        # Check density and mates
        for dy in range(-search_radius, search_radius + 1):
            for dx in range(-search_radius, search_radius + 1):
                nx = (predator.x + dx) % self.width
                ny = (predator.y + dy) % self.height
                
                if (nx, ny) in self.spatial_map:
                    for other in self.spatial_map[(nx, ny)]:
                        if other.species == predator.species and other is not predator:
                            neighbors += 1
                            mate_nearby = True
        
        # Density dependent reproduction control
        # If too many neighbors, don't reproduce
        if neighbors > 3:
            return []
            
        offspring_list = []
        if mate_nearby:
            # Litter size varies by species
            litter_size = 2 if species_data.get('pack_bonus', 0) > 0 else 1
            
            for _ in range(litter_size):
                if np.random.random() < 0.6:  # 60% offspring survival
                    offspring = Predator(predator.x, predator.y, predator.species)
                    # Offspring start with 50% HP
                    offspring.combat_stats.current_hp = int(offspring.combat_stats.max_hp * 0.5)
                    offspring_list.append(offspring)
            
            # Reproduction cost
            cost = int(predator.combat_stats.max_hp * 0.3)
            predator.combat_stats.take_damage(cost)
            predator.reproductive_cooldown = 8 # Increased cooldown
            
        return offspring_list
    
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
                'gazelle': 'gold', 'elephant': 'plum', 'rabbit': 'white'
            }
            for herb in self.herbivores.herbivores:
                color = herbivore_colors.get(herb.species, 'lightblue')
                ax_map.plot(herb.x, herb.y, 'o', color=color, markersize=2, alpha=0.5)
            
            # Predators (larger, darker)
            predator_colors = {
                'wolf': 'darkred', 'lion': 'orange', 'bear': 'brown',
                'leopard': 'gold', 'arctic_fox': 'white',
                'red_fox': 'orangered', 'boar': 'black', 'jackal': 'khaki'
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
    
    def spawn_migrants(self, species_name, count=2):
        """Spawn new predators at map edges (migration)"""
        spawned = 0
        attempts = 0
        max_attempts = count * 10
        
        species_data = self.predator_species[species_name]
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
            
            # Check if location is suitable
            if biome in preferred_biomes:
                predator = Predator(x, y, species_name)
                # Migrants are usually healthy
                predator.combat_stats.current_hp = int(predator.combat_stats.max_hp * 0.9)
                self.predators.append(predator)
                spawned += 1
        
        if spawned > 0:
            print(f"  🐺 {spawned} {species_name} migrated into the area")


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
