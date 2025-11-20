import pygame
import numpy as np
from game_controller import GameState, WorldConfig, SaveSystem
from game_renderer import TileRenderer, TooltipManager
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


class StatisticsOverlay:
    """Overlay for displaying population graphs"""
    def __init__(self, x, y, width, height, game_state):
        self.rect = pygame.Rect(x, y, width, height)
        self.game = game_state
        self.font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 32)
        self.mode = 'herbivores'  # 'herbivores' or 'predators'
        
        # Buttons
        btn_w = 120
        self.herb_btn = Button(x + 20, y + 20, btn_w, 30, "Herbivores", GREEN)
        self.pred_btn = Button(x + 150, y + 20, btn_w, 30, "Predators", RED)
        self.food_btn = Button(x + 280, y + 20, btn_w, 30, "Food Chain", ORANGE)
        self.death_btn = Button(x + 410, y + 20, btn_w, 30, "Deaths", GRAY)
        self.close_btn = Button(x + width - 40, y + 10, 30, 30, "X", RED)
        
    def handle_event(self, event):
        if self.herb_btn.handle_event(event):
            self.mode = 'herbivores'
            return True
        if self.pred_btn.handle_event(event):
            self.mode = 'predators'
            return True
        if self.food_btn.handle_event(event):
            self.mode = 'food_chain'
            return True
        if self.death_btn.handle_event(event):
            self.mode = 'deaths'
            return True
        if self.close_btn.handle_event(event):
            return 'close'
        return False
        
    def draw(self, screen):
        # Background
        s = pygame.Surface((self.rect.width, self.rect.height))
        s.set_alpha(230)
        s.fill(DARK_GRAY)
        screen.blit(s, (self.rect.x, self.rect.y))
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        # Buttons
        self.herb_btn.draw(screen)
        self.pred_btn.draw(screen)
        self.food_btn.draw(screen)
        self.death_btn.draw(screen)
        self.close_btn.draw(screen)
        
        if self.mode in ['herbivores', 'predators']:
            self._draw_graphs(screen)
        elif self.mode == 'food_chain':
            self._draw_food_chain(screen)
        elif self.mode == 'deaths':
            self._draw_deaths(screen)

    def _draw_food_chain(self, screen):
        """Draw food chain matrix"""
        stats = self.game.get_current_statistics()
        food_chain = stats.get('food_chain', {})
        
        if not food_chain:
            text = self.font.render("No predation data yet", True, WHITE)
            screen.blit(text, (self.rect.centerx - 50, self.rect.centery))
            return
            
        # Title
        title = self.title_font.render("Predation Statistics (Who ate Whom)", True, WHITE)
        screen.blit(title, (self.rect.x + 50, self.rect.y + 70))
        
        # List predators and their prey
        y_offset = 120
        x_offset = self.rect.x + 50
        
        # Sort predators by total kills
        sorted_preds = sorted(food_chain.items(), key=lambda x: sum(x[1].values()), reverse=True)
        
        for predator, prey_dict in sorted_preds:
            total_kills = sum(prey_dict.values())
            pred_text = self.font.render(f"{predator.capitalize()} (Total Kills: {total_kills})", True, ORANGE)
            screen.blit(pred_text, (x_offset, self.rect.y + y_offset))
            
            # List top prey
            prey_x = x_offset + 200
            sorted_prey = sorted(prey_dict.items(), key=lambda x: x[1], reverse=True)
            
            prey_str = ", ".join([f"{p.capitalize()}: {c}" for p, c in sorted_prey[:5]])
            if len(sorted_prey) > 5:
                prey_str += "..."
                
            prey_surf = self.font.render(prey_str, True, LIGHT_GRAY)
            screen.blit(prey_surf, (prey_x, self.rect.y + y_offset))
            
            y_offset += 30
            if y_offset > self.rect.height - 50:
                break

    def _draw_deaths(self, screen):
        """Draw causes of death"""
        stats = self.game.get_current_statistics()
        death_causes = stats.get('death_causes', {})
        
        if not death_causes:
            text = self.font.render("No death data yet", True, WHITE)
            screen.blit(text, (self.rect.centerx - 50, self.rect.centery))
            return
            
        # Title
        title = self.title_font.render("Causes of Death", True, WHITE)
        screen.blit(title, (self.rect.x + 50, self.rect.y + 70))
        
        y_offset = 120
        x_offset = self.rect.x + 50
        
        # Sort by total deaths
        sorted_species = sorted(death_causes.items(), key=lambda x: sum(x[1].values()), reverse=True)
        
        for species, causes in sorted_species:
            total = sum(causes.values())
            species_text = self.font.render(f"{species.capitalize()} (Total Deaths: {total})", True, GREEN)
            screen.blit(species_text, (x_offset, self.rect.y + y_offset))
            
            # Breakdown
            breakdown_x = x_offset + 200
            parts = []
            for cause, count in causes.items():
                pct = int(count / total * 100)
                parts.append(f"{cause}: {count} ({pct}%)")
            
            breakdown_str = " | ".join(parts)
            breakdown_surf = self.font.render(breakdown_str, True, LIGHT_GRAY)
            screen.blit(breakdown_surf, (breakdown_x, self.rect.y + y_offset))
            
            y_offset += 30
            if y_offset > self.rect.height - 50:
                break

    def _draw_graphs(self, screen):
        # Get data
        history = self.game.get_population_history()
        data = history.get(self.mode, {})
        
        if not data:
            text = self.font.render("No data available", True, WHITE)
            screen.blit(text, (self.rect.centerx - 50, self.rect.centery))
            return

        # Graph area
        graph_rect = pygame.Rect(self.rect.x + 50, self.rect.y + 80, 
                               self.rect.width - 70, self.rect.height - 100)
        pygame.draw.rect(screen, BLACK, graph_rect)
        pygame.draw.rect(screen, WHITE, graph_rect, 1)
        
        # Find max value for scaling
        max_val = 10
        max_len = 0
        for species_data in data.values():
            if species_data:
                max_val = max(max_val, max(species_data))
                max_len = max(max_len, len(species_data))
        
        if max_len < 2:
            return

        # Draw grid lines
        for i in range(5):
            y = graph_rect.bottom - (i * graph_rect.height / 4)
            pygame.draw.line(screen, DARK_GRAY, (graph_rect.left, y), (graph_rect.right, y))
            val = int(i * max_val / 4)
            text = self.font.render(str(val), True, LIGHT_GRAY)
            screen.blit(text, (graph_rect.left - 35, y - 10))
            
        # Draw lines
        colors = {
            'deer': (139, 69, 19), 'bison': (100, 50, 0), 'caribou': (200, 200, 200),
            'gazelle': (255, 165, 0), 'elephant': (128, 0, 128), 'rabbit': (255, 255, 255),
            'wolf': (100, 100, 100), 'lion': (255, 215, 0), 'bear': (80, 40, 0),
            'leopard': (200, 150, 50), 'polar_bear': (240, 240, 255), 'crocodile': (0, 100, 0)
        }
        
        x_step = graph_rect.width / (max_len - 1) if max_len > 1 else 0
        
        for species, points in data.items():
            if not points: continue
            
            color = colors.get(species, (np.random.randint(100, 255), np.random.randint(100, 255), np.random.randint(100, 255)))
            
            # Draw line
            prev_pos = None
            for i, val in enumerate(points):
                x = graph_rect.left + i * x_step
                y = graph_rect.bottom - (val / max_val * graph_rect.height)
                pos = (x, y)
                
                if prev_pos:
                    pygame.draw.line(screen, color, prev_pos, pos, 2)
                prev_pos = pos
            
            # Legend (simple)
            # (In a real app, we'd layout a proper legend)


class GameView:
    """Main game view - displays the world and controls"""
    def __init__(self, screen, game_state):
        self.screen = screen
        self.game = game_state
        self.width, self.height = screen.get_size()
        
        # Viewport dimensions (sidebar is 300px)
        viewport_width = self.width - 300
        viewport_height = self.height
        
        # Initialize Renderer
        self.renderer = TileRenderer(self.game, viewport_width, viewport_height)
        self.tooltip = TooltipManager()
        
        # UI panel
        self.panel_rect = pygame.Rect(self.width - 300, 0, 300, self.height)
        
        # Control buttons
        button_x = self.width - 280
        self.play_pause_button = Button(button_x, 50, 260, 40, "Play", GREEN)
        self.step_button = Button(button_x, 100, 260, 40, "Step Turn", BLUE)
        self.stats_button = Button(button_x, 160, 260, 40, "Statistics", YELLOW)
        self.save_button = Button(button_x, 220, 260, 40, "Save Game", ORANGE)
        self.load_button = Button(button_x, 270, 260, 40, "Load Game", ORANGE)
        self.menu_button = Button(button_x, 330, 260, 40, "Main Menu", RED)
        
        # Stats Overlay
        self.show_stats = False
        self.stats_overlay = StatisticsOverlay(50, 50, viewport_width - 100, viewport_height - 100, self.game)
        
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
    
    def handle_events(self, events):
        for event in events:
            # Pass events to renderer
            if event.type == pygame.MOUSEMOTION:
                self.renderer.handle_mouse_motion(event.pos)
                if self.dragging:
                    dx = event.pos[0] - self.drag_start[0]
                    dy = event.pos[1] - self.drag_start[1]
                    # Convert pixel drag to tile drag (approximate)
                    tile_dx = -dx / self.renderer.tile_size
                    tile_dy = -dy / self.renderer.tile_size
                    self.renderer.pan_camera(tile_dx, tile_dy)
                    self.drag_start = event.pos

            elif event.type == pygame.MOUSEWHEEL:
                # Check if mouse is in viewport
                mx, my = pygame.mouse.get_pos()
                if mx < self.renderer.viewport_width:
                    self.renderer.zoom_at_point((mx, my), 1.1 if event.y > 0 else 0.9)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and event.pos[0] < self.renderer.viewport_width:
                    self.dragging = True
                    self.drag_start = event.pos
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False

            # Buttons
            if self.show_stats:
                res = self.stats_overlay.handle_event(event)
                if res == 'close':
                    self.show_stats = False
                # Don't process other clicks if stats are open
                if event.type == pygame.MOUSEBUTTONDOWN:
                    return None
            
            if self.play_pause_button.handle_event(event):
                self.playing = not self.playing
                self.play_pause_button.text = "Pause" if self.playing else "Play"
                self.play_pause_button.color = RED if self.playing else GREEN
            
            if self.step_button.handle_event(event):
                self.game.advance_turn()
                
            if self.stats_button.handle_event(event):
                self.show_stats = not self.show_stats
            
            if self.save_button.handle_event(event):
                self.save_game()
            
            if self.load_button.handle_event(event):
                return self.load_game()
            
            if self.menu_button.handle_event(event):
                return 'menu'
        
        return None
    
    def update(self):
        """Update game state when playing"""
        if self.playing:
            current_time = pygame.time.get_ticks()
            if current_time - self.last_update > self.update_interval:
                self.game.advance_turn()
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
        
        # Draw map via renderer
        self.renderer.render(self.screen)
        
        # Draw tooltip
        self.tooltip.render_tooltip(self.screen, self.game, self.renderer.hovered_tile, pygame.mouse.get_pos())
        
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
        self.stats_button.draw(self.screen)
        self.save_button.draw(self.screen)
        self.load_button.draw(self.screen)
        self.menu_button.draw(self.screen)
        
        # Statistics
        stats = self.game.get_current_statistics()
        stats_y = 390
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
            f"Insects: {stats['populations'].get('insects', 0)}",
        ])
        
        # Events
        if stats.get('events'):
            stats_lines.extend([
                f"",
                f"Diseases: {stats['events']['active_diseases']}",
                f"Disasters: {stats['events']['active_disasters']}",
            ])
            
        # Event Log (Last 5)
        if 'event_log' in self.game.statistics and self.game.statistics['event_log']:
            stats_lines.append("")
            stats_lines.append("=== Recent Events ===")
            for event in self.game.statistics['event_log'][-5:]:
                stats_lines.append(f"{event['time']}: {event['msg']}")
        
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
            
        # Draw overlay if active
        if self.show_stats:
            self.stats_overlay.draw(self.screen)


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
