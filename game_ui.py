import pygame
import numpy as np
from game_controller import GameState, WorldConfig, SaveSystem
import os
from datetime import datetime

# Initialize Pygame
pygame.init()

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 100, 200)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)

# Biome colors (matching our visualization)
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


class Button:
    """Simple button UI element"""
    def __init__(self, x, y, width, height, text, color=BLUE, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.hover = False
        self.font = pygame.font.Font(None, 24)
    
    def draw(self, screen):
        color = tuple(min(255, c + 30) for c in self.color) if self.hover else self.color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class Slider:
    """Slider UI element for numeric values"""
    def __init__(self, x, y, width, label, min_val, max_val, default_val, step=1):
        self.rect = pygame.Rect(x, y, width, 20)
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.value = default_val
        self.step = step
        self.dragging = False
        self.font = pygame.font.Font(None, 20)
    
    def draw(self, screen):
        # Label
        label_surf = self.font.render(f"{self.label}: {self.value}", True, WHITE)
        screen.blit(label_surf, (self.rect.x, self.rect.y - 20))
        
        # Track
        pygame.draw.rect(screen, GRAY, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 1)
        
        # Handle
        progress = (self.value - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.x + int(progress * self.rect.width)
        handle_rect = pygame.Rect(handle_x - 5, self.rect.y - 5, 10, 30)
        pygame.draw.rect(screen, GREEN, handle_rect)
        pygame.draw.rect(screen, WHITE, handle_rect, 2)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            handle_progress = (self.value - self.min_val) / (self.max_val - self.min_val)
            handle_x = self.rect.x + int(handle_progress * self.rect.width)
            handle_rect = pygame.Rect(handle_x - 5, self.rect.y - 5, 10, 30)
            if handle_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            rel_x = event.pos[0] - self.rect.x
            progress = np.clip(rel_x / self.rect.width, 0, 1)
            raw_value = self.min_val + progress * (self.max_val - self.min_val)
            self.value = round(raw_value / self.step) * self.step
            self.value = np.clip(self.value, self.min_val, self.max_val)


class WorldConfigScreen:
    """Screen for configuring world generation parameters"""
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Create sliders
        slider_x = self.width // 2 - 200
        slider_y_start = 150
        slider_spacing = 80
        
        self.sliders = {
            'width': Slider(slider_x, slider_y_start, 400, "World Width", 50, 200, 150, 10),
            'height': Slider(slider_x, slider_y_start + slider_spacing, 400, "World Height", 50, 150, 100, 10),
            'sea_level': Slider(slider_x, slider_y_start + slider_spacing * 2, 400, "Sea Level", 0.2, 0.6, 0.42, 0.02),
            'herbivores': Slider(slider_x, slider_y_start + slider_spacing * 3, 400, "Herbivores/Species", 20, 200, 100, 10),
            'predators': Slider(slider_x, slider_y_start + slider_spacing * 4, 400, "Predators/Species", 5, 50, 15, 5),
            'vegetation': Slider(slider_x, slider_y_start + slider_spacing * 5, 400, "Vegetation Density", 0.5, 2.0, 1.0, 0.1),
        }
        
        # Buttons
        button_y = slider_y_start + slider_spacing * 6 + 20
        button_width = 180
        button_spacing = 200
        start_x = self.width // 2 - (button_width * 2 + button_spacing) // 2
        
        self.generate_button = Button(start_x, button_y, button_width, 50, "Generate World", GREEN)
        self.random_button = Button(start_x + button_width + 20, button_y, button_width, 50, "Randomize", ORANGE)
        self.back_button = Button(start_x + (button_width + 20) * 2, button_y, button_width, 50, "Back", RED)
        
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 24)
    
    def handle_events(self, events):
        for event in events:
            for slider in self.sliders.values():
                slider.handle_event(event)
            
            if self.generate_button.handle_event(event):
                return self.create_config()
            
            if self.random_button.handle_event(event):
                self.randomize()
            
            if self.back_button.handle_event(event):
                return 'back'
        
        return None
    
    def randomize(self):
        """Randomize all parameters"""
        import random
        self.sliders['width'].value = random.choice([80, 100, 120, 150, 180])
        self.sliders['height'].value = random.choice([60, 80, 100, 120])
        self.sliders['sea_level'].value = round(random.uniform(0.3, 0.5), 2)
        self.sliders['herbivores'].value = random.randint(50, 150)
        self.sliders['predators'].value = random.randint(10, 30)
        self.sliders['vegetation'].value = round(random.uniform(0.7, 1.5), 1)
    
    def create_config(self):
        """Create WorldConfig from slider values"""
        config = WorldConfig()
        config.width = int(self.sliders['width'].value)
        config.height = int(self.sliders['height'].value)
        config.sea_level = self.sliders['sea_level'].value
        config.herbivore_population = int(self.sliders['herbivores'].value)
        config.predator_population = int(self.sliders['predators'].value)
        config.vegetation_density_multiplier = self.sliders['vegetation'].value
        config.seed = None  # Random seed
        return config
    
    def draw(self):
        self.screen.fill(DARK_GRAY)
        
        # Title
        title_surf = self.title_font.render("World Configuration", True, WHITE)
        title_rect = title_surf.get_rect(center=(self.width // 2, 80))
        self.screen.blit(title_surf, title_rect)
        
        # Sliders
        for slider in self.sliders.values():
            slider.draw(self.screen)
        
        # Buttons
        self.generate_button.draw(self.screen)
        self.random_button.draw(self.screen)
        self.back_button.draw(self.screen)


class GameView:
    """Main game view - displays the world and controls"""
    def __init__(self, screen, game_state):
        self.screen = screen
        self.game = game_state
        self.width, self.height = screen.get_size()
        
        # Map viewport
        self.map_rect = pygame.Rect(0, 0, self.width - 300, self.height)
        self.map_surface = None
        self.update_map_surface()
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        
        # UI panel
        self.panel_rect = pygame.Rect(self.width - 300, 0, 300, self.height)
        
        # Control buttons
        button_x = self.width - 280
        self.play_pause_button = Button(button_x, 50, 260, 40, "Play", GREEN)
        self.step_button = Button(button_x, 100, 260, 40, "Step Turn", BLUE)
        self.save_button = Button(button_x, 160, 260, 40, "Save Game", ORANGE)
        self.load_button = Button(button_x, 210, 260, 40, "Load Game", ORANGE)
        self.menu_button = Button(button_x, 270, 260, 40, "Main Menu", RED)
        
        # Game state
        self.playing = False
        self.last_update = pygame.time.get_ticks()
        self.update_interval = 500  # ms between turns when playing
        
        # Fonts
        self.font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 28)
        
        # Dragging
        self.dragging = False
        self.drag_start = (0, 0)
    
    def update_map_surface(self):
        """Render the world to a surface"""
        if not self.game.world:
            return
        
        world_width = self.game.world.width
        world_height = self.game.world.height
        
        # Create surface for the map
        self.map_surface = pygame.Surface((world_width, world_height))
        
        # Draw biomes
        for y in range(world_height):
            for x in range(world_width):
                biome = self.game.world.biomes[y, x]
                color = BIOME_COLORS.get(biome, BLACK)
                
                # Modulate by vegetation
                veg = self.game.vegetation.density[y, x]
                if biome >= 3:  # Land biomes get darker with more vegetation
                    color = tuple(int(c * (0.7 + veg * 0.3)) for c in color)
                
                self.map_surface.set_at((x, y), color)
        
        # Draw animals (simplified - just dots)
        # Herbivores
        for animal in self.game.animals.herbivores:
            color = (210, 180, 140)  # Tan
            if 0 <= animal.x < world_width and 0 <= animal.y < world_height:
                self.map_surface.set_at((animal.x, animal.y), color)
        
        # Predators
        for pred in self.game.predators.predators:
            color = (255, 0, 0)  # Red
            if 0 <= pred.x < world_width and 0 <= pred.y < world_height:
                self.map_surface.set_at((pred.x, pred.y), color)
        
        # Avian (bright yellow dots)
        for bird in self.game.ecology.avian_creatures:
            color = (255, 255, 0)
            if 0 <= bird.x < world_width and 0 <= bird.y < world_height:
                self.map_surface.set_at((bird.x, bird.y), color)
    
    def handle_events(self, events):
        for event in events:
            # Buttons
            if self.play_pause_button.handle_event(event):
                self.playing = not self.playing
                self.play_pause_button.text = "Pause" if self.playing else "Play"
                self.play_pause_button.color = RED if self.playing else GREEN
            
            if self.step_button.handle_event(event):
                self.game.advance_turn()
                self.update_map_surface()
            
            if self.save_button.handle_event(event):
                self.save_game()
            
            if self.load_button.handle_event(event):
                return self.load_game()
            
            if self.menu_button.handle_event(event):
                return 'menu'
            
            # Map dragging
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.map_rect.collidepoint(event.pos):
                    self.dragging = True
                    self.drag_start = event.pos
            
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.dragging = False
            
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                dx = event.pos[0] - self.drag_start[0]
                dy = event.pos[1] - self.drag_start[1]
                self.camera_x -= dx / self.zoom
                self.camera_y -= dy / self.zoom
                self.drag_start = event.pos
            
            # Zoom with mouse wheel
            elif event.type == pygame.MOUSEWHEEL:
                if self.map_rect.collidepoint(pygame.mouse.get_pos()):
                    zoom_factor = 1.1 if event.y > 0 else 0.9
                    self.zoom = np.clip(self.zoom * zoom_factor, 0.5, 10.0)
        
        return None
    
    def update(self):
        """Update game state when playing"""
        if self.playing:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_update > self.update_interval:
                self.game.advance_turn()
                self.update_map_surface()
                self.last_update = current_time
    
    def save_game(self):
        """Save current game state"""
        if not os.path.exists('saves'):
            os.makedirs('saves')
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"saves/save_{timestamp}.json"
        
        try:
            SaveSystem.save_game(self.game, filename)
            print(f"Game saved to {filename}")
        except Exception as e:
            print(f"Failed to save: {e}")
    
    def load_game(self):
        """Load a game state"""
        if not os.path.exists('saves'):
            print("No saves folder found")
            return None
        
        saves = [f for f in os.listdir('saves') if f.endswith('.json')]
        if not saves:
            print("No save files found")
            return None
        
        # Load most recent
        saves.sort(reverse=True)
        filepath = os.path.join('saves', saves[0])
        
        try:
            loaded_game = SaveSystem.load_game(filepath)
            return loaded_game
        except Exception as e:
            print(f"Failed to load: {e}")
            return None
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw map
        if self.map_surface:
            # Calculate scaled size
            scaled_width = int(self.game.world.width * self.zoom)
            scaled_height = int(self.game.world.height * self.zoom)
            
            # Scale the map surface
            scaled_surface = pygame.transform.scale(
                self.map_surface, 
                (scaled_width, scaled_height)
            )
            
            # Apply camera offset
            offset_x = int(-self.camera_x * self.zoom)
            offset_y = int(-self.camera_y * self.zoom)
            
            self.screen.blit(scaled_surface, (offset_x, offset_y))
        
        # Draw UI panel
        pygame.draw.rect(self.screen, DARK_GRAY, self.panel_rect)
        pygame.draw.line(self.screen, WHITE, 
                        (self.panel_rect.x, 0), 
                        (self.panel_rect.x, self.height), 2)
        
        # Title
        title_surf = self.title_font.render("World Simulation", True, WHITE)
        self.screen.blit(title_surf, (self.panel_rect.x + 10, 10))
        
        # Buttons
        self.play_pause_button.draw(self.screen)
        self.step_button.draw(self.screen)
        self.save_button.draw(self.screen)
        self.load_button.draw(self.screen)
        self.menu_button.draw(self.screen)
        
        # Statistics
        stats = self.game.get_current_statistics()
        stats_y = 330
        stats_x = self.panel_rect.x + 10
        
        stats_lines = [
            f"Turn: {stats['turn']}",
            f"Year: {stats['year']} ({stats['season']})",
            f"",
            f"Vegetation: {stats['vegetation_coverage']:.1f}%",
            f"",
            "=== Populations ===",
        ]
        
        # Herbivores
        if stats['populations'].get('herbivores'):
            stats_lines.append("Herbivores:")
            for species, count in stats['populations']['herbivores'].items():
                stats_lines.append(f"  {species}: {count}")
        
        # Predators
        if stats['populations'].get('predators'):
            stats_lines.append("Predators:")
            for species, count in stats['populations']['predators'].items():
                stats_lines.append(f"  {species}: {count}")
        
        # Other
        stats_lines.extend([
            f"",
            f"Scavengers: {stats['populations'].get('scavengers', 0)}",
            f"Avian: {stats['populations'].get('avian', 0)}",
            f"Aquatic: {stats['populations'].get('aquatic', 0)}",
        ])
        
        # Events
        if stats.get('events'):
            stats_lines.extend([
                f"",
                f"Diseases: {stats['events']['active_diseases']}",
                f"Disasters: {stats['events']['active_disasters']}",
            ])
        
        for i, line in enumerate(stats_lines):
            text_surf = self.font.render(line, True, WHITE)
            self.screen.blit(text_surf, (stats_x, stats_y + i * 20))
        
        # Instructions at bottom
        inst_y = self.height - 60
        instructions = [
            "Click & drag to pan",
            "Mouse wheel to zoom",
        ]
        for i, inst in enumerate(instructions):
            text_surf = self.font.render(inst, True, LIGHT_GRAY)
            self.screen.blit(text_surf, (stats_x, inst_y + i * 20))


class MainMenu:
    """Main menu screen"""
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Buttons
        button_width = 300
        button_height = 60
        button_x = self.width // 2 - button_width // 2
        start_y = 250
        spacing = 80
        
        self.new_game_button = Button(button_x, start_y, button_width, button_height, 
                                      "New World", GREEN)
        self.load_button = Button(button_x, start_y + spacing, button_width, button_height,
                                  "Load Game", BLUE)
        self.quit_button = Button(button_x, start_y + spacing * 2, button_width, button_height,
                                  "Quit", RED)
        
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 32)
    
    def handle_events(self, events):
        for event in events:
            if self.new_game_button.handle_event(event):
                return 'new_game'
            if self.load_button.handle_event(event):
                return 'load_game'
            if self.quit_button.handle_event(event):
                return 'quit'
        return None
    
    def draw(self):
        self.screen.fill(DARK_GRAY)
        
        # Title
        title_surf = self.title_font.render("World Simulator", True, WHITE)
        title_rect = title_surf.get_rect(center=(self.width // 2, 120))
        self.screen.blit(title_surf, title_rect)
        
        # Subtitle
        subtitle_surf = self.subtitle_font.render("Ecological Strategy Game", True, LIGHT_GRAY)
        subtitle_rect = subtitle_surf.get_rect(center=(self.width // 2, 180))
        self.screen.blit(subtitle_surf, subtitle_rect)
        
        # Buttons
        self.new_game_button.draw(self.screen)
        self.load_button.draw(self.screen)
        self.quit_button.draw(self.screen)
        
        # Version
        font = pygame.font.Font(None, 20)
        version_surf = font.render("v0.3.0 - Pre-Civilization", True, GRAY)
        self.screen.blit(version_surf, (10, self.height - 25))


class GameUI:
    """Main application controller"""
    def __init__(self, width=1400, height=900):
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("World Simulator")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Screens
        self.current_screen = 'menu'
        self.menu = MainMenu(self.screen)
        self.config_screen = WorldConfigScreen(self.screen)
        self.game_view = None
        self.game_state = None
    
    def run(self):
        """Main game loop"""
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.current_screen == 'game':
                            self.current_screen = 'menu'
            
            # Handle current screen
            if self.current_screen == 'menu':
                action = self.menu.handle_events(events)
                if action == 'new_game':
                    self.current_screen = 'config'
                elif action == 'load_game':
                    self.load_game()
                elif action == 'quit':
                    self.running = False
                
                self.menu.draw()
            
            elif self.current_screen == 'config':
                result = self.config_screen.handle_events(events)
                if result == 'back':
                    self.current_screen = 'menu'
                elif isinstance(result, WorldConfig):
                    self.start_new_game(result)
                
                self.config_screen.draw()
            
            elif self.current_screen == 'game':
                result = self.game_view.handle_events(events)
                if result == 'menu':
                    self.current_screen = 'menu'
                elif isinstance(result, GameState):
                    # Loaded a new game
                    self.game_state = result
                    self.game_view = GameView(self.screen, self.game_state)
                
                self.game_view.update()
                self.game_view.draw()
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()
    
    def start_new_game(self, config):
        """Initialize a new game with given config"""
        print("\n=== STARTING NEW GAME ===")
        self.game_state = GameState(config)
        self.game_state.initialize_world()
        self.game_view = GameView(self.screen, self.game_state)
        self.current_screen = 'game'
    
    def load_game(self):
        """Load most recent save"""
        if not os.path.exists('saves'):
            print("No saves folder found")
            return
        
        saves = [f for f in os.listdir('saves') if f.endswith('.json')]
        if not saves:
            print("No save files found")
            return
        
        saves.sort(reverse=True)
        filepath = os.path.join('saves', saves[0])
        
        try:
            self.game_state = SaveSystem.load_game(filepath)
            self.game_view = GameView(self.screen, self.game_state)
            self.current_screen = 'game'
        except Exception as e:
            print(f"Failed to load: {e}")


if __name__ == "__main__":
    game = GameUI()
    game.run()
