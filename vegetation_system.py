import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

class VegetationSystem:
    def __init__(self, world_generator):
        self.world = world_generator
        self.width = world_generator.width
        self.height = world_generator.height
        
        # Vegetation density (0.0 = barren, 1.0 = maximum growth)
        self.density = np.zeros((self.height, self.width))
        
        # Biome-specific growth rates (per turn under ideal conditions)
        self.biome_growth_rates = {
            0: 0.0,    # Deep Ocean - no land vegetation
            1: 0.0,    # Shallow Ocean
            2: 0.05,   # Beach - sparse vegetation
            3: 0.02,   # Desert - very slow
            4: 0.15,   # Savanna - moderate with seasonal variation
            5: 0.20,   # Grassland - fast growth
            6: 0.25,   # Tropical Rainforest - maximum growth
            7: 0.20,   # Temperate Forest - good growth
            8: 0.12,   # Taiga - slow but steady
            9: 0.08,   # Tundra - very slow
            10: 0.0,   # Snow - no growth
            11: 0.03,  # Mountain - sparse alpine vegetation
        }
        
        # Biome-specific maximum density
        self.biome_max_density = {
            0: 0.0, 1: 0.0, 2: 0.3, 3: 0.2, 4: 0.6, 5: 0.8,
            6: 1.0, 7: 0.9, 8: 0.7, 9: 0.4, 10: 0.0, 11: 0.3
        }
        
        # Seed initial vegetation (sparse)
        self._seed_initial_vegetation()
    
    def _seed_initial_vegetation(self):
        """Place initial sparse vegetation across suitable biomes"""
        for y in range(self.height):
            for x in range(self.width):
                biome = self.world.biomes[y, x]
                max_density = self.biome_max_density.get(biome, 0.0)
                
                if max_density > 0 and np.random.random() < 0.3:  # 30% initial colonization
                    self.density[y, x] = np.random.uniform(0.1, 0.3) * max_density
    
    def update(self, climate_engine):
        """Update vegetation growth/death based on climate"""
        new_density = self.density.copy()
        
        for y in range(self.height):
            for x in range(self.width):
                biome = self.world.biomes[y, x]
                current_density = self.density[y, x]
                
                # Get environmental factors
                temp = self.world.temperature[y, x]
                moisture = self.world.moisture[y, x]
                
                # Base growth rate from biome
                base_growth = self.biome_growth_rates.get(biome, 0.0)
                max_density = self.biome_max_density.get(biome, 0.0)
                
                if base_growth > 0:
                    # Climate suitability modifiers
                    temp_factor = self._temperature_suitability(biome, temp)
                    moisture_factor = self._moisture_suitability(biome, moisture)
                    
                    # Seasonal modifier
                    season_factor = self._seasonal_modifier(climate_engine.season, biome)
                    
                    # Crowding factor (logistic growth)
                    crowding_factor = 1.0 - (current_density / max_density) if max_density > 0 else 0
                    
                    # Calculate growth
                    growth = (base_growth * temp_factor * moisture_factor * 
                             season_factor * crowding_factor)
                    
                    # Apply growth
                    new_density[y, x] = min(max_density, current_density + growth)
                    
                    # Die-back from harsh conditions
                    if temp < 0.1 or moisture < 0.05:
                        die_back = 0.1  # 10% die-off per turn in harsh conditions
                        new_density[y, x] = max(0, new_density[y, x] - die_back)
                    
                    # Spread to adjacent cells (seed dispersal)
                    if current_density > 0.3 and np.random.random() < 0.2:  # 20% chance if established
                        self._spread_seeds(x, y, new_density)
        
        self.density = new_density
        
        # Apply weather event effects
        self._apply_storm_effects(climate_engine.storms)
        self._apply_drought_effects(climate_engine.droughts)
    
    def _temperature_suitability(self, biome, temp):
        """How suitable is this temperature for this biome's vegetation?"""
        # Each biome has an optimal temperature range
        optimal_temps = {
            2: (0.6, 0.9),   # Beach - warm
            3: (0.7, 1.0),   # Desert - hot
            4: (0.6, 0.9),   # Savanna - warm
            5: (0.4, 0.7),   # Grassland - temperate
            6: (0.7, 1.0),   # Tropical Rainforest - hot
            7: (0.4, 0.7),   # Temperate Forest - moderate
            8: (0.2, 0.5),   # Taiga - cold
            9: (0.0, 0.3),   # Tundra - very cold
            11: (0.2, 0.6),  # Mountain - cool
        }
        
        if biome not in optimal_temps:
            return 1.0
        
        min_temp, max_temp = optimal_temps[biome]
        
        # Linear falloff outside optimal range
        if temp < min_temp:
            return max(0.2, temp / min_temp)
        elif temp > max_temp:
            return max(0.2, (1.0 - temp) / (1.0 - max_temp))
        else:
            return 1.0
    
    def _moisture_suitability(self, biome, moisture):
        """How suitable is this moisture level for this biome's vegetation?"""
        optimal_moisture = {
            2: (0.3, 0.6),   # Beach
            3: (0.0, 0.3),   # Desert - low moisture
            4: (0.3, 0.6),   # Savanna - moderate
            5: (0.4, 0.7),   # Grassland
            6: (0.7, 1.0),   # Tropical Rainforest - high moisture
            7: (0.5, 0.8),   # Temperate Forest
            8: (0.3, 0.6),   # Taiga
            9: (0.2, 0.5),   # Tundra
            11: (0.3, 0.7),  # Mountain
        }
        
        if biome not in optimal_moisture:
            return 1.0
        
        min_moist, max_moist = optimal_moisture[biome]
        
        if moisture < min_moist:
            return max(0.1, moisture / min_moist) if min_moist > 0 else 0.1
        elif moisture > max_moist:
            return max(0.5, (1.0 - moisture) / (1.0 - max_moist))
        else:
            return 1.0
    
    def _seasonal_modifier(self, season, biome):
        """Seasonal growth multipliers"""
        # 0=Spring, 1=Summer, 2=Fall, 3=Winter
        
        # Tropical biomes have consistent growth
        if biome in [6]:  # Rainforest
            return 1.0
        
        # Temperate biomes have seasonal variation
        if biome in [5, 7]:  # Grassland, Temperate Forest
            return [1.2, 0.9, 0.7, 0.3][season]
        
        # Cold biomes have extreme seasonal variation
        if biome in [8, 9]:  # Taiga, Tundra
            return [0.8, 1.0, 0.5, 0.0][season]
        
        # Desert/Savanna have wet/dry seasons
        if biome in [3, 4]:
            return [1.0, 0.5, 0.8, 0.6][season]
        
        return 1.0
    
    def _spread_seeds(self, x, y, new_density):
        """Spread vegetation to adjacent cells"""
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for dx, dy in directions:
            nx = (x + dx) % self.width
            ny = (y + dy) % self.height
            
            target_biome = self.world.biomes[ny, nx]
            
            # Can only spread to similar biomes or compatible adjacent ones
            source_biome = self.world.biomes[y, x]
            
            if self.biome_max_density.get(target_biome, 0) > 0:
                # Small chance to colonize empty suitable land
                if new_density[ny, nx] < 0.1 and np.random.random() < 0.1:
                    new_density[ny, nx] = 0.05  # Pioneer species
    
    def _apply_storm_effects(self, storms):
        """Storms can damage or stimulate vegetation"""
        for storm in storms:
            for dy in range(-storm['radius'], storm['radius'] + 1):
                for dx in range(-storm['radius'], storm['radius'] + 1):
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist <= storm['radius']:
                        ny = (storm['y'] + dy) % self.height
                        nx = (storm['x'] + dx) % self.width
                        
                        if storm['type'] == 'hurricane':
                            # Hurricanes damage vegetation
                            damage = storm['intensity'] * 0.2 * (1.0 - dist/storm['radius'])
                            self.density[ny, nx] = max(0, self.density[ny, nx] - damage)
                        else:
                            # Regular storms provide moisture boost (slight growth bonus next turn)
                            pass
    
    def _apply_drought_effects(self, droughts):
        """Droughts kill vegetation"""
        for drought in droughts:
            for dy in range(-drought['radius'], drought['radius'] + 1):
                for dx in range(-drought['radius'], drought['radius'] + 1):
                    dist = np.sqrt(dx*dx + dy*dy)
                    if dist <= drought['radius']:
                        ny = (drought['y'] + dy) % self.height
                        nx = (drought['x'] + dx) % self.width
                        
                        # Drought causes die-back
                        falloff = 1.0 - (dist / drought['radius'])
                        die_back = drought['severity'] * 0.15 * falloff
                        self.density[ny, nx] = max(0, self.density[ny, nx] - die_back)
    
    def visualize(self, show_biomes=True):
        """Display vegetation density, optionally with biome overlay"""
        if show_biomes:
            fig, axes = plt.subplots(1, 2, figsize=(15, 7))
            
            # Biomes
            biome_colors = [
                '#001a33', '#003d66', '#f4e7d7', '#f4d03f', '#d4a574', '#7fb069',
                '#2d5016', '#4a7c4e', '#1a4d2e', '#a8b8b0', '#ffffff', '#8b7d6b',
            ]
            cmap_biome = LinearSegmentedColormap.from_list('biomes', biome_colors, N=12)
            axes[0].imshow(self.world.biomes, cmap=cmap_biome, interpolation='nearest', vmin=0, vmax=11)
            axes[0].set_title('Biomes')
            axes[0].axis('off')
            
            # Vegetation density
            axes[1].imshow(self.density, cmap='YlGn', vmin=0, vmax=1)
            axes[1].set_title('Vegetation Density')
            axes[1].axis('off')
        else:
            plt.figure(figsize=(10, 7))
            plt.imshow(self.density, cmap='YlGn', vmin=0, vmax=1)
            plt.title('Vegetation Density')
            plt.colorbar(label='Density')
            plt.axis('off')
        
        plt.tight_layout()
        plt.show()


# Integrated simulation
if __name__ == "__main__":
    from terrain_generator import WorldGenerator
    from climate_engine import ClimateEngine
    
    # Generate world
    print("=== WORLD GENESIS ===")
    world = WorldGenerator(width=150, height=100, seed=42)
    world.generate_world(sea_level=0.42)
    
    # Initialize systems
    climate = ClimateEngine(world)
    vegetation = VegetationSystem(world)
    
    print("\n=== INITIAL STATE ===")
    vegetation.visualize()
    
    # Run simulation
    print("\n=== BEGINNING SIMULATION ===")
    for turn in range(20):  # 5 years
        climate.advance_turn()
        vegetation.update(climate)
        
        # Visualize every 4 turns (once per year)
        if turn % 4 == 3:
            print(f"\n--- Year {climate.year} Complete ---")
            vegetation.visualize()
    
    print("\n=== SIMULATION COMPLETE ===")
    print(f"Final vegetation coverage: {np.sum(vegetation.density > 0.1) / vegetation.density.size * 100:.1f}%")
    print(f"Average density (vegetated areas): {np.mean(vegetation.density[vegetation.density > 0.1]):.2f}")
