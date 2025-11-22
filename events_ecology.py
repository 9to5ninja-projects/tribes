import numpy as np
import matplotlib.pyplot as plt

class Scavenger:
    """Opportunistic feeders that consume carrion"""
    def __init__(self, x, y, species_name):
        self.x = x
        self.y = y
        self.species = species_name
        self.energy = 1.0
        self.age = 0
        self.reproductive_cooldown = 0
        self.cause_of_death = None
    
    def move(self, dx, dy, world_width, world_height):
        self.x = (self.x + dx) % world_width
        self.y = (self.y + dy) % world_height
    
    def consume_energy(self, amount):
        self.energy = max(0, self.energy - amount)
    
    def gain_energy(self, amount):
        self.energy = min(1.0, self.energy + amount)
    
    def is_alive(self):
        return self.energy > 0


class AvianCreature:
    """Flying species - birds, raptors"""
    def __init__(self, x, y, species_name):
        self.x = x
        self.y = y
        self.species = species_name
        self.energy = 1.0
        self.age = 0
        self.reproductive_cooldown = 0
        self.migration_target = None  # For migratory species
        self.cause_of_death = None
    
    def move(self, dx, dy, world_width, world_height):
        self.x = (self.x + dx) % world_width
        self.y = (self.y + dy) % world_height
    
    def consume_energy(self, amount):
        self.energy = max(0, self.energy - amount)
    
    def gain_energy(self, amount):
        self.energy = min(1.0, self.energy + amount)
    
    def is_alive(self):
        return self.energy > 0


class AquaticCreature:
    """Water-dwelling species"""
    def __init__(self, x, y, species_name):
        self.x = x
        self.y = y
        self.species = species_name
        self.energy = 1.0
        self.age = 0
        self.reproductive_cooldown = 0
        self.cause_of_death = None
    
    def move(self, dx, dy, world_width, world_height):
        self.x = (self.x + dx) % world_width
        self.y = (self.y + dy) % world_height
    
    def consume_energy(self, amount):
        self.energy = max(0, self.energy - amount)
    
    def gain_energy(self, amount):
        self.energy = min(1.0, self.energy + amount)
    
    def is_alive(self):
        return self.energy > 0


class Disease:
    """Disease outbreak affecting animal populations"""
    def __init__(self, x, y, disease_type, virulence, duration):
        self.x = x
        self.y = y
        self.type = disease_type  # 'herbivore' or 'predator' or 'all'
        self.virulence = virulence  # 0-1, how deadly
        self.spread_rate = virulence * 0.5  # How fast it spreads
        self.duration = duration
        self.radius = 5
        self.infected_animals = set()  # Track which animals are infected


class NaturalDisaster:
    """Catastrophic events affecting the ecosystem"""
    def __init__(self, x, y, disaster_type, intensity, duration):
        self.x = x
        self.y = y
        self.type = disaster_type  # 'wildfire', 'flood', 'earthquake', 'blizzard'
        self.intensity = intensity
        self.duration = duration
        self.radius = np.random.randint(8, 20)


class InsectSystem:
    """Tracks insect population density across the map"""
    def __init__(self, width, height, world_generator):
        self.width = width
        self.height = height
        self.world = world_generator
        self.density = np.zeros((height, width))
    
    def update(self, climate_engine, vegetation_system):
        # Insects thrive in warm, moist, vegetated areas
        # Growth
        temp_factor = np.clip(self.world.temperature, 0, 1)
        moist_factor = np.clip(self.world.moisture, 0, 1)
        veg_factor = vegetation_system.density
        
        # Seasonality
        season_mod = 1.0
        if climate_engine.season == 3: # Winter
            season_mod = 0.1
        elif climate_engine.season == 1: # Summer
            season_mod = 1.5
            
        growth = 0.3 * temp_factor * moist_factor * veg_factor * season_mod
        
        self.density += growth
            
        # Natural decay / carrying capacity
        self.density *= 0.95
        self.density = np.clip(self.density, 0, 1.0)
        
    def consume(self, x, y, amount):
        available = self.density[y, x]
        consumed = min(available, amount)
        self.density[y, x] -= consumed
        return consumed


class EventsEcologySystem:
    def __init__(self, world_generator, vegetation_system, animal_system, predator_system):
        self.world = world_generator
        self.vegetation = vegetation_system
        self.herbivores = animal_system
        self.predators = predator_system
        self.width = world_generator.width
        self.height = world_generator.height
        
        # Sub-systems
        self.insects = InsectSystem(self.width, self.height, self.world)
        
        # Populations
        self.scavengers = []
        self.avian_creatures = []
        self.aquatic_creatures = []
        
        # Active events
        self.diseases = []
        self.disasters = []
        self.carrion_locations = []  # (x, y, energy_value, age)
        
        # Statistics
        self.disease_deaths = 0
        self.disaster_deaths = 0
        self.scavenger_history = []
        self.avian_history = []
        self.aquatic_history = []
        
        # Event logging
        self.recent_events = []
        self.logger_callback = None

    def set_logger(self, callback):
        """Set callback for logging interactions"""
        self.logger_callback = callback

    def get_recent_events(self):
        """Return and clear recent events"""
        events = self.recent_events[:]
        self.recent_events = []
        return events
    
    def spawn_scavengers(self, count=30):
        """Spawn scavengers (vultures, hyenas, crows)"""
        for _ in range(count):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            
            # Scavengers spawn near land
            if self.world.elevation[y, x] > 0.4:
                scavenger = Scavenger(x, y, 'scavenger')
                scavenger.energy = 0.6
                self.scavengers.append(scavenger)
        
        print(f"  🦅 Spawned {len(self.scavengers)} scavengers")
    
    def spawn_avian_species(self, count=80):
        """Spawn birds - mix of herbivorous and carnivorous"""
        species_types = ['songbird', 'waterfowl', 'raptor', 'seabird', 'insectivore']
        
        for _ in range(count):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            species = np.random.choice(species_types)
            
            bird = AvianCreature(x, y, species)
            bird.energy = 0.7
            self.avian_creatures.append(bird)
        
        print(f"  🦜 Spawned {len(self.avian_creatures)} avian creatures")
    
    def spawn_aquatic_species(self, count=100):
        """Spawn fish and marine life"""
        spawned = 0
        for _ in range(count * 2):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            
            # Only spawn in water
            if self.world.elevation[y, x] < 0.4:
                rand = np.random.random()
                if rand < 0.6:
                    species = 'fish'
                elif rand < 0.8:
                    species = 'predatory_fish'
                elif rand < 0.95:
                    species = 'marine_mammal'
                else:
                    species = 'shark'
                    
                aquatic = AquaticCreature(x, y, species)
                aquatic.energy = 0.8
                self.aquatic_creatures.append(aquatic)
                spawned += 1
                if spawned >= count:
                    break
        
        print(f"  🐟 Spawned {len(self.aquatic_creatures)} aquatic creatures")
    
    def update(self, climate_engine):
        """Update all ecological events and species"""
        # Update insects
        self.insects.update(climate_engine, self.vegetation)

        # Track carrion (dead animals become food for scavengers)
        self._track_carrion()
        
        # Handle migration (re-population)
        self._handle_migration(climate_engine)
        
        # Update diseases
        self._update_diseases()
        
        # Update disasters
        self._update_disasters(climate_engine)
        
        # Generate new events
        self._generate_events(climate_engine)
        
        # Update scavengers
        self._update_scavengers()
        
        # Update avian species
        self._update_avian(climate_engine)
        
        # Update aquatic species
        self._update_aquatic()
        
        # Log deaths before cleanup
        if self.logger_callback:
            for s in self.scavengers:
                if not s.is_alive():
                    cause = s.cause_of_death if s.cause_of_death else 'starvation'
                    self.logger_callback('death', s.species, details=cause)
            
            for a in self.avian_creatures:
                if not a.is_alive():
                    cause = a.cause_of_death if a.cause_of_death else 'starvation'
                    if a.age > 100 and cause == 'starvation': cause = 'old_age'
                    self.logger_callback('death', a.species, details=cause)
            
            for a in self.aquatic_creatures:
                if not a.is_alive():
                    cause = a.cause_of_death if a.cause_of_death else 'starvation'
                    if a.age > 120 and cause == 'starvation': cause = 'old_age'
                    self.logger_callback('death', a.species, details=cause)

        # Clean up dead creatures
        self.scavengers = [s for s in self.scavengers if s.is_alive()]
        self.avian_creatures = [a for a in self.avian_creatures if a.is_alive()]
        self.aquatic_creatures = [a for a in self.aquatic_creatures if a.is_alive()]
        
        # Track populations
        self.scavenger_history.append(len(self.scavengers))
        self.avian_history.append(len(self.avian_creatures))
        self.aquatic_history.append(len(self.aquatic_creatures))
    
    def _track_carrion(self):
        """Create carrion markers from dead animals"""
        # Age existing carrion
        self.carrion_locations = [(x, y, energy * 0.8, age + 1) 
                                  for x, y, energy, age in self.carrion_locations 
                                  if age < 5 and energy > 0.05]  # Decays over time
        
        # Add new carrion from recent deaths
        # (In a real implementation, we'd track individual deaths, but we'll simulate)
        death_chance = 0.05  # Increased chance of finding carrion each turn
        for _ in range(int(death_chance * 100)):
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            if self.world.elevation[y, x] > 0.4:  # On land
                self.carrion_locations.append((x, y, 0.5, 0))
    
    def _update_diseases(self):
        """Process active disease outbreaks"""
        for disease in self.diseases:
            # Spread to nearby animals
            if disease.type in ['herbivore', 'all']:
                for animal in self.herbivores.herbivores:
                    dist = np.sqrt((animal.x - disease.x)**2 + (animal.y - disease.y)**2)
                    if dist < disease.radius:
                        animal_id = id(animal)
                        if animal_id not in disease.infected_animals:
                            if np.random.random() < disease.spread_rate:
                                disease.infected_animals.add(animal_id)
                                # Apply damage
                                animal.consume_energy(disease.virulence * 0.3)
                                if not animal.is_alive():
                                    animal.cause_of_death = f"disease_{disease.type}"
                                    self.disease_deaths += 1
            
            if disease.type in ['predator', 'all']:
                for pred in self.predators.predators:
                    dist = np.sqrt((pred.x - disease.x)**2 + (pred.y - disease.y)**2)
                    if dist < disease.radius:
                        pred_id = id(pred)
                        if pred_id not in disease.infected_animals:
                            if np.random.random() < disease.spread_rate:
                                disease.infected_animals.add(pred_id)
                                pred.consume_energy(disease.virulence * 0.3)
                                if not pred.is_alive():
                                    pred.cause_of_death = f"disease_{disease.type}"
                                    self.disease_deaths += 1
            
            disease.duration -= 1
            disease.radius += 1  # Disease spreads outward
        
        # Remove expired diseases
        self.diseases = [d for d in self.diseases if d.duration > 0]
    
    def _update_disasters(self, climate_engine):
        """Process active natural disasters"""
        for disaster in self.disasters:
            if disaster.type == 'wildfire':
                # Burns vegetation, kills animals
                for dy in range(-disaster.radius, disaster.radius + 1):
                    for dx in range(-disaster.radius, disaster.radius + 1):
                        dist = np.sqrt(dx*dx + dy*dy)
                        if dist <= disaster.radius:
                            ny = (disaster.y + dy) % self.height
                            nx = (disaster.x + dx) % self.width
                            
                            # Burn vegetation
                            burn_amount = disaster.intensity * (1 - dist / disaster.radius)
                            self.vegetation.density[ny, nx] *= (1 - burn_amount * 0.8)
                            
                            # Kill animals in fire
                            for animal in self.herbivores.herbivores:
                                if animal.x == nx and animal.y == ny:
                                    if np.random.random() < burn_amount * 0.5:
                                        animal.energy = 0
                                        animal.cause_of_death = 'wildfire'
                                        self.disaster_deaths += 1
                            
                            for pred in self.predators.predators:
                                if pred.x == nx and pred.y == ny:
                                    if np.random.random() < burn_amount * 0.4:
                                        pred.energy = 0
                                        pred.cause_of_death = 'wildfire'
                                        self.disaster_deaths += 1
            
            elif disaster.type == 'flood':
                # Drowns land animals, increases moisture
                for dy in range(-disaster.radius, disaster.radius + 1):
                    for dx in range(-disaster.radius, disaster.radius + 1):
                        dist = np.sqrt(dx*dx + dy*dy)
                        if dist <= disaster.radius:
                            ny = (disaster.y + dy) % self.height
                            nx = (disaster.x + dx) % self.width
                            
                            # Increase moisture
                            self.world.moisture[ny, nx] = min(1.0, 
                                self.world.moisture[ny, nx] + disaster.intensity * 0.3)
                            
                            # Kill animals
                            for animal in self.herbivores.herbivores:
                                if animal.x == nx and animal.y == ny:
                                    if np.random.random() < disaster.intensity * 0.3:
                                        animal.energy = 0
                                        animal.cause_of_death = 'flood'
                                        self.disaster_deaths += 1
            
            elif disaster.type == 'blizzard':
                # Freezes animals, covers vegetation
                for dy in range(-disaster.radius, disaster.radius + 1):
                    for dx in range(-disaster.radius, disaster.radius + 1):
                        dist = np.sqrt(dx*dx + dy*dy)
                        if dist <= disaster.radius:
                            ny = (disaster.y + dy) % self.height
                            nx = (disaster.x + dx) % self.width
                            
                            # Cold damage to animals
                            for animal in self.herbivores.herbivores:
                                if animal.x == nx and animal.y == ny:
                                    animal.consume_energy(disaster.intensity * 0.2)
                                    if not animal.is_alive():
                                        animal.cause_of_death = 'blizzard'
                                        self.disaster_deaths += 1
            
            disaster.duration -= 1
        
        # Remove expired disasters
        self.disasters = [d for d in self.disasters if d.duration > 0]
    
    def _generate_events(self, climate_engine):
        """Randomly spawn diseases and disasters"""
        # Disease outbreak chance
        if np.random.random() < 0.02:  # 2% chance per turn
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            
            disease_type = np.random.choice(['herbivore', 'predator', 'all'])
            virulence = np.random.uniform(0.3, 0.8)
            duration = np.random.randint(5, 15)
            
            disease = Disease(x, y, disease_type, virulence, duration)
            self.diseases.append(disease)
            event_msg = f"Disease outbreak ({disease_type}) at ({x}, {y})"
            print(f"  🦠 {event_msg}")
            self.recent_events.append(event_msg)
        
        # Natural disaster chance (higher in certain seasons/conditions)
        disaster_chance = 0.01
        
        # Wildfires more likely in summer, dry areas
        if climate_engine.season == 1:  # Summer
            disaster_chance += 0.02
        
        if np.random.random() < disaster_chance:
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            
            # Choose disaster type based on biome/season
            temp = self.world.temperature[y, x]
            moisture = self.world.moisture[y, x]
            
            if temp > 0.7 and moisture < 0.3:
                disaster_type = 'wildfire'
            elif moisture > 0.8:
                disaster_type = 'flood'
            elif temp < 0.2:
                disaster_type = 'blizzard'
            else:
                disaster_type = np.random.choice(['wildfire', 'flood', 'blizzard'])
            
            intensity = np.random.uniform(0.5, 1.0)
            duration = np.random.randint(2, 6)
            
            disaster = NaturalDisaster(x, y, disaster_type, intensity, duration)
            self.disasters.append(disaster)
            event_msg = f"{disaster_type.capitalize()} at ({x}, {y}), radius {disaster.radius}"
            print(f"  🔥 {event_msg}")
            self.recent_events.append(event_msg)
    
    def _update_scavengers(self):
        """Update scavenger behavior - seek carrion"""
        for scavenger in self.scavengers:
            scavenger.age += 1
            scavenger.consume_energy(0.06)  # Low metabolism
            
            # Look for nearby carrion
            best_dist = float('inf')
            best_carrion_idx = None
            
            for i, (cx, cy, energy, age) in enumerate(self.carrion_locations):
                dist = np.sqrt((cx - scavenger.x)**2 + (cy - scavenger.y)**2)
                if dist < best_dist and energy > 0.1:
                    best_dist = dist
                    best_carrion_idx = i
            
            # Move toward carrion
            if best_carrion_idx is not None and best_dist > 0:
                cx, cy, energy, age = self.carrion_locations[best_carrion_idx]
                dx = np.sign(cx - scavenger.x)
                dy = np.sign(cy - scavenger.y)
                
                if dx != 0 or dy != 0:
                    scavenger.move(dx, dy, self.width, self.height)
                    scavenger.consume_energy(0.02)
                
                # If reached carrion, eat it
                if scavenger.x == cx and scavenger.y == cy:
                    consumption = min(energy, 0.4)
                    scavenger.gain_energy(consumption * 0.5)
                    # Update carrion
                    self.carrion_locations[best_carrion_idx] = (cx, cy, energy - consumption, age)
            
            # Reproduce if healthy
            if scavenger.energy > 0.7 and scavenger.age > 5 and scavenger.reproductive_cooldown == 0:
                if np.random.random() < 0.1:
                    offspring = Scavenger(scavenger.x, scavenger.y, 'scavenger')
                    offspring.energy = 0.5
                    self.scavengers.append(offspring)
                    scavenger.reproductive_cooldown = 8
            
            if scavenger.reproductive_cooldown > 0:
                scavenger.reproductive_cooldown -= 1
    
    def _update_avian(self, climate_engine):
        """Update bird behavior"""
        # Spatial map for avian predation
        avian_map = {}
        for bird in self.avian_creatures:
            pos = (bird.x, bird.y)
            if pos not in avian_map:
                avian_map[pos] = []
            avian_map[pos].append(bird)
            
        # Global population pressure
        total_avian = len(self.avian_creatures)
        global_crowding = max(1.0, total_avian / 800.0) # Soft cap around 800

        for bird in self.avian_creatures:
            bird.age += 1
            bird.consume_energy(0.05)  # Low metabolism, efficient
            
            # Old age death
            if bird.age > 100:
                bird.consume_energy(0.1) # Rapid aging
            
            # Different feeding strategies
            if bird.species == 'songbird':
                # Eat insects first
                insects = self.insects.consume(bird.x, bird.y, 0.2)
                if insects > 0.05:
                    bird.gain_energy(insects)
                    if self.logger_callback and np.random.random() < 0.1:
                        self.logger_callback('predation', bird.species, 'insect')
                else:
                    # Eat seeds (vegetation)
                    veg = self.vegetation.density[bird.y, bird.x]
                    if veg > 0.1:
                        bird.gain_energy(0.08)
            
            elif bird.species == 'insectivore':
                # Eat insects
                insects = self.insects.consume(bird.x, bird.y, 0.3)
                if insects > 0.05:
                    bird.gain_energy(insects)
                    if self.logger_callback and np.random.random() < 0.1:
                        self.logger_callback('predation', bird.species, 'insect')
            
            elif bird.species == 'waterfowl':
                # Need to be near water
                if self.world.elevation[bird.y, bird.x] < 0.45:  # Near water
                    # Eat insects or aquatic plants
                    insects = self.insects.consume(bird.x, bird.y, 0.15)
                    bird.gain_energy(insects + 0.1)
                    if self.logger_callback and insects > 0.05 and np.random.random() < 0.1:
                        self.logger_callback('predation', bird.species, 'insect')
            
            elif bird.species == 'raptor':
                # Hunt small prey (birds or herbivores)
                hunted = False
                # Try to hunt other birds first (internal predation)
                if (bird.x, bird.y) in avian_map:
                    for prey in avian_map[(bird.x, bird.y)]:
                        if prey is not bird and prey.species in ['songbird', 'insectivore', 'waterfowl']:
                            if np.random.random() < 0.3: # 30% success
                                prey.energy = 0 # Kill
                                prey.cause_of_death = 'predation'
                                bird.gain_energy(0.5)
                                hunted = True
                                if self.logger_callback:
                                    self.logger_callback('predation', bird.species, prey.species)
                                break
                
                if not hunted:
                    # Hunt herbivores
                    if np.random.random() < 0.05:  # 5% hunt success
                        bird.gain_energy(0.4)
            
            elif bird.species == 'seabird':
                # Eat fish
                for fish in self.aquatic_creatures:
                    if fish.species == 'fish':
                        dist = np.sqrt((fish.x - bird.x)**2 + (fish.y - bird.y)**2)
                        if dist < 2:
                            if np.random.random() < 0.1:
                                fish.energy = 0
                                fish.cause_of_death = 'predation'
                                bird.gain_energy(0.3)
                                if self.logger_callback:
                                    self.logger_callback('predation', bird.species, fish.species)
                                break
            
            # Migration behavior (simplified - move toward better climate)
            if climate_engine.season in [0, 2]:  # Spring/Fall - migration seasons
                if np.random.random() < 0.3:
                    # Birds can move farther
                    dx = np.random.choice([-2, -1, 0, 1, 2])
                    dy = np.random.choice([-2, -1, 0, 1, 2])
                    bird.move(dx, dy, self.width, self.height)
                    bird.consume_energy(0.03)
            
            # Reproduce - Density dependent
            # Count neighbors
            neighbors = 0
            if (bird.x, bird.y) in avian_map:
                neighbors = len(avian_map[(bird.x, bird.y)])
            
            # Lower reproduction if crowded (local AND global)
            repro_chance = 0.15 * (1.0 / (1.0 + neighbors * 0.5)) * (1.0 / global_crowding)
            
            if bird.energy > 0.65 and bird.age > 3 and bird.reproductive_cooldown == 0:
                if np.random.random() < repro_chance:
                    # Reduced clutch size
                    clutch_size = 1
                    if np.random.random() < 0.3: clutch_size = 2
                    
                    for _ in range(clutch_size):  
                        if np.random.random() < 0.6:
                            chick = AvianCreature(bird.x, bird.y, bird.species)
                            chick.energy = 0.4
                            self.avian_creatures.append(chick)
                    bird.reproductive_cooldown = 8 # Increased cooldown
            
            if bird.reproductive_cooldown > 0:
                bird.reproductive_cooldown -= 1
    
    def _update_aquatic(self):
        """Update fish and marine life"""
        # Spatial map for aquatic predation and density
        aquatic_map = {}
        for aq in self.aquatic_creatures:
            pos = (aq.x, aq.y)
            if pos not in aquatic_map:
                aquatic_map[pos] = []
            aquatic_map[pos].append(aq)
            
        # Global population pressure
        total_aquatic = len(self.aquatic_creatures)
        global_crowding = max(1.0, total_aquatic / 1200.0) # Soft cap around 1200

        for aquatic in self.aquatic_creatures:
            aquatic.age += 1
            aquatic.consume_energy(0.04)
            
            # Old age death
            if aquatic.age > 120:
                aquatic.consume_energy(0.1)
            
            # Stay in water
            if self.world.elevation[aquatic.y, aquatic.x] >= 0.4:
                # Beached! Try to return to water
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        ny = (aquatic.y + dy) % self.height
                        nx = (aquatic.x + dx) % self.width
                        if self.world.elevation[ny, nx] < 0.4:
                            aquatic.move(dx, dy, self.width, self.height)
                            break
            else:
                # Feed based on water conditions
                temp = self.world.temperature[aquatic.y, aquatic.x]
                
                if aquatic.species == 'fish':
                    # Fish thrive in moderate temps
                    if 0.4 < temp < 0.7:
                        aquatic.gain_energy(0.12)
                    
                    # Eat insects if near surface/land
                    insects = self.insects.consume(aquatic.x, aquatic.y, 0.1)
                    if insects > 0.01:
                        aquatic.gain_energy(insects)
                        if self.logger_callback and np.random.random() < 0.1:
                            self.logger_callback('predation', aquatic.species, 'insect')
                    
                    # School behavior - move randomly
                    if np.random.random() < 0.4:
                        dx = np.random.choice([-1, 0, 1])
                        dy = np.random.choice([-1, 0, 1])
                        nx = (aquatic.x + dx) % self.width
                        ny = (aquatic.y + dy) % self.height
                        if self.world.elevation[ny, nx] < 0.4:
                            aquatic.move(dx, dy, self.width, self.height)
                
                elif aquatic.species == 'predatory_fish':
                    # Hunt smaller fish
                    if (aquatic.x, aquatic.y) in aquatic_map:
                        for prey in aquatic_map[(aquatic.x, aquatic.y)]:
                            if prey.species == 'fish':
                                if np.random.random() < 0.2:
                                    prey.energy = 0
                                    prey.cause_of_death = 'predation'
                                    aquatic.gain_energy(0.3)
                                    if self.logger_callback:
                                        self.logger_callback('predation', aquatic.species, prey.species)
                                    break
                
                elif aquatic.species == 'marine_mammal':
                    # Larger, hunt fish
                    if (aquatic.x, aquatic.y) in aquatic_map:
                        for prey in aquatic_map[(aquatic.x, aquatic.y)]:
                            if prey.species in ['fish', 'predatory_fish']:
                                if np.random.random() < 0.15:
                                    prey.energy = 0
                                    prey.cause_of_death = 'predation'
                                    aquatic.gain_energy(0.25)
                                    if self.logger_callback:
                                        self.logger_callback('predation', aquatic.species, prey.species)
                                    break
                
                elif aquatic.species == 'shark':
                    # Apex predator
                    if (aquatic.x, aquatic.y) in aquatic_map:
                        for prey in aquatic_map[(aquatic.x, aquatic.y)]:
                            if prey is not aquatic and prey.species in ['fish', 'predatory_fish', 'marine_mammal']:
                                if np.random.random() < 0.25:
                                    prey.energy = 0
                                    prey.cause_of_death = 'predation'
                                    aquatic.gain_energy(0.4)
                                    if self.logger_callback:
                                        self.logger_callback('predation', aquatic.species, prey.species)
                                    break
            
            # Density check
            neighbors = 0
            if (aquatic.x, aquatic.y) in aquatic_map:
                neighbors = len(aquatic_map[(aquatic.x, aquatic.y)])
            
            # Overcrowding penalty
            if neighbors > 5:
                aquatic.consume_energy(0.01 * (neighbors - 5))
            
            # Reproduce
            repro_chance = 0.2 * (1.0 / (1.0 + neighbors * 0.3)) * (1.0 / global_crowding)
            
            if aquatic.energy > 0.7 and aquatic.age > 4 and aquatic.reproductive_cooldown == 0:
                if np.random.random() < repro_chance:
                    offspring_count = 3 if aquatic.species == 'fish' else 1
                    for _ in range(offspring_count):
                        if np.random.random() < 0.5:
                            baby = AquaticCreature(aquatic.x, aquatic.y, aquatic.species)
                            baby.energy = 0.5
                            self.aquatic_creatures.append(baby)
                    aquatic.reproductive_cooldown = 8
            
            if aquatic.reproductive_cooldown > 0:
                aquatic.reproductive_cooldown -= 1
    
    def _handle_migration(self, climate_engine):
        """Allow species to migrate back if extinct or low population"""
        # DISABLED: User requested true extinctions
        return

        # Only migrate in Spring/Summer/Fall (not Winter)
        if climate_engine.season == 3:
            return

        # Check Herbivores
        for species in self.herbivores.herbivore_species.keys():
            count = sum(1 for h in self.herbivores.herbivores if h.species == species)
            if count < 8: # Critically low
                # Chance to migrate increases if population is 0
                chance = 0.1 if count > 0 else 0.2
                if np.random.random() < chance:
                    self.herbivores.spawn_migrants(species, count=np.random.randint(3, 8))

        # Check Predators
        for species in self.predators.predator_species.keys():
            count = sum(1 for p in self.predators.predators if p.species == species)
            if count < 3:
                chance = 0.05 if count > 0 else 0.15
                if np.random.random() < chance:
                    self.predators.spawn_migrants(species, count=np.random.randint(2, 4))
    
    def get_statistics(self):
        """Return ecosystem statistics"""
        return {
            'scavengers': len(self.scavengers),
            'avian': len(self.avian_creatures),
            'aquatic': len(self.aquatic_creatures),
            'insects': int(np.sum(self.insects.density)),
            'active_diseases': len(self.diseases),
            'active_disasters': len(self.disasters),
            'carrion_sites': len(self.carrion_locations),
            'disease_deaths': self.disease_deaths,
            'disaster_deaths': self.disaster_deaths
        }
    
    def visualize(self):
        """Visualize the complete ecology"""
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 3, height_ratios=[2, 1])
        
        # Main ecosystem map
        ax_main = fig.add_subplot(gs[0, :])
        
        # Background: terrain
        terrain_display = np.zeros((self.height, self.width, 3))
        for y in range(self.height):
            for x in range(self.width):
                elev = self.world.elevation[y, x]
                if elev < 0.4:
                    terrain_display[y, x] = [0, 0.2, 0.5]  # Water - blue
                else:
                    veg = self.vegetation.density[y, x]
                    terrain_display[y, x] = [0.8 - veg * 0.6, 0.6 + veg * 0.4, 0.3]  # Land - brown to green
        
        ax_main.imshow(terrain_display)
        
        # Plot all creatures
        # Aquatic
        for aq in self.aquatic_creatures:
            ax_main.plot(aq.x, aq.y, 'o', color='cyan', markersize=1, alpha=0.6)
        
        # Herbivores
        for herb in self.herbivores.herbivores:
            ax_main.plot(herb.x, herb.y, 'o', color='tan', markersize=2, alpha=0.5)
        
        # Predators
        for pred in self.predators.predators:
            ax_main.plot(pred.x, pred.y, '^', color='red', markersize=4, alpha=0.7)
        
        # Avian
        for bird in self.avian_creatures:
            color = {'songbird': 'yellow', 'waterfowl': 'lightblue', 
                    'raptor': 'orange', 'seabird': 'white'}.get(bird.species, 'gray')
            ax_main.plot(bird.x, bird.y, '*', color=color, markersize=3, alpha=0.6)
        
        # Scavengers
        for scav in self.scavengers:
            ax_main.plot(scav.x, scav.y, 'v', color='brown', markersize=3, alpha=0.7)
        
        # Events
        for disease in self.diseases:
            circle = plt.Circle((disease.x, disease.y), disease.radius, 
                               color='purple', fill=False, linewidth=2, alpha=0.7, linestyle='--')
            ax_main.add_patch(circle)
        
        for disaster in self.disasters:
            color = {'wildfire': 'red', 'flood': 'blue', 'blizzard': 'white'}.get(disaster.type, 'gray')
            circle = plt.Circle((disaster.x, disaster.y), disaster.radius,
                               color=color, fill=False, linewidth=3, alpha=0.8)
            ax_main.add_patch(circle)
        
        ax_main.set_title('Complete Ecosystem (cyan=aquatic, tan=herbivore, red=predator, stars=birds, brown=scavenger)')
        ax_main.axis('off')
        
        # Population graphs
        ax_scav = fig.add_subplot(gs[1, 0])
        if self.scavenger_history:
            ax_scav.plot(self.scavenger_history, color='brown', label='Scavengers')
        ax_scav.set_title('Scavenger Population')
        ax_scav.grid(True, alpha=0.3)
        
        ax_avian = fig.add_subplot(gs[1, 1])
        if self.avian_history:
            ax_avian.plot(self.avian_history, color='orange', label='Avian')
        ax_avian.set_title('Avian Population')
        ax_avian.grid(True, alpha=0.3)
        
        ax_aquatic = fig.add_subplot(gs[1, 2])
        if self.aquatic_history:
            ax_aquatic.plot(self.aquatic_history, color='cyan', label='Aquatic')
        ax_aquatic.set_title('Aquatic Population')
        ax_aquatic.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


# Full ecosystem with events
if __name__ == "__main__":
    from terrain_generator import WorldGenerator
    from climate_engine import ClimateEngine
    from vegetation_system import VegetationSystem
    from animal_system import AnimalSystem
    from predator_system import PredatorSystem
    
    print("=== COMPLETE ECOSYSTEM SIMULATION ===\n")
    
    # World generation
    print("Generating world...")
    world = WorldGenerator(width=150, height=100, seed=42)
    world.generate_world(sea_level=0.42)
    
    # Initialize systems
    climate = ClimateEngine(world)
    vegetation = VegetationSystem(world)
    
    # Establish vegetation
    print("Establishing vegetation (5 years)...")
    for turn in range(20):
        climate.advance_turn()
        vegetation.update(climate)
    
    # Spawn herbivores
    print("\nSpawning herbivores...")
    animals = AnimalSystem(world, vegetation)
    animals.spawn_initial_populations(population_per_species=100)
    
    # Establish herbivores
    print("Herbivores establishing (3 years)...")
    for turn in range(12):
        climate.advance_turn()
        vegetation.update(climate)
        animals.update(climate)
    
    # Spawn predators
    print("\nSpawning predators...")
    predators = PredatorSystem(world, vegetation, animals)
    predators.spawn_initial_populations(population_per_species=15)
    
    # Let predator-prey stabilize
    print("Predator-prey stabilizing (2 years)...")
    for turn in range(8):
        climate.advance_turn()
        vegetation.update(climate)
        animals.update(climate)
        predators.update(climate)
    
    # Add complete ecology
    print("\n=== INTRODUCING COMPLETE ECOLOGY ===")
    ecology = EventsEcologySystem(world, vegetation, animals, predators)
    ecology.spawn_scavengers(count=40)
    ecology.spawn_avian_species(count=100)
    ecology.spawn_aquatic_species(count=150)
    
    # Full simulation
    print("\n=== FULL ECOSYSTEM RUNNING (20 years) ===\n")
    for turn in range(80):
        climate.advance_turn()
        vegetation.update(climate)
        animals.update(climate)
        predators.update(climate)
        ecology.update(climate)
        
        # Report every 4 years
        if turn % 16 == 15:
            stats = ecology.get_statistics()
            print(f"\n--- Year {climate.year} Full Report ---")
            print(f"Vegetation coverage: {np.sum(vegetation.density > 0.1) / vegetation.density.size * 100:.1f}%")
            print(f"Herbivores: {len(animals.herbivores)}")
            print(f"Predators: {len(predators.predators)}")
            print(f"Scavengers: {stats['scavengers']}")
            print(f"Avian: {stats['avian']}")
            print(f"Aquatic: {stats['aquatic']}")
            print(f"Active diseases: {stats['active_diseases']}")
            print(f"Active disasters: {stats['active_disasters']}")
            print(f"Deaths from disease: {stats['disease_deaths']}")
            print(f"Deaths from disasters: {stats['disaster_deaths']}")
            
            # Visualize every 8 years
            if climate.year % 8 == 0:
                ecology.visualize()
    
    print("\n=== ECOSYSTEM SIMULATION COMPLETE ===")
    print("The world is alive and ready for civilizations.")
