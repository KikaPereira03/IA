import pygame
import sys
import time
from game.core import CakeGame, CakeLayer
from game.solver import GameSolver
from game.utils import load_image, draw_text, create_gradient

class CakeGameUI:
    def __init__(self, width: int = 4, height: int = 5):
        pygame.init()
        self.game = CakeGame(width, height)
        self.solver = GameSolver(self.game)
        
        # UI Settings
        self.screen_width = 1000
        self.screen_height = 800
        self.cell_size = 80  # Smaller cell size
        self.cake_radius = 35  # Smaller cake radius
        self.layer_height = 12  # Slightly smaller layer height
        self.margin = 80
        self.grid_padding = 10  # Reduced padding between cells
        
        # Plate queue settings - moved higher up
        self.queue_height = 130  # Height of the plate queue area
        self.queue_y_position = 600  # Fixed position higher up
        self.queue_slots = 3  # Reduced to 3 queue slots
        self.queue_plates = [[] for _ in range(self.queue_slots)]  # Empty placeholders
        self.selected_queue_idx = None  # Selected queue plate index
        
        # Points system
        self.points = 0
        
        # Colors
        self.bg_color = (230, 220, 240)  # Lighter purple background
        self.grid_color = (180, 170, 230)  # Light purple for the grid
        self.grid_border_color = (150, 140, 200)  # Darker purple for borders
        self.plate_color = (250, 250, 250)  # White for the plate
        self.selected_color = (255, 255, 0, 100)  # Semi-transparent yellow highlight
        self.text_color = (80, 80, 100)  # Darker text
        
        # Cake colors - making them more vibrant and cake-like
        self.color_map = {
            'R': (255, 80, 80),    # Red
            'G': (100, 200, 100),  # Green
            'B': (100, 150, 255),  # Blue
            'Y': (255, 230, 100),  # Yellow
            'P': (230, 100, 230),  # Purple
            'O': (255, 160, 80),   # Orange
            'C': (100, 230, 230),  # Cyan
            'M': (200, 100, 180)   # Magenta
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
        # Use the game's existing level loading functionality
        self.game.initialize_level(filename)
        self.selected_tube = None
        self.selected_layer_pos = None
        self.selected_queue_idx = None
        self.solving = False
        self.solution_moves = []
        
        # Initialize empty queue placeholders
        self.queue_plates = [[] for _ in range(self.queue_slots)]
    
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
        """Handle mouse clicks on tubes and queue"""
        # First check if clicking on the main grid
        if mouse_pos[1] < self.queue_y_position:
            for tube_idx, tube in enumerate(self.game.tubes):
                cell_rect = self.get_cell_rect(tube_idx)
                if cell_rect.collidepoint(mouse_pos):
                    if self.selected_tube is None and self.selected_queue_idx is None:
                        # Select a tube and layer
                        self.selected_tube = tube_idx
                        # Find which layer was clicked based on distance from center
                        center_x, center_y = cell_rect.center
                        rel_y = mouse_pos[1] - center_y
                        # Adjust for cake position (layers are stacked upward from the center)
                        layers_total_height = len(tube.layers) * self.layer_height
                        cake_top_y = center_y - layers_total_height / 2
                        rel_layer_y = mouse_pos[1] - cake_top_y
                        self.selected_layer_pos = min(
                            max(0, int(rel_layer_y // self.layer_height)),
                            len(tube.layers) - 1
                        )
                    elif self.selected_queue_idx is not None:
                        # Try to place a plate from the queue onto the grid
                        if self.place_from_queue_to_grid(self.selected_queue_idx, tube_idx):
                            if self.game.is_solved():
                                self.show_win_message()
                        self.selected_queue_idx = None
                    else:
                        # Try to move the selected layer
                        if tube_idx in self.game.get_adjacent_tubes(self.selected_tube):
                            if self.game.move_layer(self.selected_tube, self.selected_layer_pos, tube_idx):
                                if self.game.is_solved():
                                    self.show_win_message()
                        self.selected_tube = None
                        self.selected_layer_pos = None
        # Check if clicking on the queue area
        else:
            for idx, _ in enumerate(self.queue_plates):
                slot_rect = self.get_queue_slot_rect(idx)
                if slot_rect.collidepoint(mouse_pos):
                    if self.selected_tube is None and self.selected_queue_idx is None:
                        # Select this queue slot if it has a plate
                        if self.queue_plates[idx]:
                            self.selected_queue_idx = idx
                    else:
                        # Deselect everything
                        self.selected_tube = None
                        self.selected_layer_pos = None
                        self.selected_queue_idx = None
    
    def show_win_message(self):
        """Display win message"""
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Semi-transparent overlay
        self.screen.blit(overlay, (0, 0))
        
        # Create a message box
        message_box = pygame.Rect(
            self.screen_width//2 - 200,
            self.screen_height//2 - 100,
            400, 200
        )
        pygame.draw.rect(self.screen, (255, 255, 255), message_box, 0, 20)
        pygame.draw.rect(self.screen, (100, 100, 100), message_box, 3, 20)
        
        win_text = self.big_font.render("Level Complete!", True, (0, 180, 0))
        self.screen.blit(win_text, 
                       (self.screen_width//2 - win_text.get_width()//2, 
                        self.screen_height//2 - 50))
        
        continue_text = self.font.render("Press any key to continue", True, (80, 80, 80))
        self.screen.blit(continue_text, 
                       (self.screen_width//2 - continue_text.get_width()//2, 
                        self.screen_height//2 + 20))
        
        pygame.display.flip()
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    waiting = False
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
    
    def get_cell_rect(self, tube_idx: int) -> pygame.Rect:
        """Calculate grid cell position"""
        # Calculate grid dimensions
        grid_width = self.game.width
        grid_height = self.game.height
        
        # Create a centered grid
        grid_total_width = grid_width * self.cell_size + (grid_width - 1) * self.grid_padding
        grid_total_height = grid_height * self.cell_size + (grid_height - 1) * self.grid_padding
        
        grid_start_x = (self.screen_width - grid_total_width) // 2
        # Position the grid higher to make room for the queue area
        grid_start_y = (self.screen_height - self.queue_height - grid_total_height) // 2
        
        # Calculate cell position
        col = tube_idx % grid_width
        row = tube_idx // grid_width
        
        x = grid_start_x + col * (self.cell_size + self.grid_padding)
        y = grid_start_y + row * (self.cell_size + self.grid_padding)
        
        return pygame.Rect(x, y, self.cell_size, self.cell_size)
    
    def get_queue_slot_rect(self, slot_idx: int) -> pygame.Rect:
        """Calculate position for a queue slot"""
        # Space the queue slots evenly
        slot_width = self.cell_size
        
        # Calculate total width of all slots with padding
        queue_total_width = self.queue_slots * slot_width + (self.queue_slots - 1) * self.grid_padding
        
        # Center the queue horizontally
        queue_start_x = (self.screen_width - queue_total_width) // 2
        
        # Calculate the position
        x = queue_start_x + slot_idx * (slot_width + self.grid_padding)
        y = self.queue_y_position + (self.queue_height - slot_width) // 2
        
        return pygame.Rect(x, y, slot_width, slot_width)
        
    def place_from_queue_to_grid(self, queue_idx: int, grid_idx: int) -> bool:
        """Place cake layers from queue onto the grid"""
        # In a real implementation, you'd need game logic to validate this move
        # For this example, we'll just make it work if there's something in the queue slot
        if not self.queue_plates[queue_idx]:
            return False
            
        # Get the target tube
        tube = self.game.tubes[grid_idx]
        
        # Check if the tube can accept the cake based on game rules
        # For simplicity, we'll just check if there's room
        if tube.is_full():
            return False
            
        # In a real game, you might need more complex logic here
        # For example, checking if the colors match existing layers
        
        # Add the layers to the tube using proper game mechanics
        for layer in self.queue_plates[queue_idx]:
            if not tube.add_layer(layer):
                # If adding fails, we need to revert any changes
                # For simplicity in this example, we'll just fail the whole operation
                return False
            
        # Remove the plate from the queue
        self.queue_plates[queue_idx] = []
        
        # Count this as a move
        self.game.moves += 1
        
        return True
    
    def draw_plate_with_layers(self, surface, center_x, center_y, layers):
        """Draw a plate with cake layers on top"""
        # Draw plate (white circle)
        pygame.draw.circle(surface, self.plate_color, (center_x, center_y), self.cake_radius)
        pygame.draw.circle(surface, (200, 200, 200), (center_x, center_y), self.cake_radius, 2)
        
        # Draw layers stacked upward from the plate
        total_layers = len(layers)
        if total_layers == 0:
            return
            
        # Start drawing from the bottom layer
        for i, layer in enumerate(layers):
            # Calculate vertical position (stacked upward)
            layer_y = center_y - (i * self.layer_height)
            
            # Create a smaller radius for the cake layer
            layer_radius = self.cake_radius * 0.85
            
            # Draw cake layer (colored circle)
            # Get color based on the layer.color attribute from CakeLayer class
            color = self.color_map.get(layer.color, (200, 200, 200))
            
            # Draw cake layer as a slightly flattened circle (oval)
            layer_rect = pygame.Rect(
                center_x - layer_radius,
                layer_y - self.layer_height // 2,
                layer_radius * 2,
                self.layer_height
            )
            pygame.draw.ellipse(surface, color, layer_rect)
            pygame.draw.ellipse(surface, (100, 100, 100), layer_rect, 1)
            
            # Draw layer size at the center of the layer
            size_text = self.font.render(str(layer.size), True, (0, 0, 0))
            text_x = center_x - size_text.get_width() // 2
            text_y = layer_y - size_text.get_height() // 2
            surface.blit(size_text, (text_x, text_y))
    
    def draw(self):
        """Draw the game state"""
        self.screen.fill(self.bg_color)
        
        # Draw grid background
        for tube_idx in range(len(self.game.tubes)):
            cell_rect = self.get_cell_rect(tube_idx)
            
            # Draw cell background with rounded corners
            pygame.draw.rect(self.screen, self.grid_color, cell_rect, 0, 15)
            pygame.draw.rect(self.screen, self.grid_border_color, cell_rect, 2, 15)
            
            # Highlight selected cell
            if tube_idx == self.selected_tube:
                highlight = pygame.Surface((cell_rect.width, cell_rect.height), pygame.SRCALPHA)
                highlight.fill(self.selected_color)
                self.screen.blit(highlight, cell_rect.topleft)
        
        # Draw cakes with layers in the grid
        for tube_idx, tube in enumerate(self.game.tubes):
            cell_rect = self.get_cell_rect(tube_idx)
            center_x, center_y = cell_rect.center
            
            # Draw the plate with cake layers
            self.draw_plate_with_layers(self.screen, center_x, center_y, tube.layers)
        
        # Draw the plate queue area background
        queue_area_rect = pygame.Rect(0, self.queue_y_position, self.screen_width, self.queue_height)
        pygame.draw.rect(self.screen, (220, 210, 230), queue_area_rect)  # Lighter color for the queue area
        pygame.draw.line(self.screen, (180, 170, 190), 
                       (0, self.queue_y_position), 
                       (self.screen_width, self.queue_y_position), 3)
        
        # Draw queue slots and plates (without the "Cake Queue" label)
        for idx in range(self.queue_slots):
            slot_rect = self.get_queue_slot_rect(idx)
            
            # Draw slot background
            pygame.draw.rect(self.screen, self.grid_color, slot_rect, 0, 15)
            pygame.draw.rect(self.screen, self.grid_border_color, slot_rect, 2, 15)
            
            # Highlight selected queue slot
            if idx == self.selected_queue_idx:
                highlight = pygame.Surface((slot_rect.width, slot_rect.height), pygame.SRCALPHA)
                highlight.fill(self.selected_color)
                self.screen.blit(highlight, slot_rect.topleft)
            
            # Draw plates in queue
            if idx < len(self.queue_plates) and self.queue_plates[idx]:
                center_x, center_y = slot_rect.center
                self.draw_plate_with_layers(self.screen, center_x, center_y, self.queue_plates[idx])
        
        # Draw title
        title = self.big_font.render("Cake Sort Puzzle", True, self.text_color)
        title_x = self.screen_width // 2 - title.get_width() // 2
        self.screen.blit(title, (title_x, 20))
        
        # Points display below the title with more space
        points_text = self.font.render(f"Points: {self.points}", True, (0, 150, 0))
        points_x = self.screen_width // 2 - points_text.get_width() // 2
        self.screen.blit(points_text, (points_x, 70))
        
        # Draw controls at the bottom of the plate queue area
        controls_text = self.font.render("1/2/3: Level   R: Reset   S: Solve   H: Hint", True, self.text_color)
        text_x = self.screen_width // 2 - controls_text.get_width() // 2
        self.screen.blit(controls_text, (text_x, self.screen_height - 30))
        
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