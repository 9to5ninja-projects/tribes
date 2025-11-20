import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

class WorldGenerator:
    def __init__(self, width=100, height=100, seed=None):
        self.width = width
        self.height = height
        self.seed = seed
        if seed:
            np.random.seed(seed)
        
        # Core data layers
        self.elevation = np.zeros((height, width))
        self.temperature = np.zeros((height, width))
        self.moisture = np.zeros((height, width))
        self.biomes = np.zeros((height, width), dtype=int)
        
    def generate_noise_map(self, scale=50.0, octaves=6, persistence=0.5, lacunarity=2.0):
        """Generate Perlin-like noise using multiple octaves of random interpolation"""
        noise_map = np.zeros((self.height, self.width))
        
        for octave in range(octaves):
            freq = lacunarity ** octave
            amp = persistence ** octave
            
            # Create random gradient grid for this octave
            grid_size = int(max(self.width, self.height) / scale * freq) + 2
            gradients = np.random.randn(grid_size, grid_size, 2)
            
            # Sample and interpolate
            for y in range(self.height):
                for x in range(self.width):
                    # Scale coordinates
                    sx = x / scale * freq
                    sy = y / scale * freq
                    
                    # Grid cell coordinates
                    x0 = int(sx)
                    y0 = int(sy)
                    x1 = x0 + 1
                    y1 = y0 + 1
                    
                    # Interpolation weights
                    wx = sx - x0
                    wy = sy - y0
                    
                    # Smoothstep interpolation
                    wx = wx * wx * (3 - 2 * wx)
                    wy = wy * wy * (3 - 2 * wy)
                    
                    # Sample corners (with wrapping)
                    x0 = x0 % grid_size
                    x1 = x1 % grid_size
                    y0 = y0 % grid_size
                    y1 = y1 % grid_size
                    
                    # Dot products with gradients
                    v00 = np.dot(gradients[y0, x0], [sx - x0, sy - y0])
                    v10 = np.dot(gradients[y0, x1], [sx - x1, sy - y0])
                    v01 = np.dot(gradients[y1, x0], [sx - x0, sy - y1])
                    v11 = np.dot(gradients[y1, x1], [sx - x1, sy - y1])
                    
                    # Bilinear interpolation
                    v0 = v00 * (1 - wx) + v10 * wx
                    v1 = v01 * (1 - wx) + v11 * wx
                    value = v0 * (1 - wy) + v1 * wy
                    
                    noise_map[y, x] += value * amp
        
        # Normalize to 0-1 range
        noise_map = (noise_map - noise_map.min()) / (noise_map.max() - noise_map.min())
        return noise_map
    
    def generate_elevation(self, sea_level=0.4, mountain_threshold=0.7):
        """Create elevation map with distinct land/sea/mountain regions"""
        self.elevation = self.generate_noise_map(scale=40.0, octaves=6)
        
        # Apply island mask (optional - creates continent in center)
        # center_x, center_y = self.width // 2, self.height // 2
        # for y in range(self.height):
        #     for x in range(self.width):
        #         dx = (x - center_x) / self.width
        #         dy = (y - center_y) / self.height
        #         distance = np.sqrt(dx*dx + dy*dy)
        #         self.elevation[y, x] *= (1 - distance * 1.5)
        
        self.elevation = np.clip(self.elevation, 0, 1)
        
    def generate_temperature(self):
        """Temperature based on latitude and elevation"""
        for y in range(self.height):
            # Latitude effect (colder at poles)
            latitude_factor = abs(y - self.height/2) / (self.height/2)
            base_temp = 1.0 - latitude_factor * 0.8
            
            for x in range(self.width):
                # Elevation effect (colder at high elevation)
                elevation_penalty = max(0, self.elevation[y, x] - 0.5) * 0.6
                self.temperature[y, x] = max(0, base_temp - elevation_penalty)
        
        # Add noise for variation
        temp_noise = self.generate_noise_map(scale=60.0, octaves=3) * 0.15
        self.temperature += temp_noise
        self.temperature = np.clip(self.temperature, 0, 1)
    
    def generate_moisture(self, sea_level=0.4):
        """Moisture based on proximity to water and rainfall patterns"""
        # Start with base moisture from water proximity
        self.moisture = np.zeros((self.height, self.width))
        
        for y in range(self.height):
            for x in range(self.width):
                # If water, max moisture
                if self.elevation[y, x] < sea_level:
                    self.moisture[y, x] = 1.0
                else:
                    # Find distance to nearest water
                    min_dist = float('inf')
                    search_radius = 15
                    for dy in range(-search_radius, search_radius + 1):
                        for dx in range(-search_radius, search_radius + 1):
                            ny = (y + dy) % self.height
                            nx = (x + dx) % self.width
                            if self.elevation[ny, nx] < sea_level:
                                dist = np.sqrt(dx*dx + dy*dy)
                                min_dist = min(min_dist, dist)
                    
                    # Moisture decreases with distance from water
                    moisture_from_water = max(0, 1.0 - min_dist / search_radius)
                    self.moisture[y, x] = moisture_from_water * 0.6
        
        # Add rainfall patterns (noise)
        rain_noise = self.generate_noise_map(scale=45.0, octaves=4) * 0.5
        self.moisture += rain_noise
        self.moisture = np.clip(self.moisture, 0, 1)
    
    def generate_biomes(self, sea_level=0.4):
        """Derive biomes from temperature and moisture"""
        # Biome indices:
        # 0: Deep Ocean, 1: Shallow Ocean, 2: Beach
        # 3: Desert, 4: Savanna, 5: Grassland
        # 6: Tropical Rainforest, 7: Temperate Forest, 8: Taiga
        # 9: Tundra, 10: Snow, 11: Mountain
        
        for y in range(self.height):
            for x in range(self.width):
                elev = self.elevation[y, x]
                temp = self.temperature[y, x]
                moist = self.moisture[y, x]
                
                # Water biomes
                if elev < sea_level - 0.1:
                    self.biomes[y, x] = 0  # Deep Ocean
                elif elev < sea_level:
                    self.biomes[y, x] = 1  # Shallow Ocean
                elif elev < sea_level + 0.05:
                    self.biomes[y, x] = 2  # Beach
                # Mountain
                elif elev > 0.75:
                    self.biomes[y, x] = 11  # Mountain
                elif elev > 0.65 and temp < 0.3:
                    self.biomes[y, x] = 10  # Snow
                # Land biomes based on temp and moisture
                elif temp > 0.7:  # Hot
                    if moist > 0.6:
                        self.biomes[y, x] = 6  # Tropical Rainforest
                    elif moist > 0.3:
                        self.biomes[y, x] = 4  # Savanna
                    else:
                        self.biomes[y, x] = 3  # Desert
                elif temp > 0.4:  # Temperate
                    if moist > 0.5:
                        self.biomes[y, x] = 7  # Temperate Forest
                    else:
                        self.biomes[y, x] = 5  # Grassland
                elif temp > 0.2:  # Cold
                    if moist > 0.3:
                        self.biomes[y, x] = 8  # Taiga
                    else:
                        self.biomes[y, x] = 9  # Tundra
                else:  # Very cold
                    self.biomes[y, x] = 10  # Snow
    
    def generate_world(self, sea_level=0.4):
        """Generate complete world with all layers"""
        print("Generating elevation...")
        self.generate_elevation(sea_level=sea_level)
        print("Generating temperature...")
        self.generate_temperature()
        print("Generating moisture...")
        self.generate_moisture(sea_level=sea_level)
        print("Deriving biomes...")
        self.generate_biomes(sea_level=sea_level)
        print("World generation complete!")
    
    def visualize(self):
        """Display all layers"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 15))
        
        # Elevation
        axes[0, 0].imshow(self.elevation, cmap='terrain')
        axes[0, 0].set_title('Elevation')
        axes[0, 0].axis('off')
        
        # Temperature
        axes[0, 1].imshow(self.temperature, cmap='RdYlBu_r')
        axes[0, 1].set_title('Temperature')
        axes[0, 1].axis('off')
        
        # Moisture
        axes[1, 0].imshow(self.moisture, cmap='Blues')
        axes[1, 0].set_title('Moisture')
        axes[1, 0].axis('off')
        
        # Biomes with custom colors
        biome_colors = [
            '#001a33',  # Deep Ocean
            '#003d66',  # Shallow Ocean
            '#f4e7d7',  # Beach
            '#f4d03f',  # Desert
            '#d4a574',  # Savanna
            '#7fb069',  # Grassland
            '#2d5016',  # Tropical Rainforest
            '#4a7c4e',  # Temperate Forest
            '#1a4d2e',  # Taiga
            '#a8b8b0',  # Tundra
            '#ffffff',  # Snow
            '#8b7d6b',  # Mountain
        ]
        cmap = LinearSegmentedColormap.from_list('biomes', biome_colors, N=12)
        axes[1, 1].imshow(self.biomes, cmap=cmap, interpolation='nearest', vmin=0, vmax=11)
        axes[1, 1].set_title('Biomes')
        axes[1, 1].axis('off')
        
        plt.tight_layout()
        plt.show()

# Generate and visualize
world = WorldGenerator(width=150, height=100, seed=42)
world.generate_world(sea_level=0.42)
world.visualize()
