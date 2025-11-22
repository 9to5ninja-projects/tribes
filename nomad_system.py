import numpy as np
import uuid
from srpg_combat import CombatResolver

class NomadHunter:
    def __init__(self, x, y):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.hp = 20
        self.max_hp = 20
        self.energy = 100
        self.max_energy = 100
        self.age = 0
        self.kills = 0
        self.name = f"Hunter {str(uuid.uuid4())[:4]}"
    
    def is_alive(self):
        return self.hp > 0 and self.energy > 0

class NomadBand:
    def __init__(self, x, y, size=5):
        self.id = str(uuid.uuid4())
        self.x = x
        self.y = y
        self.members = [NomadHunter(x, y) for _ in range(size)]
        self.food_stock = 50
        self.target_pos = None
        self.state = 'wander' # wander, hunt, rest
        self.cooldown = 0
        self.home_range_center = (x, y)

class NomadSystem:
    def __init__(self, world, animal_system):
        self.world = world
        self.animals = animal_system
        self.bands = []
        self.width = world.width
        self.height = world.height
        self.combat_resolver = CombatResolver(world)
        self.logger_callback = None
        
        # Stats
        self.total_kills = 0
        self.total_deaths = 0
        self.population_history = []
        
    def set_logger(self, callback):
        self.logger_callback = callback
        
    def spawn_nomads(self, count=5):
        spawned = 0
        attempts = 0
        while spawned < count and attempts < 100:
            attempts += 1
            x = np.random.randint(0, self.width)
            y = np.random.randint(0, self.height)
            # Spawn on land
            if self.world.elevation[y, x] > 0.4:
                band = NomadBand(x, y, size=np.random.randint(3, 8))
                self.bands.append(band)
                spawned += 1
        print(f"  🏹 Spawned {len(self.bands)} nomad bands")
        
        # Initial history
        self.population_history.append(sum(len(b.members) for b in self.bands))
        
    def update(self):
        active_bands = []
        
        for band in self.bands:
            # Remove dead members
            band.members = [m for m in band.members if m.is_alive()]
            
            if not band.members:
                continue # Band wiped out
            
            active_bands.append(band)
            
            # Update members
            for member in band.members:
                member.age += 1
                member.energy -= 0.5 # Metabolism
                if member.energy <= 0:
                    member.hp -= 5 # Starvation damage
                    if member.hp <= 0:
                        self.total_deaths += 1
                        if self.logger_callback:
                            self.logger_callback('death', 'nomad', 'starvation')
            
            # Consume food from stock
            food_needed = len(band.members) * 2
            if band.food_stock >= food_needed:
                band.food_stock -= food_needed
                # Heal members
                for member in band.members:
                    member.energy = min(member.max_energy, member.energy + 5)
                    member.hp = min(member.max_hp, member.hp + 1)
            else:
                # Partial feeding
                eaten = band.food_stock
                band.food_stock = 0
                # Distribute energy
                energy_per_person = (eaten / len(band.members)) * 2
                for member in band.members:
                    member.energy = min(member.max_energy, member.energy + energy_per_person)
            
            # Band Behavior
            if band.cooldown > 0:
                band.cooldown -= 1
                continue
                
            # 1. Scan for animals
            prey_found = None
            min_dist = 999
            
            # Look in radius 6 (Reduced from 8 for performance)
            scan_radius = 6
            for dy in range(-scan_radius, scan_radius + 1):
                for dx in range(-scan_radius, scan_radius + 1):
                    nx = (band.x + dx) % self.width
                    ny = (band.y + dy) % self.height
                    
                    # Check animal system spatial map if available, else iterate (slow)
                    # Assuming animal_system has spatial_map updated
                    if hasattr(self.animals, 'spatial_map') and (nx, ny) in self.animals.spatial_map:
                        animals_here = self.animals.spatial_map[(nx, ny)]
                        if animals_here:
                            dist = np.sqrt(dx*dx + dy*dy)
                            if dist < min_dist:
                                min_dist = dist
                                prey_found = (nx, ny)
            
            if prey_found:
                # Move towards prey
                tx, ty = prey_found
                dx = np.sign(tx - band.x) # Simple sign, ignoring wrap for now
                dy = np.sign(ty - band.y)
                
                # Handle wrap logic roughly
                if abs(tx - band.x) > self.width / 2: dx *= -1
                if abs(ty - band.y) > self.height / 2: dy *= -1
                
                # Move band
                band.x = (band.x + int(dx)) % self.width
                band.y = (band.y + int(dy)) % self.height
                
                # Update members position
                for member in band.members:
                    member.x = band.x
                    member.y = band.y
                
                # If close, hunt!
                if min_dist <= 1.5:
                    self._hunt(band, tx, ty)
            else:
                # Wander
                if np.random.random() < 0.3:
                    dx = np.random.choice([-1, 0, 1])
                    dy = np.random.choice([-1, 0, 1])
                    band.x = (band.x + dx) % self.width
                    band.y = (band.y + dy) % self.height
                    for member in band.members:
                        member.x = band.x
                        member.y = band.y
            
            # Reproduction (Recruitment)
            if band.food_stock > 100 and len(band.members) < 10:
                if np.random.random() < 0.1:
                    new_member = NomadHunter(band.x, band.y)
                    band.members.append(new_member)
                    band.food_stock -= 50
                    if self.logger_callback:
                        self.logger_callback('birth', 'nomad', 'recruitment')

        self.bands = active_bands
        
        # Update history
        self.population_history.append(sum(len(b.members) for b in self.bands))

    def _hunt(self, band, tx, ty):
        # Get animals at target
        if (tx, ty) not in self.animals.spatial_map:
            return
            
        prey_list = self.animals.spatial_map[(tx, ty)]
        if not prey_list:
            return
            
        target_animal = prey_list[0]
        
        # Simple combat: Band power vs Animal HP
        # Each hunter deals 2-4 damage
        total_damage = 0
        for member in band.members:
            if member.energy > 10:
                dmg = np.random.randint(2, 5)
                total_damage += dmg
                member.energy -= 5
        
        # Apply damage
        target_animal.combat_stats.take_damage(total_damage)
        
        if not target_animal.is_alive():
            target_animal.cause_of_death = 'hunted_by_nomads'
            # Gain food
            meat = target_animal.combat_stats.max_hp * 0.5 # 50% yield
            band.food_stock += meat
            self.total_kills += 1
            band.cooldown = 2 # Rest after kill
            
            if self.logger_callback:
                self.logger_callback('kill', 'nomad', target_animal.species)
        else:
            # Animal flees?
            pass

    def get_statistics(self):
        total_pop = sum(len(b.members) for b in self.bands)
        return {
            'bands': len(self.bands),
            'population': total_pop,
            'kills': self.total_kills,
            'deaths': self.total_deaths
        }
