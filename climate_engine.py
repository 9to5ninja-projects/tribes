import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from terrain_generator import WorldGenerator

class ClimateEngine:
    def __init__(self, world_generator):
        self.world = world_generator
        self.width = world_generator.width
        self.height = world_generator.height
        
        # Time tracking
        self.current_turn = 0
        self.season = 0  # 0=Spring, 1=Summer, 2=Fall, 3=Winter
        self.year = 0
        
        # Store base values (unchanging foundation)
        self.base_temperature = self.world.temperature.copy()
        self.base_moisture = self.world.moisture.copy()
        
        # Active weather systems
        self.storms = []  # List of active storm systems
        self.droughts = []  # List of drought zones
        
        # Weather event thresholds
        self.storm_threshold = 0.85  # High moisture + temp differential
        self.drought_threshold = 0.15  # Very low moisture
        
    def advance_turn(self):
        """Progress time by one turn (one season)"""
        self.current_turn += 1
        self.season = self.current_turn % 4
        if self.season == 0:
            self.year += 1
        
        print(f"\n=== Year {self.year}, {self._season_name()} ===")
        
        # Update climate based on season
        self._apply_seasonal_shift()
        
        # Generate and process weather events
        self._generate_weather_events()
        self._process_storms()
        self._process_droughts()
        
    def _season_name(self):
        return ["Spring", "Summer", "Fall", "Winter"][self.season]
    
    def _apply_seasonal_shift(self):
        """Modify temperature and moisture based on current season"""
        # Seasonal temperature shifts
        # Summer: +warmth in north, ++warmth in south
        # Winter: --cold in north, -cold in south
        
        for y in range(self.height):
            latitude_factor = abs(y - self.height/2) / (self.height/2)
            
            for x in range(self.width):
                base_temp = self.base_temperature[y, x]
                base_moist = self.base_moisture[y, x]
                
                # Temperature modulation
                if self.season == 1:  # Summer
                    # Warmer everywhere, especially at poles
                    temp_shift = 0.15 + (latitude_factor * 0.2)
                elif self.season == 3:  # Winter
                    # Colder everywhere, especially at poles
                    temp_shift = -0.15 - (latitude_factor * 0.3)
                else:  # Spring/Fall
                    # Moderate temperatures
                    temp_shift = 0.0
                
                self.world.temperature[y, x] = np.clip(base_temp + temp_shift, 0, 1)
                
                # Moisture modulation (seasonal rainfall patterns)
                if self.season == 0:  # Spring - increased rainfall
                    moist_shift = 0.1
                elif self.season == 1:  # Summer - drier inland
                    if self.world.elevation[y, x] > 0.5:  # High elevation
                        moist_shift = -0.15
                    else:
                        moist_shift = -0.05
                elif self.season == 2:  # Fall - moderate rainfall
                    moist_shift = 0.05
                else:  # Winter - snow/rain depending on temp
                    if self.world.temperature[y, x] < 0.3:
                        moist_shift = 0.1  # Snow accumulation
                    else:
                        moist_shift = 0.0
                
                self.world.moisture[y, x] = np.clip(base_moist + moist_shift, 0, 1)
        
        # Add seasonal noise variation
        season_noise = np.random.randn(self.height, self.width) * 0.03
        self.world.temperature += season_noise
        self.world.moisture += season_noise
        
        self.world.temperature = np.clip(self.world.temperature, 0, 1)
        self.world.moisture = np.clip(self.world.moisture, 0, 1)
    
    def _generate_weather_events(self):
        """Spawn storms and droughts based on atmospheric conditions"""
        # Clear old events
        self.storms = [s for s in self.storms if s['duration'] > 0]
        self.droughts = [d for d in self.droughts if d['duration'] > 0]
        
        # Scan for storm conditions (high moisture + temperature differential)
        for _ in range(np.random.randint(1, 4)):  # 1-3 potential storms per turn
            y = np.random.randint(0, self.height)
            x = np.random.randint(0, self.width)
            
            if self.world.moisture[y, x] > self.storm_threshold:
                # Check for temperature gradient nearby (instability)
                local_temp = self.world.temperature[max(0,y-2):min(self.height,y+3), 
                                                     max(0,x-2):min(self.width,x+3)]
                temp_variance = np.std(local_temp)
                
                if temp_variance > 0.1:  # Significant gradient = storm potential
                    storm = {
                        'x': x,
                        'y': y,
                        'intensity': np.random.uniform(0.5, 1.0),
                        'radius': np.random.randint(3, 8),
                        'duration': np.random.randint(1, 3),  # Lasts 1-3 turns
                        'type': 'hurricane' if self.world.temperature[y, x] > 0.7 else 'thunderstorm'
                    }
                    self.storms.append(storm)
                    print(f"  🌀 {storm['type'].capitalize()} forming at ({x}, {y})")
        
        # Scan for drought conditions (very low moisture in non-water areas)
        for _ in range(np.random.randint(0, 2)):  # 0-2 potential droughts
            y = np.random.randint(0, self.height)
            x = np.random.randint(0, self.width)
            
            if (self.world.moisture[y, x] < self.drought_threshold and 
                self.world.elevation[y, x] > 0.4):  # Land only
                drought = {
                    'x': x,
                    'y': y,
                    'severity': 1.0 - self.world.moisture[y, x],
                    'radius': np.random.randint(5, 12),
                    'duration': np.random.randint(2, 5)  # Droughts last longer
                }
                self.droughts.append(drought)
                print(f"  ☀️ Drought beginning at ({x}, {y})")
    
    def _process_storms(self):
        """Apply storm effects to affected areas"""
        for storm in self.storms:
            # Increase moisture in storm area
            for dy in range(-storm['radius'], storm['radius'] + 1):
                for dx in range(-storm['radius'], storm['radius'] + 1):
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist <= storm['radius']:
                        ny = (storm['y'] + dy) % self.height
                        nx = (storm['x'] + dx) % self.width
                        
                        # Moisture boost (rainfall)
                        falloff = 1.0 - (dist / storm['radius'])
                        moisture_increase = storm['intensity'] * 0.3 * falloff
                        self.world.moisture[ny, nx] = min(1.0, 
                            self.world.moisture[ny, nx] + moisture_increase)
                        
                        # Slight temperature drop (cooling from rain)
                        temp_decrease = storm['intensity'] * 0.1 * falloff
                        self.world.temperature[ny, nx] = max(0.0,
                            self.world.temperature[ny, nx] - temp_decrease)
            
            storm['duration'] -= 1
            if storm['duration'] <= 0:
                print(f"  🌤️ {storm['type'].capitalize()} dissipating")
    
    def _process_droughts(self):
        """Apply drought effects to affected areas"""
        for drought in self.droughts:
            # Decrease moisture in drought area
            for dy in range(-drought['radius'], drought['radius'] + 1):
                for dx in range(-drought['radius'], drought['radius'] + 1):
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist <= drought['radius']:
                        ny = (drought['y'] + dy) % self.height
                        nx = (drought['x'] + dx) % self.width
                        
                        # Only affect land
                        if self.world.elevation[ny, nx] > 0.4:
                            falloff = 1.0 - (dist / drought['radius'])
                            moisture_decrease = drought['severity'] * 0.15 * falloff
                            self.world.moisture[ny, nx] = max(0.0,
                                self.world.moisture[ny, nx] - moisture_decrease)
                            
                            # Temperature increase (heat from sun)
                            temp_increase = drought['severity'] * 0.08 * falloff
                            self.world.temperature[ny, nx] = min(1.0,
                                self.world.temperature[ny, nx] + temp_increase)
            
            drought['duration'] -= 1
            if drought['duration'] <= 0:
                print(f"  🌧️ Drought ending")
    
    def visualize_climate(self):
        """Display current climate state with weather overlays"""
        fig, axes = plt.subplots(1, 2, figsize=(15, 7))
        
        # Temperature map with storms
        temp_display = self.world.temperature.copy()
        axes[0].imshow(temp_display, cmap='RdYlBu_r')
        axes[0].set_title(f'Temperature - {self._season_name()} (Year {self.year})')
        
        # Mark storms
        for storm in self.storms:
            circle = plt.Circle((storm['x'], storm['y']), storm['radius'], 
                               color='purple', fill=False, linewidth=2, alpha=0.7)
            axes[0].add_patch(circle)
            axes[0].plot(storm['x'], storm['y'], 'w*', markersize=15)
        
        axes[0].axis('off')
        
        # Moisture map with droughts
        moist_display = self.world.moisture.copy()
        axes[1].imshow(moist_display, cmap='Blues')
        axes[1].set_title(f'Moisture - {self._season_name()} (Year {self.year})')
        
        # Mark droughts
        for drought in self.droughts:
            circle = plt.Circle((drought['x'], drought['y']), drought['radius'],
                               color='red', fill=False, linewidth=2, alpha=0.7)
            axes[1].add_patch(circle)
            axes[1].plot(drought['x'], drought['y'], 'r+', markersize=15, markeredgewidth=3)
        
        axes[1].axis('off')
        
        plt.tight_layout()
        plt.show()

# Run simulation
if __name__ == "__main__":
    # Generate world
    world = WorldGenerator(width=150, height=100, seed=42)
    world.generate_world(sea_level=0.42)
    
    # Initialize climate engine
    climate = ClimateEngine(world)
    
    # Run for several years
    for turn in range(12):  # 3 years (4 seasons each)
        climate.advance_turn()
        climate.visualize_climate()
        
        # Update biomes based on new climate
        world.generate_biomes(sea_level=0.42)
