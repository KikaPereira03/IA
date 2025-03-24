import pygame
import sys
import time
from game.core import CakeGame, CakeLayer
from game.solver import GameSolver
from game.utils import load_image, draw_text, create_gradient

class CakeGameUI:
    def __init__(self, width: int = 5, height: int = 5):
        pygame.init()
        self.game = CakeGame(width, height)
        self.solver = GameSolver(self.game)
        
        # UI Settings
        self.screen_width = 800
        self.screen_height = 600
        self.tube_width = 80
        self.tube_height = 200
        self.layer_height = 30
        self.margin = 50
        
        # Colors
        self.bg_color = (240, 240, 250)
        self.tube_color = (200, 200, 210)
        self.selected_color = (255, 255, 0)
        self.text_color = (50, 50, 50)
        
        # Initialize display
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cake Sort Puzzle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        
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
        
        # Auto-play solution if solving
        if self.solving and self.solution_moves and time.time() - self.last_move_time > 0.5:
            from_idx, layer_pos, to_idx = self.solution_moves.pop(0)
            self.game.move_layer(from_idx, layer_pos, to_idx)
            self.last_move_time = time.time()
            if not self.solution_moves:
                self.solving = False
        
        return True
    
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
                else:
                    # Try to