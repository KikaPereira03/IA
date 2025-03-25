import pygame
import sys
import time
import math
import random
import os

# Import from game modules
from game.core import CakeGame, CakeLayer
from game.solver import GameSolver
from game.utils import load_image, draw_text, create_gradient
from game.themes import THEMES, get_theme
from game.progress import GameProgress
from game.effects import ParticleSystem, draw_cake_decoration
from game.level_info import LevelManager

class GameState:
    """Game state constants"""
    MAIN_MENU = "main_menu"
    LEVEL_SELECT = "level_select"
    PLAYING = "playing"
    LEVEL_COMPLETE = "level_complete"
    SETTINGS = "settings"
    SHOP = "shop"

class CakeGameUI:
    def __init__(self):
        pygame.init()
        
        # Load game progress and level data
        self.progress = GameProgress()
        self.level_manager = LevelManager()
        
        # Initialize with default dimensions, will be updated when loading level
        self.game = CakeGame(4, 3)
        self.solver = GameSolver(self.game)
        
        # UI Settings
        self.screen_width = 1000
        self.screen_height = 800
        self.tube_width = 80
        self.tube_height = 300
        self.layer_height = 40
        self.margin = 50
        
        # Colors
        self.bg_color = (240, 240, 250)
        self.tube_color = (200, 200, 210)
        self.selected_color = (255, 255, 0, 150)  # Semi-transparent yellow
        self.text_color = (50, 50, 50)
        
        # Get color map from theme
        self.current_theme = get_theme(self.progress.theme)
        
        # Initialize display
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cake Sort Puzzle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 36)
        self.small_font = pygame.font.SysFont('Arial', 18)
        
        # Game state
        self.game_state = GameState.MAIN_MENU
        self.selected_tube = None
        self.selected_layer_pos = None
        self.solving = False
        self.solution_moves = []
        self.last_move_time = 0
        self.current_level = self.progress.current_level
        self.level_info = None
        
        # Visual effects
        self.particles = ParticleSystem()
        
        # Background elements
        self.bg_gradient = create_gradient(
            self.screen_width, self.screen_height,
            (220, 220, 240), (240, 240, 255)
        )
        
        # Load a level to start
        self.load_level(self.current_level)
    
    def load_level(self, level_num: int):
        """Load a specific level by number"""
        level_info = self.level_manager.get_level_info(level_num)
        
        if level_info:
            self.level_info = level_info
            
            # Update game dimensions if needed
            if level_info.width != self.game.width or level_info.height != self.game.height:
                self.game = CakeGame(level_info.width, level_info.height)
                self.solver = GameSolver(self.game)
            
            # Load the level file
            level_path = self.level_manager.get_level_path(level_num)
            self.game.initialize_level(level_path)
            
            # Reset game state
            self.selected_tube = None
            self.selected_layer_pos = None
            self.solving = False
            self.solution_moves = []
            self.game_state = GameState.PLAYING
            self.current_level = level_num
            self.progress.current_level = level_num
            self.progress.save()
            
            # Add level start particles
            for tube_idx in range(len(self.game.tubes)):
                tube_rect = self.get_tube_rect(tube_idx)
                self.particles.add_particle('sparkle', tube_rect.centerx, tube_rect.y)
        else:
            print(f"Level {level_num} not found")
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if self.game_state == GameState.MAIN_MENU:
                self.handle_main_menu_events(event)
            elif self.game_state == GameState.PLAYING:
                self.handle_playing_events(event)
            elif self.game_state == GameState.LEVEL_COMPLETE:
                self.handle_level_complete_events(event)
            elif self.game_state == GameState.LEVEL_SELECT:
                self.handle_level_select_events(event)
            elif self.game_state == GameState.SETTINGS:
                self.handle_settings_events(event)
            elif self.game_state == GameState.SHOP:
                self.handle_shop_events(event)
        
        # Auto-play solution if solving
        if self.game_state == GameState.PLAYING and self.solving and self.solution_moves and time.time() - self.last_move_time > 0.5:
            from_idx, layer_pos, to_idx = self.solution_moves.pop(0)
            self.game.move_layer(from_idx, layer_pos, to_idx)
            self.last_move_time = time.time()
            
            # Add particle effect for the move
            to_tube_rect = self.get_tube_rect(to_idx)
            self.particles.add_particle('move', to_tube_rect.centerx, to_tube_rect.y)
            
            if not self.solution_moves:
                self.solving = False
                if self.game.is_solved():
                    self.show_win_message()
        
        # Check for level completion
        if self.game_state == GameState.PLAYING and self.game.is_solved():
            self.show_win_message()
        
        return True
    
    def handle_main_menu_events(self, event):
        """Handle events for the main menu"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Play button
            play_rect = pygame.Rect(self.screen_width//2 - 100, 300, 200, 50)
            if play_rect.collidepoint(mouse_pos):
                self.game_state = GameState.LEVEL_SELECT
            
            # Settings button
            settings_rect = pygame.Rect(self.screen_width//2 - 100, 380, 200, 50)
            if settings_rect.collidepoint(mouse_pos):
                self.game_state = GameState.SETTINGS
            
            # Shop button
            shop_rect = pygame.Rect(self.screen_width//2 - 100, 460, 200, 50)
            if shop_rect.collidepoint(mouse_pos):
                self.game_state = GameState.SHOP
    
    def handle_playing_events(self, event):
        """Handle events while playing a level"""
        if event.type == pygame.MOUSEBUTTONDOWN and not self.solving:
            if event.button == 1:  # Left click
                self.handle_click(pygame.mouse.get_pos())
            elif event.button == 3:  # Right click - cancel selection
                self.selected_tube = None
                self.selected_layer_pos = None
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:  # Reset level
                self.load_level(self.current_level)
            elif event.key == pygame.K_s:  # Solve with A*
                self.start_solving('advanced')
            elif event.key == pygame.K_b:  # Solve with BFS
                self.start_solving('bfs')
            elif event.key == pygame.K_n:  # Next level
                if self.current_level < max(self.level_manager.levels.keys()):
                    self.load_level(self.current_level + 1)
            elif event.key == pygame.K_p:  # Previous level
                if self.current_level > 1:
                    self.load_level(self.current_level - 1)
            elif event.key == pygame.K_h:  # Hint
                self.get_hint()
            elif event.key == pygame.K_m:  # Back to menu
                self.game_state = GameState.MAIN_MENU
            elif event.key == pygame.K_t:  # Toggle theme
                themes = list(THEMES.keys())
                current_idx = themes.index(self.progress.theme)
                next_idx = (current_idx + 1) % len(themes)
                self.progress.theme = themes[next_idx]
                self.current_theme = get_theme(self.progress.theme)
                self.progress.save()
    
    def handle_level_complete_events(self, event):
        """Handle events on level complete screen"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Next Level button
            next_level_rect = pygame.Rect(self.screen_width//2 - 100, self.screen_height//2 + 50, 200, 50)
            if next_level_rect.collidepoint(mouse_pos):
                if self.current_level < max(self.level_manager.levels.keys()):
                    self.load_level(self.current_level + 1)
                else:
                    # All levels completed, go back to level select
                    self.game_state = GameState.LEVEL_SELECT
            
            # Back to Menu button
            menu_rect = pygame.Rect(self.screen_width//2 - 100, self.screen_height//2 + 120, 200, 50)
            if menu_rect.collidepoint(mouse_pos):
                self.game_state = GameState.MAIN_MENU
    
    def handle_level_select_events(self, event):
        """Handle events on level select screen"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Back button
            back_rect = pygame.Rect(20, 20, 100, 40)
            if back_rect.collidepoint(mouse_pos):
                self.game_state = GameState.MAIN_MENU
                return
            
            # Level buttons
            for level_num, level_info in self.level_manager.levels.items():
                # Only allow selecting levels up to max_level
                if level_num <= self.progress.max_level:
                    row = (level_num - 1) // 5
                    col = (level_num - 1) % 5
                    
                    x = self.margin + col * 180
                    y = 150 + row * 180
                    
                    level_rect = pygame.Rect(x, y, 150, 150)
                    if level_rect.collidepoint(mouse_pos):
                        self.load_level(level_num)
                        return
    
    def handle_settings_events(self, event):
        """Handle events on settings screen"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Back button
            back_rect = pygame.Rect(20, 20, 100, 40)
            if back_rect.collidepoint(mouse_pos):
                self.game_state = GameState.MAIN_MENU
                return
            
            # Theme selection
            theme_y = 180
            for i, theme_name in enumerate(THEMES.keys()):
                if theme_name in self.progress.unlocked_themes:
                    theme_rect = pygame.Rect(self.screen_width // 2 - 150, theme_y + i * 60, 300, 50)
                    if theme_rect.collidepoint(mouse_pos):
                        self.progress.theme = theme_name
                        self.current_theme = get_theme(theme_name)
                        self.progress.save()
    
    def handle_shop_events(self, event):
        """Handle events on shop screen"""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Back button
            back_rect = pygame.Rect(20, 20, 100, 40)
            if back_rect.collidepoint(mouse_pos):
                self.game_state = GameState.MAIN_MENU
                return
            
            # Theme purchase buttons
            theme_costs = {
                "pastel": 100,
                "chocolate": 200,
                "frosting": 300
            }
            
            theme_y = 180
            for i, (theme_name, cost) in enumerate(theme_costs.items()):
                if theme_name not in self.progress.unlocked_themes:
                    button_rect = pygame.Rect(self.screen_width // 2 + 100, theme_y + i * 60, 150, 50)
                    if button_rect.collidepoint(mouse_pos):
                        success, message = self.progress.unlock_theme(theme_name)
                        if success:
                            # Add celebration particles
                            for _ in range(10):
                                self.particles.add_particle(
                                    'confetti', 
                                    self.screen_width // 2,
                                    theme_y + i * 60 + 25
                                )
    
    def get_hint(self):
        """Show the next best move"""
        if not self.solution_moves:
            self.start_solving('advanced')
        
        if self.solution_moves:
            from_idx, layer_pos, to_idx = self.solution_moves[0]
            print(f"Hint: Move from tube {from_idx} (layer {layer_pos}) to tube {to_idx}")
            
            # Highlight the source and target tubes
            self.selected_tube = from_idx
            self.selected_layer_pos = layer_pos
            
            # Add hint particles
            from_tube_rect = self.get_tube_rect(from_idx)
            to_tube_rect = self.get_tube_rect(to_idx)
            
            for _ in range(5):
                self.particles.add_particle(
                    'sparkle',
                    from_tube_rect.centerx, 
                    from_tube_rect.y + from_tube_rect.height - (layer_pos + 1) * self.layer_height
                )
                self.particles.add_particle(
                    'sparkle',
                    to_tube_rect.centerx,
                    to_tube_rect.y + 20
                )
    
    def start_solving(self, method: str):
        """Start auto-solving the puzzle"""
        start_time = time.time()
        
        if method == 'bfs':
            self.solution_moves = self.solver.solve_bfs()
        else:
            self.solution_moves = self.solver.solve_a_star(method)
        
        end_time = time.time()
        
        if self.solution_moves:
            print(f"Solution found in {len(self.solution_moves)} moves! Time: {end_time-start_time:.2f}s")
            self.solving = True
            self.last_move_time = time.time()
        else:
            print("No solution found!")
            self.solving = False
    
    def handle_click(self, mouse_pos):
        for tube_idx, tube in enumerate(self.game.tubes):
            tube_rect = self.get_tube_rect(tube_idx)
            if tube_rect.collidepoint(mouse_pos):
                if self.selected_tube is None:
                    # Check if tube has layers to select
                    if not tube.is_empty():
                        # Select a tube and layer
                        self.selected_tube = tube_idx
                        # Find which layer was clicked
                        rel_y = mouse_pos[1] - tube_rect.y
                        layer_index = min(
                            len(tube.layers) - 1 - (rel_y // self.layer_height),
                            len(tube.layers) - 1
                        )
                        if layer_index >= 0:
                            self.selected_layer_pos = layer_index
                            # Add selection particle
                            self.particles.add_particle(
                                'selection',
                                tube_rect.centerx,
                                tube_rect.y + tube_rect.height - (layer_index+1)*self.layer_height
                            )
                else:
                    # Try to move the selected layer
                    if tube_idx != self.selected_tube:  # Can't move to the same tube
                        # Make sure both values are valid before trying to move
                        if self.selected_tube is not None and self.selected_layer_pos is not None:
                            if self.game.move_layer(self.selected_tube, self.selected_layer_pos, tube_idx):
                                # Add move particles
                                to_tube_rect = self.get_tube_rect(tube_idx)
                                self.particles.add_particle('move', to_tube_rect.centerx, to_tube_rect.y)
                                
                                if self.game.is_solved():
                                    self.show_win_message()
                    
                    # Reset selection after attempting move
                    self.selected_tube = None
                    self.selected_layer_pos = None
    
    def show_win_message(self):
        """Display win message and update progress"""
        self.game_state = GameState.LEVEL_COMPLETE
        
        # Calculate stars based on moves
        if self.level_info:
            stars = self.progress.complete_level(
                self.current_level, 
                self.game.moves, 
                self.level_info.par_moves
            )
            
            # Add celebration particles
            for _ in range(30):
                self.particles.add_particle(
                    'confetti', 
                    self.screen_width // 2 + random.randint(-100, 100),
                    self.screen_height // 2 + random.randint(-100, 100)
                )
    
    def get_tube_rect(self, tube_idx: int) -> pygame.Rect:
        """Calculate tube position in grid"""
        col = tube_idx % self.game.width
        row = tube_idx // self.game.width
        
        x = self.margin + col * (self.tube_width + 20)
        y = self.margin + row * (self.tube_height + 20)
        
        return pygame.Rect(x, y, self.tube_width, self.tube_height)
    
    def draw_main_menu(self):
        """Draw the main menu screen"""
        # Draw background
        self.screen.blit(self.bg_gradient, (0, 0))
        
        # Draw title
        title = self.big_font.render("Cake Sort Puzzle", True, self.text_color)
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 150))
        
        # Draw buttons
        button_rects = []
        
        # Play button
        play_rect = pygame.Rect(self.screen_width//2 - 100, 300, 200, 50)
        button_rects.append((play_rect, "Play", (0, 180, 0)))
        
        # Settings button
        settings_rect = pygame.Rect(self.screen_width//2 - 100, 380, 200, 50)
        button_rects.append((settings_rect, "Settings", (0, 120, 180)))
        
        # Shop button
        shop_rect = pygame.Rect(self.screen_width//2 - 100, 460, 200, 50)
        button_rects.append((shop_rect, "Shop", (180, 120, 0)))
        
        for rect, text, color in button_rects:
            pygame.draw.rect(self.screen, color, rect, 0, 10)
            text_surf = self.font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surf, (rect.centerx - text_surf.get_width()//2, rect.centery - text_surf.get_height()//2))
        
        # Draw player stats
        stats_y = self.screen_height - 100
        
        # Current level
        level_text = self.font.render(f"Current Level: {self.progress.current_level}", True, self.text_color)
        self.screen.blit(level_text, (20, stats_y))
        
        # Stars collected
        stars_text = self.font.render(f"Stars: {self.progress.get_total_stars()}", True, self.text_color)
        self.screen.blit(stars_text, (20, stats_y + 30))
        
        # Coins
        coins_text = self.font.render(f"Coins: {self.progress.coins}", True, self.text_color)
        self.screen.blit(coins_text, (20, stats_y + 60))
    
    def draw_level_select(self):
        """Draw the level select screen"""
        # Draw background
        self.screen.blit(self.bg_gradient, (0, 0))
        
        # Draw title
        title = self.big_font.render("Select Level", True, self.text_color)
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 40))
        
        # Draw back button
        back_rect = pygame.Rect(20, 20, 100, 40)
        pygame.draw.rect(self.screen, (180, 0, 0), back_rect, 0, 10)
        back_text = self.font.render("Back", True, (255, 255, 255))
        self.screen.blit(back_text, (back_rect.centerx - back_text.get_width()//2, back_rect.centery - back_text.get_height()//2))
        
        # Draw level buttons
        for level_num, level_info in self.level_manager.levels.items():
            row = (level_num - 1) // 5
            col = (level_num - 1) % 5
            
            x = self.margin + col * 180
            y = 150 + row * 180
            
            # Level button background
            level_rect = pygame.Rect(x, y, 150, 150)
            
            if level_num <= self.progress.max_level:
                # Unlocked level
                color = (0, 150, 0) if level_num == self.current_level else (0, 100, 150)
                pygame.draw.rect(self.screen, color, level_rect, 0, 10)
                
                # Level number
                level_text = self.big_font.render(str(level_num), True, (255, 255, 255))
                self.screen.blit(level_text, (x + 75 - level_text.get_width()//2, y + 40 - level_text.get_height()//2))
                
                # Difficulty
                diff_text = self.font.render(level_info.difficulty, True, (255, 255, 255))
                self.screen.blit(diff_text, (x + 75 - diff_text.get_width()//2, y + 75))
                
                # Stars earned
                stars = self.progress.stars.get(str(level_num), 0)
                for i in range(3):
                    star_color = (255, 255, 0) if i < stars else (100, 100, 100)
                    star_center = (x + 50 + i * 25, y + 110)
                    pygame.draw.circle(self.screen, star_color, star_center, 12)
            else:
                # Locked level
                pygame.draw.rect(self.screen, (100, 100, 100), level_rect, 0, 10)
                lock_text = self.font.render("🔒", True, (200, 200, 200))
                self.screen.blit(lock_text, (x + 75 - lock_text.get_width()//2, y + 75 - lock_text.get_height()//2))
    
    def draw_settings(self):
        """Draw the settings screen"""
        # Draw background
        self.screen.blit(self.bg_gradient, (0, 0))
        
        # Draw title
        title = self.big_font.render("Settings", True, self.text_color)
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 40))
        
        # Draw back button
        back_rect = pygame.Rect(20, 20, 100, 40)
        pygame.draw.rect(self.screen, (180, 0, 0), back_rect, 0, 10)
        back_text = self.font.render("Back", True, (255, 255, 255))
        self.screen.blit(back_text, (back_rect.centerx - back_text.get_width()//2, back_rect.centery - back_text.get_height()//2))
        
        # Draw Theme options
        theme_title = self.font.render("Theme:", True, self.text_color)
        self.screen.blit(theme_title, (self.screen_width//2 - 180, 120))
        
        theme_y = 180
        for i, theme_name in enumerate(THEMES.keys()):
            if theme_name in self.progress.unlocked_themes:
                # Theme button
                theme_rect = pygame.Rect(self.screen_width//2 - 150, theme_y + i * 60, 300, 50)
                is_selected = theme_name == self.progress.theme
                color = (0, 150, 0) if is_selected else (100, 100, 100)
                pygame.draw.rect(self.screen, color, theme_rect, 0, 10)
                
                # Theme name
                theme_text = self.font.render(theme_name.capitalize(), True, (255, 255, 255))
                self.screen.blit(theme_text, (theme_rect.centerx - theme_text.get_width()//2, theme_rect.centery - theme_text.get_height()//2))
            else:
                # Locked theme
                theme_rect = pygame.Rect(self.screen_width//2 - 150, theme_y + i * 60, 300, 50)
                pygame.draw.rect(self.screen, (70, 70, 70), theme_rect, 0, 10)
                
                # Theme name with lock
                theme_text = self.font.render(f"{theme_name.capitalize()} 🔒", True, (150, 150, 150))
                self.screen.blit(theme_text, (theme_rect.centerx - theme_text.get_width()//2, theme_rect.centery - theme_text.get_height()//2))
        
        # Controls help
        controls_y = 450
        controls_title = self.font.render("Controls:", True, self.text_color)
        self.screen.blit(controls_title, (self.screen_width//2 - 180, controls_y))
        
        controls = [
            "Click - Select/move layers",
            "R - Reset level",
            "H - Get hint",
            "M - Main menu",
            "N/P - Next/Previous level"
        ]
        
        for i, text in enumerate(controls):
            control_text = self.small_font.render(text, True, self.text_color)
            self.screen.blit(control_text, (self.screen_width//2 - 150, controls_y + 40 + i * 25))
    
    def draw_shop(self):
        """Draw the shop screen"""
        # Draw background
        self.screen.blit(self.bg_gradient, (0, 0))
        
        # Draw title
        title = self.big_font.render("Shop", True, self.text_color)
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 40))
        
        # Draw back button
        back_rect = pygame.Rect(20, 20, 100, 40)
        pygame.draw.rect(self.screen, (180, 0, 0), back_rect, 0, 10)
        back_text = self.font.render("Back", True, (255, 255, 255))
        self.screen.blit(back_text, (back_rect.centerx - back_text.get_width()//2, back_rect.centery - back_text.get_height()//2))
        
        # Draw coins
        coins_text = self.font.render(f"Coins: {self.progress.coins}", True, self.text_color)
        self.screen.blit(coins_text, (self.screen_width - 180, 30))
        
        # Available themes to purchase
        theme_costs = {
            "pastel": 100,
            "chocolate": 200,
            "frosting": 300
        }
        
        shop_title = self.font.render("Available Themes:", True, self.text_color)
        self.screen.blit(shop_title, (self.screen_width//2 - 180, 120))
        
        theme_y = 180
        for i, (theme_name, cost) in enumerate(theme_costs.items()):
            # Theme item row
            theme_rect = pygame.Rect(self.screen_width//2 - 250, theme_y + i * 60, 400, 50)
            pygame.draw.rect(self.screen, (50, 50, 70), theme_rect, 0, 10)
            
            # Theme name
            theme_text = self.font.render(theme_name.capitalize(), True, (255, 255, 255))
            self.screen.blit(theme_text, (theme_rect.x + 20, theme_rect.centery - theme_text.get_height()//2))
            
            if theme_name in self.progress.unlocked_themes:
                # Already owned
                status_text = self.font.render("Owned", True, (0, 255, 0))
                self.screen.blit(status_text, (theme_rect.right - 120, theme_rect.centery - status_text.get_height()//2))
            else:
                # Purchase button
                button_rect = pygame.Rect(theme_rect.right - 170, theme_rect.y + 5, 150, 40)
                can_afford = self.progress.coins >= cost
                button_color = (0, 150, 0) if can_afford else (150, 0, 0)
                pygame.draw.rect(self.screen, button_color, button_rect, 0, 10)
                
                # Button text with cost
                button_text = self.font.render(f"Buy for {cost} 🪙", True, (255, 255, 255))
                self.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, button_rect.centery - button_text.get_height()//2))
    
    def draw_level_complete(self):
        """Draw level complete screen"""
        # First draw the game state in the background
        self.draw_tubes()
        
        # Add semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Draw "Level Complete" text
        win_text = self.big_font.render("Level Complete!", True, (255, 255, 255))
        self.screen.blit(win_text, 
                        (self.screen_width//2 - win_text.get_width()//2, 
                         self.screen_height//2 - 100))
        
        # Draw stars earned
        stars = self.progress.stars.get(str(self.current_level), 0)
        for i in range(3):
            star_color = (255, 255, 0) if i < stars else (100, 100, 100)
            star_center = (self.screen_width//2 - 60 + i * 60, self.screen_height//2 - 20)
            
            # Draw a simple star
            points = []
            for j in range(5):
                # Outer points
                angle = j * 2 * math.pi / 5 - math.pi / 2
                points.append((
                    star_center[0] + 20 * math.cos(angle),
                    star_center[1] + 20 * math.sin(angle)
                ))
                # Inner points
                angle += math.pi / 5
                points.append((
                    star_center[0] + 10 * math.cos(angle),
                    star_center[1] + 10 * math.sin(angle)
                ))
            pygame.draw.polygon(self.screen, star_color, points)
        
        # Draw moves taken
        moves_text = self.font.render(f"Moves: {self.game.moves}", True, (255, 255, 255))
        self.screen.blit(moves_text, 
                        (self.screen_width//2 - moves_text.get_width()//2, 
                         self.screen_height//2 + 20))
        
        # Draw coins earned
        coins_earned = stars * 10
        coins_text = self.font.render(f"Coins earned: {coins_earned}", True, (255, 255, 0))
        self.screen.blit(coins_text, 
                        (self.screen_width//2 - coins_text.get_width()//2, 
                         self.screen_height//2 + 50))
        
        # Draw "Next Level" button
        next_button_rect = pygame.Rect(self.screen_width//2 - 100, self.screen_height//2 + 90, 200, 50)
        pygame.draw.rect(self.screen, (0, 180, 0), next_button_rect, 0, 10)
        
        next_text = self.font.render("Next Level", True, (255, 255, 255))
        self.screen.blit(next_text, 
                        (next_button_rect.centerx - next_text.get_width()//2, 
                         next_button_rect.centery - next_text.get_height()//2))
        
        # Draw "Back to Menu" button
        menu_rect = pygame.Rect(self.screen_width//2 - 100, self.screen_height//2 + 160, 200, 50)
        pygame.draw.rect(self.screen, (180, 0, 0), menu_rect, 0, 10)
        
        menu_text = self.font.render("Back to Menu", True, (255, 255, 255))
        self.screen.blit(menu_text, 
                        (menu_rect.centerx - menu_text.get_width()//2, 
                         menu_rect.centery - menu_text.get_height()//2))
    
    def draw_tubes(self):
        """Draw the tubes and cake layers"""
        # Draw title and level info
        title = self.big_font.render(f"Level {self.current_level}", True, self.text_color)
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 10))
        
        # Draw moves
        moves_text = self.font.render(f"Moves: {self.game.moves}", True, self.text_color)
        self.screen.blit(moves_text, (20, 20))
        
        # Draw coins
        coins_text = self.font.render(f"Coins: {self.progress.coins}", True, self.text_color)
        self.screen.blit(coins_text, (self.screen_width - coins_text.get_width() - 20, 20))
        
        # Draw theme
        theme_text = self.small_font.render(f"Theme: {self.current_theme.name}", True, self.text_color)
        self.screen.blit(theme_text, (self.screen_width - theme_text.get_width() - 20, 50))
        
        # Draw tubes
        for tube_idx, tube in enumerate(self.game.tubes):
            tube_rect = self.get_tube_rect(tube_idx)
            
            # Draw tube outline
            pygame.draw.rect(self.screen, self.tube_color, tube_rect, 0, 10)
            pygame.draw.rect(self.screen, (150, 150, 160), tube_rect, 2, 10)
            
            # Highlight selected tube
            if tube_idx == self.selected_tube:
                highlight = pygame.Surface((self.tube_width, self.tube_height), pygame.SRCALPHA)
                highlight.fill(self.selected_color)
                self.screen.blit(highlight, tube_rect.topleft)
            
            # Draw layers
            for i, layer in enumerate(tube.layers):
                layer_rect = pygame.Rect(
                    tube_rect.x,
                    tube_rect.y + tube_rect.height - (i+1)*self.layer_height,
                    tube_rect.width,
                    self.layer_height
                )
                
                # Get layer color from theme
                color = self.current_theme.get_layer_color(layer.color)
                pygame.draw.rect(self.screen, color, layer_rect, 0, 5)
                pygame.draw.rect(self.screen, (0, 0, 0), layer_rect, 1, 5)
                
                # Draw decorations if theme has them
                decoration = self.current_theme.get_decoration(layer.color)
                if decoration:
                    decoration_type, decoration_color = decoration
                    draw_cake_decoration(self.screen, decoration_type, layer_rect, decoration_color)
                
                # Draw layer size
                size_text = self.font.render(str(layer.size), True, (0, 0, 0))
                self.screen.blit(size_text, 
                               (layer_rect.centerx - size_text.get_width()//2,
                                layer_rect.centery - size_text.get_height()//2))
        
        # Draw controls help
        if self.game_state == GameState.PLAYING:
            controls = [
                "R - Reset",
                "H - Hint",
                "M - Menu"
            ]
            
            for i, text in enumerate(controls):
                y_pos = self.screen_height - 80 + i * 25
                draw_text(self.screen, text, (20, y_pos), self.small_font, self.text_color)
    
    def draw(self):
        """Draw the game state"""
        # Clear screen
        self.screen.fill(self.bg_color)
        
        # Draw appropriate screen based on game state
        if self.game_state == GameState.MAIN_MENU:
            self.draw_main_menu()
        elif self.game_state == GameState.LEVEL_SELECT:
            self.draw_level_select()
        elif self.game_state == GameState.PLAYING:
            self.draw_tubes()
        elif self.game_state == GameState.LEVEL_COMPLETE:
            self.draw_level_complete()
        elif self.game_state == GameState.SETTINGS:
            self.draw_settings()
        elif self.game_state == GameState.SHOP:
            self.draw_shop()
        
        # Draw particles on top
        self.particles.draw(self.screen)
        
        # Update display
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        running = True
        while running:
            # Handle events
            running = self.handle_events()
            
            # Update particles
            self.particles.update()
            
            # Draw everything
            self.draw()
            
            # Cap the frame rate
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game_ui = CakeGameUI()
    game_ui.run()