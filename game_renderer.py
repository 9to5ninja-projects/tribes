"""
Proper tile-based SRPG renderer with grid, sprites, and UI.
"""

import pygame
import numpy as np
from srpg_stats import HERBIVORE_STATS, PREDATOR_STATS

# Initialize Pygame
pygame.init()

# Display settings
TILE_SIZE = 32  # Base tile size in pixels
MIN_ZOOM = 0.5
MAX_ZOOM = 3.0

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (200, 200, 200)
GRID_COLOR = (60, 60, 60)
SELECTION_COLOR = (255, 255, 0)
HOVER_COLOR = (255, 255, 255, 100)

# Biome colors (unchanged)
BIOME_COLORS = {
    0: (0, 26, 51),      # Deep Ocean
    1: (0, 61, 102),     # Shallow Ocean
    2: (244, 231, 215),  # Beach
    3: (244, 208, 63),   # Desert
    4: (212, 165, 116),  # Savanna
    5: (127, 176, 105),  # Grassland
    6: (45, 80, 22),     # Tropical Rainforest
    7: (74, 124, 78),    # Temperate Forest
    8: (26, 77, 46),     # Taiga
    9: (168, 184, 176),  # Tundra
    10: (255, 255, 255), # Snow
    11: (139, 125, 107), # Mountain
}


class SpriteManager:
    """Manages sprite generation for entities"""
    
    def __init__(self, tile_size=32):
        self.tile_size = tile_size
        self.sprites = {}
        self._generate_sprites()
    
    def _generate_sprites(self):
        """Generate simple iconic sprites for each entity type"""
        
        # Herbivores - circles with unique colors
        herbivore_colors = {
            'deer': (139, 90, 43),      # Brown
            'bison': (101, 67, 33),     # Dark brown
            'caribou': (169, 169, 169), # Gray
            'gazelle': (210, 180, 140), # Tan
            'elephant': (128, 128, 128), # Gray
            'rabbit': (255, 255, 255),  # White/Light Gray
            'musk_ox': (60, 40, 20),    # Very Dark Brown
            'iguana': (34, 139, 34),    # Forest Green
            'frog': (50, 205, 50)       # Lime Green
        }
        
        for species, color in herbivore_colors.items():
            surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            # Draw circle
            radius = self.tile_size // 3
            if species in ['rabbit', 'frog']: radius = self.tile_size // 4 # Smaller
            
            center = self.tile_size // 2
            pygame.draw.circle(surf, color, (center, center), radius)
            pygame.draw.circle(surf, WHITE, (center, center), radius, 2)  # Outline
            
            # Add species identifier (first letter)
            font = pygame.font.Font(None, self.tile_size // 2)
            text = font.render(species[0].upper(), True, WHITE)
            text_rect = text.get_rect(center=(center, center))
            surf.blit(text, text_rect)
            
            self.sprites[f'herbivore_{species}'] = surf
        
        # Predators - triangles with unique colors
        predator_colors = {
            'wolf': (139, 0, 0),        # Dark red
            'lion': (218, 165, 32),     # Goldenrod
            'bear': (101, 67, 33),      # Brown
            'leopard': (255, 215, 0),   # Gold
            'arctic_fox': (240, 248, 255), # White
            'red_fox': (255, 69, 0),    # Red-Orange
            'boar': (80, 50, 20),       # Dark Brown/Black
            'jackal': (189, 183, 107),  # Dark Khaki
            'polar_bear': (250, 250, 255), # White
            'snow_leopard': (220, 220, 220), # Light Gray
            'crocodile': (0, 100, 0),   # Dark Green
            'snake': (107, 142, 35),    # Olive Drab
            'giant_toad': (85, 107, 47) # Dark Olive Green
        }
        
        for species, color in predator_colors.items():
            surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            # Draw triangle pointing up
            points = [
                (self.tile_size // 2, self.tile_size // 6),           # Top
                (self.tile_size // 6, self.tile_size * 5 // 6),       # Bottom left
                (self.tile_size * 5 // 6, self.tile_size * 5 // 6)   # Bottom right
            ]
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, WHITE, points, 2)  # Outline
            
            self.sprites[f'predator_{species}'] = surf
        
        # Avian - stars
        avian_colors = {
            'songbird': (255, 255, 0),      # Yellow
            'waterfowl': (135, 206, 250),   # Light blue
            'raptor': (255, 140, 0),        # Orange
            'seabird': (255, 255, 255),     # White
            'insectivore': (144, 238, 144)  # Light Green
        }
        
        for species, color in avian_colors.items():
            surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            # Draw 5-pointed star
            center = self.tile_size // 2
            outer_radius = self.tile_size // 3
            inner_radius = self.tile_size // 6
            
            points = []
            for i in range(10):
                angle = (i * 36 - 90) * np.pi / 180
                radius = outer_radius if i % 2 == 0 else inner_radius
                x = center + int(radius * np.cos(angle))
                y = center + int(radius * np.sin(angle))
                points.append((x, y))
            
            pygame.draw.polygon(surf, color, points)
            pygame.draw.polygon(surf, WHITE, points, 1)
            
            self.sprites[f'avian_{species}'] = surf
        
        # Scavenger - diamond
        surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        center = self.tile_size // 2
        size = self.tile_size // 3
        points = [
            (center, center - size),      # Top
            (center + size, center),      # Right
            (center, center + size),      # Bottom
            (center - size, center)       # Left
        ]
        pygame.draw.polygon(surf, (101, 67, 33), points)
        pygame.draw.polygon(surf, WHITE, points, 2)
        self.sprites['scavenger'] = surf
        
        # Aquatic - small circles (fish)
        surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (0, 191, 255), (self.tile_size // 2, self.tile_size // 2), self.tile_size // 5)
        self.sprites['aquatic_fish'] = surf
        
        surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (0, 100, 200), (self.tile_size // 2, self.tile_size // 2), self.tile_size // 4)
        self.sprites['aquatic_marine_mammal'] = surf

        # Predatory Fish - slightly larger, darker blue
        surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        pygame.draw.circle(surf, (0, 0, 139), (self.tile_size // 2, self.tile_size // 2), self.tile_size // 4)
        self.sprites['aquatic_predatory_fish'] = surf

        # Shark - Triangle
        surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
        points = [
            (self.tile_size // 2, self.tile_size // 4),
            (self.tile_size // 4, self.tile_size * 3 // 4),
            (self.tile_size * 3 // 4, self.tile_size * 3 // 4)
        ]
        pygame.draw.polygon(surf, (105, 105, 105), points) # Dim Gray
        self.sprites['aquatic_shark'] = surf
    
    def get_sprite(self, entity_type, species=None):
        """Get sprite for an entity"""
        if species:
            key = f"{entity_type}_{species}"
        else:
            key = entity_type
        
        return self.sprites.get(key, self.sprites.get(entity_type))
    
    def rescale_sprites(self, new_tile_size):
        """Regenerate sprites at new size"""
        self.tile_size = new_tile_size
        self._generate_sprites()


class TileRenderer:
    """Renders the game world tile by tile"""
    
    def __init__(self, game_state, viewport_width, viewport_height):
        self.game = game_state
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.tile_size = TILE_SIZE
        
        # Sprite manager
        self.sprites = SpriteManager(self.tile_size)
        
        # Rendering layers
        self.terrain_surface = None
        self.entities_surface = None
        
        # Selection
        self.hovered_tile = None
        self.selected_tile = None
        
        # Options
        self.show_grid = True
        self.show_vegetation = True
    
    def update_tile_size(self):
        """Update tile size based on zoom"""
        new_size = int(TILE_SIZE * self.zoom)
        if new_size != self.tile_size:
            self.tile_size = new_size
            self.sprites.rescale_sprites(new_size)
            self.terrain_surface = None  # Force redraw
    
    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        screen_x = (world_x - self.camera_x) * self.tile_size
        screen_y = (world_y - self.camera_y) * self.tile_size
        return int(screen_x), int(screen_y)
    
    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = screen_x // self.tile_size + self.camera_x
        world_y = screen_y // self.tile_size + self.camera_y
        return int(world_x), int(world_y)
    
    def get_visible_tiles(self):
        """Get range of tiles visible in viewport"""
        tiles_wide = (self.viewport_width // self.tile_size) + 2
        tiles_high = (self.viewport_height // self.tile_size) + 2
        
        start_x = max(0, int(self.camera_x))
        start_y = max(0, int(self.camera_y))
        end_x = min(self.game.world.width, start_x + tiles_wide)
        end_y = min(self.game.world.height, start_y + tiles_high)
        
        return start_x, start_y, end_x, end_y
    
    def render_terrain(self, surface):
        """Render terrain layer"""
        start_x, start_y, end_x, end_y = self.get_visible_tiles()
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                screen_x, screen_y = self.world_to_screen(x, y)
                
                # Get biome color
                biome = self.game.world.biomes[y, x]
                color = BIOME_COLORS.get(biome, BLACK)
                
                # Modulate by vegetation if enabled
                if self.show_vegetation and biome >= 3:  # Land biomes
                    veg = self.game.vegetation.density[y, x]
                    color = tuple(int(c * (0.6 + veg * 0.4)) for c in color)
                
                # Draw tile
                tile_rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                pygame.draw.rect(surface, color, tile_rect)
                
                # Draw grid
                if self.show_grid:
                    pygame.draw.rect(surface, GRID_COLOR, tile_rect, 1)
        
        # Draw hover highlight
        if self.hovered_tile:
            hx, hy = self.hovered_tile
            if start_x <= hx < end_x and start_y <= hy < end_y:
                screen_x, screen_y = self.world_to_screen(hx, hy)
                hover_rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                
                # Semi-transparent white overlay
                hover_surf = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                hover_surf.fill(HOVER_COLOR)
                surface.blit(hover_surf, (screen_x, screen_y))
                
                # Yellow border
                pygame.draw.rect(surface, SELECTION_COLOR, hover_rect, 2)
    
    def render_entities(self, surface):
        """Render all entities"""
        start_x, start_y, end_x, end_y = self.get_visible_tiles()
        
        # Render herbivores
        for animal in self.game.animals.herbivores:
            if start_x <= animal.x < end_x and start_y <= animal.y < end_y:
                sprite = self.sprites.get_sprite('herbivore', animal.species)
                if sprite:
                    screen_x, screen_y = self.world_to_screen(animal.x, animal.y)
                    surface.blit(sprite, (screen_x, screen_y))
                    
                    # HP bar
                    self._draw_hp_bar(surface, screen_x, screen_y, animal.combat_stats)
        
        # Render predators
        for pred in self.game.predators.predators:
            if start_x <= pred.x < end_x and start_y <= pred.y < end_y:
                sprite = self.sprites.get_sprite('predator', pred.species)
                if sprite:
                    screen_x, screen_y = self.world_to_screen(pred.x, pred.y)
                    surface.blit(sprite, (screen_x, screen_y))
                    
                    # HP bar
                    self._draw_hp_bar(surface, screen_x, screen_y, pred.combat_stats)
        
        # Render avian (if zoomed in enough)
        if self.zoom >= 1.0:
            for bird in self.game.ecology.avian_creatures:
                if start_x <= bird.x < end_x and start_y <= bird.y < end_y:
                    sprite = self.sprites.get_sprite('avian', bird.species)
                    if sprite:
                        screen_x, screen_y = self.world_to_screen(bird.x, bird.y)
                        surface.blit(sprite, (screen_x, screen_y))
        
        # Render aquatic (if over water)
        if self.zoom >= 1.0:
            for aq in self.game.ecology.aquatic_creatures:
                if start_x <= aq.x < end_x and start_y <= aq.y < end_y:
                    sprite = self.sprites.get_sprite('aquatic', aq.species)
                    if sprite:
                        screen_x, screen_y = self.world_to_screen(aq.x, aq.y)
                        surface.blit(sprite, (screen_x, screen_y))
    
    def _draw_hp_bar(self, surface, x, y, combat_stats):
        """Draw HP bar above entity"""
        bar_width = self.tile_size
        bar_height = max(3, self.tile_size // 10)
        bar_y = y - bar_height - 2
        
        # Background (red)
        pygame.draw.rect(surface, (200, 0, 0), (x, bar_y, bar_width, bar_height))
        
        # Foreground (green)
        hp_percent = combat_stats.hp_percentage()
        fill_width = int(bar_width * hp_percent)
        pygame.draw.rect(surface, (0, 200, 0), (x, bar_y, fill_width, bar_height))
        
        # Border
        pygame.draw.rect(surface, WHITE, (x, bar_y, bar_width, bar_height), 1)
    
    def render(self, surface):
        """Render complete frame"""
        self.render_terrain(surface)
        self.render_entities(surface)
    
    def handle_mouse_motion(self, screen_pos):
        """Update hovered tile based on mouse position"""
        if 0 <= screen_pos[0] < self.viewport_width and 0 <= screen_pos[1] < self.viewport_height:
            world_x, world_y = self.screen_to_world(screen_pos[0], screen_pos[1])
            
            if 0 <= world_x < self.game.world.width and 0 <= world_y < self.game.world.height:
                self.hovered_tile = (world_x, world_y)
            else:
                self.hovered_tile = None
        else:
            self.hovered_tile = None
    
    def zoom_at_point(self, screen_pos, zoom_delta):
        """Zoom toward a specific screen point"""
        # Get world position before zoom
        old_world_x, old_world_y = self.screen_to_world(screen_pos[0], screen_pos[1])
        
        # Apply zoom
        self.zoom = np.clip(self.zoom * zoom_delta, MIN_ZOOM, MAX_ZOOM)
        self.update_tile_size()
        
        # Adjust camera so world position stays under cursor
        new_world_x, new_world_y = self.screen_to_world(screen_pos[0], screen_pos[1])
        self.camera_x += old_world_x - new_world_x
        self.camera_y += old_world_y - new_world_y
    
    def pan_camera(self, dx, dy):
        """Move camera"""
        self.camera_x = np.clip(self.camera_x + dx, 0, self.game.world.width - 1)
        self.camera_y = np.clip(self.camera_y + dy, 0, self.game.world.height - 1)


class TooltipManager:
    """Manages tooltip display for hovered entities"""
    
    def __init__(self):
        self.font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 24)
    
    def render_tooltip(self, surface, game_state, world_pos, screen_pos):
        """Render tooltip for hovered tile"""
        if not world_pos:
            return
        
        x, y = world_pos
        
        # Gather info about this tile
        info_lines = []
        
        # Terrain info
        biome_names = {
            0: "Deep Ocean", 1: "Shallow Ocean", 2: "Beach", 3: "Desert",
            4: "Savanna", 5: "Grassland", 6: "Tropical Rainforest",
            7: "Temperate Forest", 8: "Taiga", 9: "Tundra", 10: "Snow", 11: "Mountain"
        }
        biome = game_state.world.biomes[y, x]
        info_lines.append(("Terrain:", biome_names.get(biome, "Unknown")))
        
        veg = game_state.vegetation.density[y, x]
        info_lines.append(("Vegetation:", f"{veg*100:.1f}%"))
        
        # Find entities at this location
        entities = []
        
        for animal in game_state.animals.herbivores:
            if animal.x == x and animal.y == y:
                entities.append(('Herbivore', animal.species, animal.combat_stats))
        
        for pred in game_state.predators.predators:
            if pred.x == x and pred.y == y:
                entities.append(('Predator', pred.species, pred.combat_stats))
        
        if entities:
            info_lines.append(("", ""))  # Spacer
            for entity_type, species, stats in entities[:3]:  # Show up to 3
                info_lines.append((f"{species.capitalize()}:", f"HP {stats.current_hp}/{stats.max_hp}"))
                info_lines.append(("", f"ATK {stats.attack} | DEF {stats.defense}"))
        
        # Calculate tooltip size
        padding = 10
        line_height = 20
        max_width = 250
        
        tooltip_height = padding * 2 + line_height * len(info_lines)
        tooltip_width = max_width
        
        # Position tooltip near mouse
        tooltip_x = screen_pos[0] + 15
        tooltip_y = screen_pos[1] + 15
        
        # Keep on screen
        if tooltip_x + tooltip_width > surface.get_width():
            tooltip_x = screen_pos[0] - tooltip_width - 15
        if tooltip_y + tooltip_height > surface.get_height():
            tooltip_y = screen_pos[1] - tooltip_height - 15
        
        # Draw background
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(surface, DARK_GRAY, tooltip_rect)
        pygame.draw.rect(surface, WHITE, tooltip_rect, 2)
        
        # Draw text
        text_y = tooltip_y + padding
        for label, value in info_lines:
            if label:
                text = f"{label} {value}"
            else:
                text = value
            
            text_surf = self.font.render(text, True, WHITE)
            surface.blit(text_surf, (tooltip_x + padding, text_y))
            text_y += line_height


# Test
if __name__ == "__main__":
    from game_controller import GameState, WorldConfig
    
    # Create test game
    config = WorldConfig()
    config.width = 80
    config.height = 60
    game = GameState(config)
    game.initialize_world()
    
    # Create renderer
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("Tile Renderer Test")
    
    renderer = TileRenderer(game, 1200, 800)
    tooltip = TooltipManager()
    clock = pygame.time.Clock()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEMOTION:
                renderer.handle_mouse_motion(event.pos)
            elif event.type == pygame.MOUSEWHEEL:
                renderer.zoom_at_point(pygame.mouse.get_pos(), 1.1 if event.y > 0 else 0.9)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    renderer.pan_camera(0, -1)
                elif event.key == pygame.K_DOWN:
                    renderer.pan_camera(0, 1)
                elif event.key == pygame.K_LEFT:
                    renderer.pan_camera(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    renderer.pan_camera(1, 0)
                elif event.key == pygame.K_g:
                    renderer.show_grid = not renderer.show_grid
                elif event.key == pygame.K_SPACE:
                    game.advance_turn()
        
        screen.fill(BLACK)
        renderer.render(screen)
        tooltip.render_tooltip(screen, game, renderer.hovered_tile, pygame.mouse.get_pos())
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()