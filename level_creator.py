"""
Level creator utility for Cake Sort Puzzle game.
This script helps create and test new levels.
"""

import pygame
import sys
import os
import random
from typing import Dict, List, Tuple

# Make sure we can import game modules
sys.path.append('.')
from game.core import CakeGame, CakeLayer, Tube

class LevelCreator:
    def __init__(self):
        pygame.init()
        
        # UI Settings
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cake Sort Puzzle - Level Creator")
        
        # Fonts
        self.font = pygame.font.SysFont('Arial', 24)
        self.small_font = pygame.font.SysFont('Arial', 18)
        
        # Colors
        self.bg_color = (240, 240, 250)
        self.text_color = (50, 50, 50)
        self.button_color = (100, 100, 200)
        self.tube_color = (200, 200, 210)
        self.selected_color = (255, 255, 0, 150)
        
        # Available colors for cake layers
        self.available_colors = ['R', 'G', 'B', 'Y', 'P', 'O', 'C', 'M']
        self.color_map = {
            'R': (255, 0, 0),
            'G': (0, 255, 0),
            'B': (0, 0, 255),
            'Y': (255, 255, 0),
            'P': (255, 0, 255),
            'O': (255, 165, 0),
            'C': (0, 255, 255),
            'M': (150, 0, 150)
        }
        
        # Level settings
        self.width = 4
        self.height = 3
        self.game = CakeGame(self.width, self.height)
        self.tube_width = 80
        self.tube_height = 300
        self.layer_height = 40
        self.margin = 50
        
        # Editor state
        self.selected_tube = None
        self.selected_color = 'R'
        self.selected_size = 1
        self.level_number = 1
        self.difficulty = "Medium"
        self.par_moves = 10
        self.status_message = ""
        self.status_time = 0
        
        # Test mode
        self.test_mode = False
        self.test_game = None
        self.selected_test_tube = None
        self.selected_test_layer = None
    
    def get_tube_rect(self, tube_idx: int) -> pygame.Rect:
        """Calculate tube position in grid"""
        col = tube_idx % self.width
        row = tube_idx // self.width
        
        x = self.margin + col * (self.tube_width + 20)
        y = self.margin + row * (self.tube_height + 20)
        
        return pygame.Rect(x, y, self.tube_width, self.tube_height)
    
    def handle_events(self):
        """Process user input"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if self.test_mode:
                self.handle_test_events(event)
            else:
                self.handle_editor_events(event)
        
        return True
    
    def handle_editor_events(self, event):
        """Handle events in editor mode"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Check for tube clicks
            for tube_idx in range(len(self.game.tubes)):
                tube_rect = self.get_tube_rect(tube_idx)
                if tube_rect.collidepoint(mouse_pos):
                    self.selected_tube = tube_idx
                    return
            
            # Check for color palette clicks
            palette_rect = pygame.Rect(self.screen_width - 200, 100, 150, 200)
            if palette_rect.collidepoint(mouse_pos):
                color_idx = (mouse_pos[1] - 100) // 25
                if 0 <= color_idx < len(self.available_colors):
                    self.selected_color = self.available_colors[color_idx]
                    return
            
            # Check for size buttons
            for i in range(1, 6):
                size_rect = pygame.Rect(self.screen_width - 200, 320 + (i-1)*40, 40, 30)
                if size_rect.collidepoint(mouse_pos):
                    self.selected_size = i
                    return
            
            # Check for action buttons
            if pygame.Rect(self.screen_width - 200, 500, 150, 40).collidepoint(mouse_pos):
                # Add layer
                if self.selected_tube is not None:
                    tube = self.game.tubes[self.selected_tube]
                    if len(tube.layers) < tube.max_capacity:
                        tube.add_layer(CakeLayer(self.selected_color, self.selected_size))
                return
            
            if pygame.Rect(self.screen_width - 200, 550, 150, 40).collidepoint(mouse_pos):
                # Remove layer
                if self.selected_tube is not None:
                    tube = self.game.tubes[self.selected_tube]
                    if tube.layers:
                        tube.remove_layer(len(tube.layers) - 1)
                return
            
            if pygame.Rect(self.screen_width - 200, 600, 150, 40).collidepoint(mouse_pos):
                # Clear tube
                if self.selected_tube is not None:
                    self.game.tubes[self.selected_tube] = Tube(self.game.max_capacity)
                return
            
            if pygame.Rect(self.screen_width - 200, 650, 150, 40).collidepoint(mouse_pos):
                # Test level
                self.enter_test_mode()
                return
            
            # Width/height adjustment
            if pygame.Rect(100, self.screen_height - 100, 30, 30).collidepoint(mouse_pos):
                # Decrease width
                if self.width > 2:
                    self.width -= 1
                    self.resize_game()
                return
            
            if pygame.Rect(170, self.screen_height - 100, 30, 30).collidepoint(mouse_pos):
                # Increase width
                if self.width < 6:
                    self.width += 1
                    self.resize_game()
                return
            
            if pygame.Rect(100, self.screen_height - 60, 30, 30).collidepoint(mouse_pos):
                # Decrease height
                if self.height > 2:
                    self.height -= 1
                    self.resize_game()
                return
            
            if pygame.Rect(170, self.screen_height - 60, 30, 30).collidepoint(mouse_pos):
                # Increase height
                if self.height < 5:
                    self.height += 1
                    self.resize_game()
                return
            
            # Level number adjustment
            if pygame.Rect(350, self.screen_height - 100, 30, 30).collidepoint(mouse_pos):
                # Decrease level
                if self.level_number > 1:
                    self.level_number -= 1
                return
            
            if pygame.Rect(420, self.screen_height - 100, 30, 30).collidepoint(mouse_pos):
                # Increase level
                self.level_number += 1
                return
            
            # Par moves adjustment
            if pygame.Rect(350, self.screen_height - 60, 30, 30).collidepoint(mouse_pos):
                # Decrease par moves
                if self.par_moves > 1:
                    self.par_moves -= 1
                return
            
            if pygame.Rect(420, self.screen_height - 60, 30, 30).collidepoint(mouse_pos):
                # Increase par moves
                self.par_moves += 1
                return
            
            # Difficulty selection
            difficulties = ["Easy", "Medium", "Hard", "Expert"]
            for i, diff in enumerate(difficulties):
                diff_rect = pygame.Rect(500 + i*100, self.screen_height - 80, 80, 30)
                if diff_rect.collidepoint(mouse_pos):
                    self.difficulty = diff
                    return
            
            # Save/load buttons
            if pygame.Rect(self.screen_width - 200, 700, 70, 40).collidepoint(mouse_pos):
                # Save level
                self.save_level()
                return
            
            if pygame.Rect(self.screen_width - 120, 700, 70, 40).collidepoint(mouse_pos):
                # Load level
                self.load_level()
                return
            
            # Random level generation
            if pygame.Rect(500, self.screen_height - 40, 180, 30).collidepoint(mouse_pos):
                self.generate_random_level()
                return
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.save_level()
            elif event.key == pygame.K_l and pygame.key.get_mods() & pygame.KMOD_CTRL:
                self.load_level()
            elif event.key == pygame.K_t:
                self.enter_test_mode()
            elif event.key == pygame.K_r:
                self.generate_random_level()
    
    def handle_test_events(self, event):
        """Handle events in test mode"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.exit_test_mode()
                return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            
            # Exit button
            if pygame.Rect(self.screen_width - 120, 20, 100, 40).collidepoint(mouse_pos):
                self.exit_test_mode()
                return
            
            # Handle tube clicks for testing
            for tube_idx, tube in enumerate(self.test_game.tubes):
                tube_rect = self.get_tube_rect(tube_idx)
                if tube_rect.collidepoint(mouse_pos):
                    if self.selected_test_tube is None:
                        if not tube.is_empty():
                            self.selected_test_tube = tube_idx
                            # Find which layer was clicked
                            rel_y = mouse_pos[1] - tube_rect.y
                            self.selected_test_layer = min(
                                len(tube.layers) - 1 - (rel_y // self.layer_height),
                                len(tube.layers) - 1
                            )
                    else:
                        # Try to move the selected layer
                        if tube_idx != self.selected_test_tube:
                            self.test_game.move_layer(
                                self.selected_test_tube, 
                                self.selected_test_layer, 
                                tube_idx
                            )
                        
                        self.selected_test_tube = None
                        self.selected_test_layer = None
                    return
    
    def resize_game(self):
        """Resize the game grid"""
        old_tubes = self.game.tubes.copy()
        self.game = CakeGame(self.width, self.height)
        
        # Copy over tube data for tubes that still exist
        for i in range(min(len(old_tubes), len(self.game.tubes))):
            self.game.tubes[i] = old_tubes[i]
        
        # Reset selected tube if it's now out of bounds
        if self.selected_tube is not None and self.selected_tube >= len(self.game.tubes):
            self.selected_tube = None
    
    def enter_test_mode(self):
        """Switch to test mode"""
        self.test_mode = True
        
        # Create a copy of the game for testing
        self.test_game = CakeGame(self.width, self.height)
        for i, tube in enumerate(self.game.tubes):
            self.test_game.tubes[i] = Tube(self.game.max_capacity)
            for layer in tube.layers:
                self.test_game.tubes[i].add_layer(CakeLayer(layer.color, layer.size))
        
        self.selected_test_tube = None
        self.selected_test_layer = None
    
    def exit_test_mode(self):
        """Exit test mode"""
        self.test_mode = False
        self.test_game = None
    
    def save_level(self):
        """Save the current level to a file"""
        os.makedirs("game/levels", exist_ok=True)
        
        filename = f"game/levels/level{self.level_number}.txt"
        
        try:
            with open(filename, 'w') as f:
                f.write(f"# Level {self.level_number}\n")
                f.write(f"# Difficulty: {self.difficulty}\n")
                f.write(f"# Moves: {self.par_moves}\n")
                f.write(f"width: {self.width}\n")
                f.write(f"height: {self.height}\n")
                
                for i, tube in enumerate(self.game.tubes):
                    layers_str = " ".join([f"{layer.color}{layer.size}" for layer in tube.layers])
                    f.write(f"{i}: {layers_str}\n")
            
            self.status_message = f"Level saved to {filename}"
            self.status_time = pygame.time.get_ticks()
        except Exception as e:
            self.status_message = f"Error saving level: {e}"
            self.status_time = pygame.time.get_ticks()
    
    def load_level(self):
        """Load a level from file"""
        filename = f"game/levels/level{self.level_number}.txt"
        
        try:
            # Read level first to get dimensions
            with open(filename, 'r') as f:
                for line in f:
                    if line.startswith("width:"):
                        self.width = int(line.split(":")[1].strip())
                    elif line.startswith("height:"):
                        self.height = int(line.split(":")[1].strip())
                    elif line.startswith("# Difficulty:"):
                        self.difficulty = line.split(":")[1].strip()
                    elif line.startswith("# Moves:"):
                        self.par_moves = int(line.split(":")[1].strip())
            
            # Create a new game with the right dimensions
            self.game = CakeGame(self.width, self.height)
            
            # Now load the level data
            self.game.initialize_level(filename)
            
            self.status_message = f"Level loaded from {filename}"
            self.status_time = pygame.time.get_ticks()
        except FileNotFoundError:
            self.status_message = f"Level file not found: {filename}"
            self.status_time = pygame.time.get_ticks()
        except Exception as e:
            self.status_message = f"Error loading level: {e}"
            self.status_time = pygame.time.get_ticks()
    
    def generate_random_level(self):
        """Create a random puzzle level"""
        # Determine number of colors based on difficulty
        if self.difficulty == "Easy":
            num_colors = min(3, self.width * self.height - 2)
        elif self.difficulty == "Medium":
            num_colors = min(4, self.width * self.height - 2)
        elif self.difficulty == "Hard":
            num_colors = min(6, self.width * self.height - 2)
        else:  # Expert
            num_colors = min(8, self.width * self.height - 2)
        
        # Number of empty tubes (at least 1)
        empty_tubes = max(1, self.width * self.height - num_colors)
        
        # Reset game
        self.game = CakeGame(self.width, self.height)
        
        # Select random colors
        colors = random.sample(self.available_colors, num_colors)
        
        # Create layers for each color
        all_layers = []
        for color in colors:
            # Random size between 1-5
            size = random.randint(1, 5)
            # Create identical layers for this color
            for _ in range(self.game.max_capacity):
                all_layers.append(CakeLayer(color, size))
        
        # Shuffle layers
        random.shuffle(all_layers)
        
        # Distribute layers to tubes
        tube_idx = 0
        for layer in all_layers:
            # Skip empty tubes
            if tube_idx >= self.width * self.height - empty_tubes:
                tube_idx = 0
            
            # Add layer to tube
            if len(self.game.tubes[tube_idx].layers) < self.game.max_capacity:
                self.game.tubes[tube_idx].add_layer(layer)
            else:
                tube_idx += 1
                if tube_idx >= self.width * self.height - empty_tubes:
                    tube_idx = 0
                self.game.tubes[tube_idx].add_layer(layer)
        
        # Estimate par moves based on complexity
        self.par_moves = num_colors * self.game.max_capacity // 2
        
        self.status_message = f"Generated random {self.difficulty} level"
        self.status_time = pygame.time.get_ticks()
    
    def draw(self):
        """Draw the level editor interface"""
        self.screen.fill(self.bg_color)
        
        if self.test_mode:
            self.draw_test_mode()
        else:
            self.draw_editor_mode()
        
        pygame.display.flip()
    
    def draw_editor_mode(self):
        """Draw the level editor interface"""
        # Draw title
        title = self.font.render("Cake Sort Puzzle - Level Editor", True, self.text_color)
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 20))
        
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
            
            # Draw tube index
            idx_text = self.small_font.render(str(tube_idx), True, (0, 0, 0))
            self.screen.blit(idx_text, (tube_rect.x + 5, tube_rect.y + 5))
            
            # Draw layers
            for i, layer in enumerate(tube.layers):
                layer_rect = pygame.Rect(
                    tube_rect.x,
                    tube_rect.y + tube_rect.height - (i+1)*self.layer_height,
                    tube_rect.width,
                    self.layer_height
                )
                
                # Draw layer with color
                color = self.color_map.get(layer.color, (200, 200, 200))
                pygame.draw.rect(self.screen, color, layer_rect, 0, 5)
                pygame.draw.rect(self.screen, (0, 0, 0), layer_rect, 1, 5)
                
                # Draw layer size
                size_text = self.font.render(str(layer.size), True, (0, 0, 0))
                self.screen.blit(size_text, 
                               (layer_rect.centerx - size_text.get_width()//2,
                                layer_rect.centery - size_text.get_height()//2))
        
        # Draw color palette
        pygame.draw.rect(self.screen, (220, 220, 230), pygame.Rect(self.screen_width - 220, 80, 200, 250), 0, 10)
        title = self.font.render("Color Palette", True, self.text_color)
        self.screen.blit(title, (self.screen_width - 200, 50))
        
        for i, color_code in enumerate(self.available_colors):
            color = self.color_map.get(color_code, (200, 200, 200))
            color_rect = pygame.Rect(self.screen_width - 180, 100 + i*25, 80, 20)
            pygame.draw.rect(self.screen, color, color_rect, 0, 5)
            
            # Highlight selected color
            if color_code == self.selected_color:
                pygame.draw.rect(self.screen, (0, 0, 0), color_rect, 2, 5)
            
            # Draw color code
            code_text = self.small_font.render(color_code, True, (0, 0, 0))
            self.screen.blit(code_text, (self.screen_width - 190, 100 + i*25))
        
        # Draw size selector
        title = self.font.render("Size", True, self.text_color)
        self.screen.blit(title, (self.screen_width - 200, 300))
        
        for i in range(1, 6):
            size_rect = pygame.Rect(self.screen_width - 200, 320 + (i-1)*40, 40, 30)
            pygame.draw.rect(self.screen, (200, 200, 200), size_rect, 0, 5)
            
            # Highlight selected size
            if i == self.selected_size:
                pygame.draw.rect(self.screen, (0, 0, 0), size_rect, 2, 5)
            
            # Draw size number
            size_text = self.font.render(str(i), True, (0, 0, 0))
            self.screen.blit(size_text, (size_rect.centerx - size_text.get_width()//2, size_rect.centery - size_text.get_height()//2))
        
        # Draw action buttons
        buttons = [
            ("Add Layer", (0, 150, 0), pygame.Rect(self.screen_width - 200, 500, 150, 40)),
            ("Remove Layer", (150, 0, 0), pygame.Rect(self.screen_width - 200, 550, 150, 40)),
            ("Clear Tube", (150, 150, 0), pygame.Rect(self.screen_width - 200, 600, 150, 40)),
            ("Test Level", (0, 0, 150), pygame.Rect(self.screen_width - 200, 650, 150, 40)),
            ("Save", (0, 100, 0), pygame.Rect(self.screen_width - 200, 700, 70, 40)),
            ("Load", (100, 0, 0), pygame.Rect(self.screen_width - 120, 700, 70, 40))
        ]
        
        for text, color, rect in buttons:
            pygame.draw.rect(self.screen, color, rect, 0, 10)
            button_text = self.small_font.render(text, True, (255, 255, 255))
            self.screen.blit(button_text, (rect.centerx - button_text.get_width()//2, rect.centery - button_text.get_height()//2))
        
        # Draw level dimensions controls
        dim_text = self.font.render("Level Dimensions:", True, self.text_color)
        self.screen.blit(dim_text, (20, self.screen_height - 130))
        
        # Width controls
        width_text = self.font.render(f"Width: {self.width}", True, self.text_color)
        self.screen.blit(width_text, (20, self.screen_height - 100))
        
        pygame.draw.rect(self.screen, (180, 0, 0), pygame.Rect(100, self.screen_height - 100, 30, 30), 0, 5)
        pygame.draw.rect(self.screen, (0, 180, 0), pygame.Rect(170, self.screen_height - 100, 30, 30), 0, 5)
        
        minus = self.font.render("-", True, (255, 255, 255))
        plus = self.font.render("+", True, (255, 255, 255))
        
        self.screen.blit(minus, (110, self.screen_height - 100))
        self.screen.blit(plus, (180, self.screen_height - 100))
        
        # Height controls
        height_text = self.font.render(f"Height: {self.height}", True, self.text_color)
        self.screen.blit(height_text, (20, self.screen_height - 60))
        
        pygame.draw.rect(self.screen, (180, 0, 0), pygame.Rect(100, self.screen_height - 60, 30, 30), 0, 5)
        pygame.draw.rect(self.screen, (0, 180, 0), pygame.Rect(170, self.screen_height - 60, 30, 30), 0, 5)
        
        self.screen.blit(minus, (110, self.screen_height - 60))
        self.screen.blit(plus, (180, self.screen_height - 60))
        
        # Level number controls
        level_text = self.font.render(f"Level: {self.level_number}", True, self.text_color)
        self.screen.blit(level_text, (250, self.screen_height - 100))
        
        pygame.draw.rect(self.screen, (180, 0, 0), pygame.Rect(350, self.screen_height - 100, 30, 30), 0, 5)
        pygame.draw.rect(self.screen, (0, 180, 0), pygame.Rect(420, self.screen_height - 100, 30, 30), 0, 5)
        
        self.screen.blit(minus, (360, self.screen_height - 100))
        self.screen.blit(plus, (430, self.screen_height - 100))
        
        # Par moves controls
        par_text = self.font.render(f"Par Moves: {self.par_moves}", True, self.text_color)
        self.screen.blit(par_text, (250, self.screen_height - 60))
        
        pygame.draw.rect(self.screen, (180, 0, 0), pygame.Rect(350, self.screen_height - 60, 30, 30), 0, 5)
        pygame.draw.rect(self.screen, (0, 180, 0), pygame.Rect(420, self.screen_height - 60, 30, 30), 0, 5)
        
        self.screen.blit(minus, (360, self.screen_height - 60))
        self.screen.blit(plus, (430, self.screen_height - 60))
        
        # Difficulty selection
        diff_text = self.font.render("Difficulty:", True, self.text_color)
        self.screen.blit(diff_text, (500, self.screen_height - 100))
        
        difficulties = ["Easy", "Medium", "Hard", "Expert"]
        for i, diff in enumerate(difficulties):
            diff_rect = pygame.Rect(500 + i*100, self.screen_height - 80, 80, 30)
            color = (0, 150, 0) if diff == self.difficulty else (100, 100, 100)
            pygame.draw.rect(self.screen, color, diff_rect, 0, 5)
            
            text = self.small_font.render(diff, True, (255, 255, 255))
            self.screen.blit(text, (diff_rect.centerx - text.get_width()//2, diff_rect.centery - text.get_height()//2))
        
        # Random level generator
        random_rect = pygame.Rect(500, self.screen_height - 40, 180, 30)
        pygame.draw.rect(self.screen, (100, 0, 100), random_rect, 0, 5)
        
        random_text = self.font.render("Generate Random", True, (255, 255, 255))
        self.screen.blit(random_text, (random_rect.centerx - random_text.get_width()//2, random_rect.centery - random_text.get_height()//2))
        
        # Display status message
        if pygame.time.get_ticks() - self.status_time < 3000:  # Display for 3 seconds
            status_surface = self.font.render(self.status_message, True, (0, 100, 0))
            self.screen.blit(status_surface, (self.screen_width//2 - status_surface.get_width()//2, self.screen_height - 40))
    
    def draw_test_mode(self):
        """Draw the test mode interface"""
        # Draw title
        title = self.font.render("Cake Sort Puzzle - Test Mode", True, self.text_color)
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 20))
        
        # Draw exit button
        exit_rect = pygame.Rect(self.screen_width - 120, 20, 100, 40)
        pygame.draw.rect(self.screen, (180, 0, 0), exit_rect, 0, 10)
        exit_text = self.font.render("Exit", True, (255, 255, 255))
        self.screen.blit(exit_text, (exit_rect.centerx - exit_text.get_width()//2, exit_rect.centery - exit_text.get_height()//2))
        
        # Draw moves counter
        moves_text = self.font.render(f"Moves: {self.test_game.moves}", True, self.text_color)
        self.screen.blit(moves_text, (20, 20))
        
        # Draw instructions
        help_text = self.small_font.render("Click tubes to move layers. ESC to exit.", True, self.text_color)
        self.screen.blit(help_text, (self.screen_width//2 - help_text.get_width()//2, 60))
        
        # Draw tubes
        for tube_idx, tube in enumerate(self.test_game.tubes):
            tube_rect = self.get_tube_rect(tube_idx)
            
            # Draw tube outline
            pygame.draw.rect(self.screen, self.tube_color, tube_rect, 0, 10)
            pygame.draw.rect(self.screen, (150, 150, 160), tube_rect, 2, 10)
            
            # Highlight selected tube
            if tube_idx == self.selected_test_tube:
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
                
                # Draw layer with color
                color = self.color_map.get(layer.color, (200, 200, 200))
                pygame.draw.rect(self.screen, color, layer_rect, 0, 5)
                pygame.draw.rect(self.screen, (0, 0, 0), layer_rect, 1, 5)
                
                # Draw layer size
                size_text = self.font.render(str(layer.size), True, (0, 0, 0))
                self.screen.blit(size_text, 
                               (layer_rect.centerx - size_text.get_width()//2,
                                layer_rect.centery - size_text.get_height()//2))
        
        # Display completion message
        if self.test_game.is_solved():
            solved_text = self.big_font.render("Level Solved!", True, (0, 150, 0))
            self.screen.blit(solved_text, (self.screen_width//2 - solved_text.get_width()//2, self.screen_height - 100))
            
            par_text = self.font.render(f"Moves: {self.test_game.moves} / Par: {self.par_moves}", True, self.text_color)
            self.screen.blit(par_text, (self.screen_width//2 - par_text.get_width()//2, self.screen_height - 60))
    
    def run(self):
        """Run the level editor main loop"""
        clock = pygame.time.Clock()
        running = True
        
        while running:
            running = self.handle_events()
            self.draw()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    editor = LevelCreator()
    editor.run()