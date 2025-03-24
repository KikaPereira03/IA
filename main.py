import pygame
import sys
import time
from game.core import CakeGame, CakeLayer
from game.solver import GameSolver
from game.utils import load_image, draw_text, create_gradient

class CakeGameUI:
    def __init__(self, width: int = 5, height: int = 4):
        pygame.init()
        self.game = CakeGame(width, height)
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
        
        # Initialize display
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cake Sort Puzzle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 36)
        
        # Game state
        self.selected_tube = None
        self.selected_layer_pos = None
        self.solving = False
        self.solution_moves = []
        self.last_move_time = 0
        
        # Load initial level
        self.load_level("game/levels/level1.txt")
    
    def load_level(self, filename: str):
        """Load a level from file"""
        self.game.initialize_level(filename)
        self.selected_tube = None
        self.selected_layer_pos = None
        self.solving = False
        self.solution_moves = []
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.MOUSEBUTTONDOWN and not self.solving:
                if event.button == 1:  # Left click
                    self.handle_click(pygame.mouse.get_pos())
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  # Reset level
                    self.load_level("game/levels/level1.txt")
                elif event.key == pygame.K_s:  # Solve with A*
                    self.start_solving('advanced')
                elif event.key == pygame.K_b:  # Solve with BFS
                    self.start_solving('bfs')
                elif event.key == pygame.K_1:  # Load level 1
                    self.load_level("game/levels/level1.txt")
                elif event.key == pygame.K_2:  # Load level 2
                    self.load_level("game/levels/level2.txt")
                elif event.key == pygame.K_3:  # Load level 3
                    self.load_level("game/levels/level3.txt")
                elif event.key == pygame.K_h:  # Hint
                    self.get_hint()
        
        # Auto-play solution if solving
        if self.solving and self.solution_moves and time.time() - self.last_move_time > 0.5:
            from_idx, layer_pos, to_idx = self.solution_moves.pop(0)
            self.game.move_layer(from_idx, layer_pos, to_idx)
            self.last_move_time = time.time()
            if not self.solution_moves:
                self.solving = False
        
        return True
    
    def get_hint(self):
        """Show the next best move"""
        if not self.solution_moves:
            self.start_solving('advanced')
        if self.solution_moves:
            from_idx, layer_pos, to_idx = self.solution_moves[0]
            print(f"Hint: Move from tube {from_idx} (layer {layer_pos}) to tube {to_idx}")
    
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
        """Handle mouse clicks on tubes"""
        for tube_idx, tube in enumerate(self.game.tubes):
            tube_rect = self.get_tube_rect(tube_idx)
            if tube_rect.collidepoint(mouse_pos):
                if self.selected_tube is None:
                    # Select a tube and layer
                    self.selected_tube = tube_idx
                    # Find which layer was clicked
                    rel_y = mouse_pos[1] - tube_rect.y
                    self.selected_layer_pos = min(
                        len(tube.layers) - 1 - (rel_y // self.layer_height),
                        len(tube.layers) - 1
                    )
                else:
                    # Try to move the selected layer
                    if tube_idx in self.game.get_adjacent_tubes(self.selected_tube):
                        if self.game.move_layer(self.selected_tube, self.selected_layer_pos, tube_idx):
                            if self.game.is_solved():
                                self.show_win_message()
                    self.selected_tube = None
                    self.selected_layer_pos = None
    
    def show_win_message(self):
        """Display win message"""
        win_text = self.big_font.render("Level Complete!", True, (0, 200, 0))
        self.screen.blit(win_text, 
                        (self.screen_width//2 - win_text.get_width()//2, 
                         self.screen_height//2 - win_text.get_height()//2))
        pygame.display.flip()
        pygame.time.delay(2000)
    
    def get_tube_rect(self, tube_idx: int) -> pygame.Rect:
        """Calculate tube position in grid"""
        col = tube_idx % self.game.width
        row = tube_idx // self.game.width
        
        x = self.margin + col * (self.tube_width + 20)
        y = self.margin + row * (self.tube_height + 20)
        
        return pygame.Rect(x, y, self.tube_width, self.tube_height)
    
    def draw(self):
        """Draw the game state"""
        self.screen.fill(self.bg_color)
        
        # Draw title and moves
        title = self.big_font.render("Cake Sort Puzzle", True, self.text_color)
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, 10))
        
        moves_text = self.font.render(f"Moves: {self.game.moves}", True, self.text_color)
        self.screen.blit(moves_text, (20, 20))
        
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
                
                # Draw layer with color from color_map
                color = self.color_map.get(layer.color, (200, 200, 200))
                pygame.draw.rect(self.screen, color, layer_rect, 0, 5)
                pygame.draw.rect(self.screen, (0, 0, 0), layer_rect, 1, 5)
                
                # Draw layer size
                size_text = self.font.render(str(layer.size), True, (0, 0, 0))
                self.screen.blit(size_text, 
                               (layer_rect.centerx - size_text.get_width()//2,
                                layer_rect.centery - size_text.get_height()//2))
        
        # Draw controls help
        controls = [
            "Controls:",
            "1/2/3 - Load levels",
            "R - Reset level",
            "S - Solve with A*",
            "B - Solve with BFS",
            "H - Get hint",
            "Click - Select/move layers"
        ]
        
        for i, text in enumerate(controls):
            y_pos = self.screen_height - 150 + i * 25
            draw_text(self.screen, text, (20, y_pos), self.font, self.text_color)
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        running = True
        while running:
            running = self.handle_events()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game_ui = CakeGameUI()
    game_ui.run()