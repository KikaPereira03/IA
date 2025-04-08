import pygame
import time
import re
import sys
import os
from game.core import CakeGame, CakeSlice
from game.solver import greedy_bot_solver, astar_bot_solver, metrics
from game.models import CakeSlice
from game.metrics_collector import MetricsCollector

class CakeGameUI:
    def __init__(self, level_file="game/levels/level1.txt", width=4, height=5, max_capacity=6, bot_algorithm=None):
        pygame.init()
        self.bot_algorithm = bot_algorithm
        self.level_file = level_file
        match = re.search(r'level(\d+)', level_file)
        self.current_level_number = int(match.group(1)) if match else 1
        self.queue_slots = 3
        self.queue_pointer = self.queue_slots
        self.game = CakeGame(width, height)
        self.game.ui_level_switch = self.change_level
        self.load_level(level_file)
        self.game.ui_callback = self.animate_disappearing_plate

        self.screen_width = 1000
        self.screen_height = 800
        self.cell_size = 80
        self.cake_radius = 35
        self.layer_height = 12
        self.grid_padding = 10

        self.queue_height = 130
        self.queue_y_position = 600
        self.selected_queue_idx = None
        self.selected_plate = None

        self.bg_color = (230, 220, 240)
        self.grid_color = (180, 170, 230)
        self.grid_border_color = (150, 140, 200)
        self.plate_color = (250, 250, 250)
        self.selected_color = (255, 255, 0, 100)
        self.text_color = (80, 80, 100)

        # Hint button properties
        self.hint_button_rect = pygame.Rect(self.screen_width - 300, 650, 100, 40)
        self.hint_active = False
        self.hint_timer = 0
        self.hint_duration = 2000  
        self.hint_move = None

        self.color_map = {
            'R': (255, 80, 80), 'G': (100, 200, 100), 'B': (100, 150, 255),
            'Y': (255, 230, 100), 'P': (230, 100, 230), 'O': (255, 160, 80),
            'C': (100, 230, 230), 'M': (200, 100, 180)
        }

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cake Sort Puzzle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 36)

        if self.bot_algorithm:
            self.run_solver_with_algorithm(self.bot_algorithm)

    # -------------------------
    # Drawing & Layout Methods
    # -------------------------

    def get_cell_rect(self, plate_idx):
        grid_width = self.game.width
        grid_total_width = grid_width * self.cell_size + (grid_width - 1) * self.grid_padding
        grid_total_height = self.game.height * self.cell_size + (self.game.height - 1) * self.grid_padding
        grid_start_x = (self.screen_width - grid_total_width) // 2
        grid_start_y = (self.screen_height - self.queue_height - grid_total_height) // 2 + 30
        col = plate_idx % grid_width
        row = plate_idx // grid_width
        x = grid_start_x + col * (self.cell_size + self.grid_padding)
        y = grid_start_y + row * (self.cell_size + self.grid_padding)
        return pygame.Rect(x, y, self.cell_size, self.cell_size)

    def get_queue_slot_rect(self, slot_idx):
        slot_width = self.cell_size
        queue_total_width = self.queue_slots * slot_width + (self.queue_slots - 1) * self.grid_padding
        queue_start_x = (self.screen_width - queue_total_width) // 2
        x = queue_start_x + slot_idx * (slot_width + self.grid_padding)
        y = self.queue_y_position + (self.queue_height - slot_width) // 2
        return pygame.Rect(x, y, slot_width, slot_width)

    def draw_plate_with_slices(self, surface, center_x, center_y, slices):
        pygame.draw.ellipse(surface, (255, 250, 240), (center_x - 42, center_y + 36, 84, 18))
        total_height = len(slices) * (self.layer_height + 6)
        base_y = center_y + total_height // 2

        for i, layer in enumerate(slices):
            layer_y = base_y - i * (self.layer_height + 6)
            layer_width = self.cake_radius * 1.5
            layer_height = self.layer_height + 2
            color = self.color_map.get(layer.color, (220, 220, 220))
            shadow = tuple(max(0, c - 30) for c in color)
            highlight = tuple(min(255, c + 50) for c in color)

            pygame.draw.ellipse(surface, shadow, pygame.Rect(center_x - layer_width//2, layer_y + 2, layer_width, layer_height))
            main_rect = pygame.Rect(center_x - layer_width//2, layer_y, layer_width, layer_height)
            pygame.draw.ellipse(surface, color, main_rect)
            pygame.draw.ellipse(surface, highlight, main_rect.inflate(-layer_width * 0.4, -layer_height * 0.4).move(0, -1))
            pygame.draw.ellipse(surface, (80, 80, 80), main_rect, 1)

    def draw_score_bar(self):
        bar_width, bar_height = 220, 18
        bar_x = self.screen_width // 2 - bar_width // 2
        bar_y = 110
        required_score = getattr(self.game, 'required_score', 100)
        progress = min(self.game.score / required_score, 1.0)

        pygame.draw.rect(self.screen, (210, 210, 250), (bar_x, bar_y, bar_width, bar_height), border_radius=10)
        fill_width = int(bar_width * progress)
        fill_color = (140, 80, 255) if progress < 1.0 else (80, 200, 120)
        pygame.draw.rect(self.screen, fill_color, (bar_x, bar_y, fill_width, bar_height), border_radius=10)

        score_text = pygame.font.SysFont("Arial", 16).render(f"{self.game.score} / {required_score}", True, (70, 70, 70))
        self.screen.blit(score_text, (self.screen_width // 2 - score_text.get_width() // 2, bar_y - 26))

    def draw_hint_button(self):
        # Draw hint button
        button_color = (150, 200, 150) if self.hint_button_rect.collidepoint(pygame.mouse.get_pos()) else (120, 180, 120)
        pygame.draw.rect(self.screen, button_color, self.hint_button_rect, 0, 10)
        pygame.draw.rect(self.screen, (100, 160, 100), self.hint_button_rect, 2, 10)
        
        hint_text = self.font.render("Hint", True, (255, 255, 255))
        self.screen.blit(hint_text, (self.hint_button_rect.centerx - hint_text.get_width() // 2, 
                                     self.hint_button_rect.centery - hint_text.get_height() // 2))

    def draw_hint(self):
        if not self.hint_active or not self.hint_move:
            return

        # Highlight the queue item to move
        q_idx, g_idx = self.hint_move
        queue_rect = self.get_queue_slot_rect(q_idx)
        
        # Draw arrow from queue to destination
        grid_rect = self.get_cell_rect(g_idx)
        
        # Pulsating effect
        alpha = 128 + int(100 * abs(pygame.time.get_ticks() % 1000 - 500) / 500)
        
        # Highlight queue item
        highlight = pygame.Surface((queue_rect.width, queue_rect.height), pygame.SRCALPHA)
        highlight.fill((255, 255, 0, alpha))
        self.screen.blit(highlight, queue_rect.topleft)
        
        # Highlight target plate
        highlight2 = pygame.Surface((grid_rect.width, grid_rect.height), pygame.SRCALPHA)
        highlight2.fill((255, 255, 0, alpha))
        self.screen.blit(highlight2, grid_rect.topleft)
        
        # Draw arrow
        pygame.draw.line(self.screen, (255, 255, 0), 
                          (queue_rect.centerx, queue_rect.centery),
                          (grid_rect.centerx, grid_rect.centery), 3)
        
        # Draw arrowhead
        angle = pygame.math.Vector2(grid_rect.centerx - queue_rect.centerx, 
                                   grid_rect.centery - queue_rect.centery).normalize()
        pos = (grid_rect.centerx - angle.x * 20, grid_rect.centery - angle.y * 20)
        
        # Arrow points
        p1 = (pos[0] + angle.y * 10, pos[1] - angle.x * 10)
        p2 = (pos[0] - angle.y * 10, pos[1] + angle.x * 10)
        
        pygame.draw.polygon(self.screen, (255, 255, 0), [pos, p1, p2])

    def draw(self):
        self.screen.fill(self.bg_color)
        for idx, plate in enumerate(self.game.plates):
            rect = self.get_cell_rect(idx)
            pygame.draw.rect(self.screen, self.grid_color, rect, 0, 15)
            pygame.draw.rect(self.screen, self.grid_border_color, rect, 2, 15)
            self.draw_plate_with_slices(self.screen, *rect.center, plate.slices)

        for idx, plate in enumerate(self.queue_plates):
            slot_rect = self.get_queue_slot_rect(idx)
            pygame.draw.rect(self.screen, self.grid_color, slot_rect, 0, 15)
            pygame.draw.rect(self.screen, self.grid_border_color, slot_rect, 2, 15)

            if idx == self.selected_queue_idx:
                highlight = pygame.Surface((slot_rect.width, slot_rect.height), pygame.SRCALPHA)
                highlight.fill(self.selected_color)
                self.screen.blit(highlight, slot_rect.topleft)

            if plate:
                self.draw_plate_with_slices(self.screen, *slot_rect.center, plate)

        title = self.big_font.render("Cake Sort Puzzle", True, self.text_color)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 40))
        self.draw_score_bar()
        self.draw_hint_button()

        if self.hint_active:
            self.draw_hint()

        pygame.display.flip()

    # -------------------------
    # Game State & Logic
    # -------------------------

    def load_level(self, level_file):
        self.game.initialize_level(level_file)
        self.queue_plates = [
            [CakeSlice(color, 1) for color in reversed(plate)]
            for plate in self.game.queue_data[:self.queue_slots]
        ]
        self.selected_queue_idx = None
        self.selected_plate = None

    def check_level_completion(self):
        score_met = self.game.score >= self.game.required_score
        goal_met = self.game.is_goal_state()
        if score_met:
            next_level = self.current_level_number + 1
            self.change_level(next_level)
            if not os.path.exists(f"game/levels/level{next_level}.txt"):
                return True
        return False

    def handle_click(self, pos):
        if self.hint_button_rect.collidepoint(pos):  
            self.show_hint()
            return
    
        for idx, plate in enumerate(self.queue_plates):
            if self.get_queue_slot_rect(idx).collidepoint(pos) and plate:
                self.selected_queue_idx = idx
                return

        if self.selected_queue_idx is not None:
            queue_idx = self.selected_queue_idx
            selected_plate = self.queue_plates[queue_idx]
            empty_plates = any(len(p.slices) == 0 for p in self.game.plates)
            if not empty_plates:
                self.show_game_over_popup()
                return

            for idx, board_plate in enumerate(self.game.plates):
                if self.get_cell_rect(idx).collidepoint(pos) and len(board_plate.slices) == 0:
                    board_plate.slices.extend(list(selected_plate))
                    self.game.score += 10
                    self.game.merge_all_possible_slices()
                    self.check_level_completion()
                    if self.queue_pointer < len(self.game.queue_data):
                        next_plate = self.game.queue_data[self.queue_pointer]
                        self.queue_plates[queue_idx] = [CakeSlice(c, 1) for c in reversed(next_plate)]
                        self.queue_pointer += 1
                    else:
                        self.queue_plates[queue_idx] = None
                    self.selected_queue_idx = None
                    return
            self.selected_queue_idx = None
            return

        for idx, plate in enumerate(self.game.plates):
            if self.get_cell_rect(idx).collidepoint(pos) and plate.slices:
                self.selected_plate = idx
                return


    # -------------------------
    # Hint Feature
    # -------------------------
    
    def show_hint(self):
        """Generate and display a hint using the game's enhanced greedy_bot_solver"""
        # Prepare the queue data in the format expected by greedy_bot_solver
        queue_data = []
        for idx, plate in enumerate(self.queue_plates):
            if plate:
                cake_colors = [slice.color for slice in plate]
                queue_data.append((idx, cake_colors))
        
        if not queue_data:
            print("No hint available - queue is empty")
            return
        
        # Get hint from the enhanced greedy solver, passing game instance for context
        hint_moves = greedy_bot_solver(self.game.plates, queue_data, game_instance=self.game)
        
        if hint_moves and hint_moves[0] != (-1, -1):
            # Store the hint move
            self.hint_move = hint_moves[0]
            self.hint_active = True
            self.hint_timer = pygame.time.get_ticks()
            print(f"Hint: Move queue {self.hint_move[0]} to grid {self.hint_move[1]}")
        else:
            print("No hint available")
        
    def update_hint_state(self):
        """Update the hint state based on the timer"""
        if self.hint_active:
            current_time = pygame.time.get_ticks()
            if current_time - self.hint_timer > self.hint_duration:
                self.hint_active = False


    # -------------------------
    # Popups
    # -------------------------

    def show_game_over_popup(self):
        popup_running = True
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect(
            (self.screen_width - 400) // 2,
            (self.screen_height - 200) // 2,
            400,
            200
        )

        pygame.draw.rect(self.screen, (245, 245, 255), box_rect, border_radius=25)
        pygame.draw.rect(self.screen, (180, 180, 220), box_rect, 4, border_radius=25)

        title_font = pygame.font.SysFont("Arial", 40, bold=True)
        title = title_font.render("GAME OVER", True, (200, 60, 60))
        subtitle = self.font.render("No empty plates left on the grid!", True, (100, 100, 120))
        score_text = self.font.render(f"Final Score: {self.game.score}", True, (100, 100, 120))
        button_text = self.font.render("EXIT", True, (255, 255, 255))

        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, box_rect.top + 30))
        self.screen.blit(subtitle, (self.screen_width//2 - subtitle.get_width()//2, box_rect.top + 90))
        self.screen.blit(score_text, (self.screen_width//2 - score_text.get_width()//2, box_rect.top + 120))

        button_rect = pygame.Rect(self.screen_width//2 - 80, box_rect.bottom - 50, 160, 36)
        pygame.draw.rect(self.screen, (120, 220, 120), button_rect, border_radius=18)
        self.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, button_rect.centery - button_text.get_height()//2))

        pygame.display.flip()

        while popup_running:
            for event in pygame.event.get():
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    return True
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    def show_level_popup(self, level_number):
        popup_running = True
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect(
            (self.screen_width - 380) // 2,
            (self.screen_height - 180) // 2,
            380,
            180
        )

        pygame.draw.rect(self.screen, (245, 245, 255), box_rect, border_radius=25)
        pygame.draw.rect(self.screen, (180, 180, 220), box_rect, 4, border_radius=25)

        title_font = pygame.font.SysFont("Arial", 48, bold=True)
        title = title_font.render(f"LEVEL {level_number}", True, (80, 60, 150))
        subtitle = self.font.render("LEVEL COMPLETE!", True, (100, 100, 120))
        button_text = self.font.render("NEXT", True, (255, 255, 255))

        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, box_rect.top + 20))
        self.screen.blit(subtitle, (self.screen_width//2 - subtitle.get_width()//2, box_rect.top + 78))

        button_rect = pygame.Rect(self.screen_width//2 - 80, box_rect.bottom - 50, 160, 36)
        pygame.draw.rect(self.screen, (120, 220, 120), button_rect, border_radius=18)
        self.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, button_rect.centery - button_text.get_height()//2))

        pygame.display.flip()

        while popup_running:
            for event in pygame.event.get():
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    return
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    def show_game_completed_popup(self):
        popup_running = True
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect(
            (self.screen_width - 400) // 2,
            (self.screen_height - 200) // 2,
            400,
            200
        )

        pygame.draw.rect(self.screen, (245, 245, 255), box_rect, border_radius=25)
        pygame.draw.rect(self.screen, (180, 180, 220), box_rect, 4, border_radius=25)

        title_font = pygame.font.SysFont("Arial", 40, bold=True)
        title = title_font.render("CONGRATULATIONS!", True, (80, 60, 150))
        subtitle = self.font.render("All levels have been passed!", True, (100, 100, 120))
        button_text = self.font.render("MENU", True, (255, 255, 255))

        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, box_rect.top + 30))
        self.screen.blit(subtitle, (self.screen_width//2 - subtitle.get_width()//2, box_rect.top + 90))

        button_rect = pygame.Rect(self.screen_width//2 - 80, box_rect.bottom - 50, 160, 36)
        pygame.draw.rect(self.screen, (120, 220, 120), button_rect, border_radius=18)
        self.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, button_rect.centery - button_text.get_height()//2))

        pygame.display.flip()

        while popup_running:
            for event in pygame.event.get():
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    return True
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    # -------------------------
    # Level Transitions
    # -------------------------

    def change_level(self, level_number):
        self.level_file = f"game/levels/level{level_number}.txt"
        print(f"Loading level: {self.level_file}")

        if not os.path.exists(self.level_file):
            print("Level file not found.")
            if level_number > 1:
                self.show_game_completed_popup()
            return

        self.current_level_number = level_number
        self.show_level_popup(level_number)

        self.game = CakeGame(self.game.width, self.game.height)
        self.game.ui_callback = self.animate_disappearing_plate
        self.game.ui_level_switch = self.change_level
        self.game.initialize_level(self.level_file)

        self.selected_queue_idx = None
        self.selected_plate = None
        self.queue_pointer = self.queue_slots

        self.queue_plates = [
            [CakeSlice(color, 1) for color in reversed(plate)]
            for plate in self.game.queue_data[:self.queue_slots]
        ]

        print(f"Level {level_number} ready.")

    # -------------------------
    # Utility
    # -------------------------

    def animate_disappearing_plate(self, plate_idx):
        rect = self.get_cell_rect(plate_idx)
        center_x, center_y = rect.center
        original_slices = self.game.plates[plate_idx].slices[:]

        for scale in reversed(range(1, 11)):
            self.draw()
            scaled_slices = [CakeSlice(layer.color, layer.size) for layer in original_slices]
            shrink_radius = int(self.cake_radius * (scale / 10))
            shrink_layer_height = int(self.layer_height * (scale / 10))

            pygame.draw.circle(self.screen, self.plate_color, (center_x, center_y), shrink_radius)

            total_height = len(scaled_slices) * (shrink_layer_height + 2) - 2
            base_y = center_y + total_height // 2 - shrink_layer_height // 2

            for i, layer in enumerate(scaled_slices):
                layer_y = base_y - i * (shrink_layer_height + 2)
                layer_rect = pygame.Rect(
                    center_x - shrink_radius * 0.75,
                    layer_y - shrink_layer_height // 2,
                    shrink_radius * 1.5,
                    shrink_layer_height
                )
                color = self.color_map.get(layer.color, (200, 200, 200))
                pygame.draw.ellipse(self.screen, color, layer_rect)

            pygame.display.update()
            pygame.time.delay(30)

    def get_grid_state(self):
        grid_state = []
        for row in range(self.game.height):
            row_data = []
            for col in range(self.game.width):
                idx = row * self.game.width + col
                plate = self.game.plates[idx]
                if plate.slices:
                    row_data.append([slice.color for slice in plate.slices])
                else:
                    row_data.append(None)
            grid_state.append(row_data)
        return grid_state

    def get_queue_state(self):
        return [list(plate) for plate in self.game.queue_data]



    # -------------------------
    # Bot / Solver Functions
    # -------------------------

    def run_solver(self):
        print("Bot running (greedy)...")

        while self.game.queue_data:
            queue = self.game.queue_data[:3]
            grid = self.game.plates

            moves = greedy_bot_solver(grid, queue, apply_moves=True)
            if not moves:
                print("No valid moves.")
                break

            q_index, g_index = moves[0]
            plate = self.game.queue_data.pop(q_index)
            grid[g_index].slices.extend([CakeSlice(color, 1) for color in plate])

            self.game._check_plate_completion(g_index)
            self.game.merge_all_possible_slices()

            pygame.time.delay(300)
            self.draw()

        print("Bot finished.")

    def run_solver_with_algorithm(self, algorithm):
        """
        Run the selected solver algorithm with performance tracking
        """
        from game.metrics_collector import MetricsCollector
        from game.solver import metrics, greedy_bot_solver, astar_bot_solver
        import os
        import time
        import re

        solver_map = {
            'greedy': greedy_bot_solver,
            'a*': astar_bot_solver,
        }

        solver = solver_map.get(algorithm.lower())
        if not solver:
            print(f"Unknown solver: {algorithm}")
            return

        # Extract level name from level file path
        match = re.search(r'level(\d+)', self.level_file)
        current_level_name = f"level{match.group(1)}" if match else os.path.basename(self.level_file)
        current_level = self.current_level_number

        print(f"Bot running ({algorithm})...")
        
        # Start fresh metrics tracking
        metrics.reset()
        metrics.start_tracking(current_level_name, algorithm)
        
        # Track steps for this specific run
        steps_taken = 0
        
        # Run the solver for the current level
        while self.game.queue_data:
            # Check if level has changed (this indicates previous level was completed)
            if current_level != self.current_level_number:
                # Save metrics for the completed level
                print(f"\nLevel {current_level_name} completed.")
                metrics.stop_tracking(self.game.score)
                metrics.steps_taken = steps_taken
                metrics.print_summary()
                
                # Set up for the new level
                current_level = self.current_level_number
                current_level_name = f"level{current_level}"
                print(f"\nStarting level {current_level_name}...")
                
                # Reset metrics for new level
                metrics.reset()
                metrics.start_tracking(current_level_name, algorithm)
                steps_taken = 0
            
            # Run one step of the solver
            queue = list(enumerate(self.game.queue_data[:3]))
            moves = solver(self.game.plates, queue, apply_moves=True, game_instance=self.game)

            if not moves:
                print("No valid moves.")
                break

            q_index, g_index = moves[0]
            if q_index == -1:  # Invalid move
                print("Invalid move returned by solver.")
                break
                
            # Track this step
            steps_taken += 1
            
            # Apply the move
            plate = self.game.queue_data.pop(q_index)
            self.queue_plates = [
                [CakeSlice(color, 1) for color in reversed(p)]
                for p in self.game.queue_data[:self.queue_slots]
            ]

            print(f"Move: placed queue {q_index} → grid {g_index}")
            self.game.plates[g_index].slices.extend([CakeSlice(color, 1) for color in plate])
            self.game._check_plate_completion(g_index)
            self.game.merge_all_possible_slices()

            # Check if level is completed
            level_completed = self.check_level_completion()
            
            # If level is completed but we're still in the same level (didn't change to next)
            # this means we're on the last level or no more levels available
            if level_completed and current_level == self.current_level_number:
                print(f"\nFinal level {current_level_name} completed.")
                metrics.stop_tracking(self.game.score)
                metrics.steps_taken = steps_taken
                metrics.print_summary()
                break

            # Delay for visualization
            pygame.time.delay(800)
            self.draw()
        
        # Make sure to save metrics for the current level if we exit the loop without completion
        if metrics.start_time is not None:
            print(f"\nLevel {current_level_name} finished.")
            metrics.stop_tracking(self.game.score)
            metrics.steps_taken = steps_taken
            metrics.print_summary()
        
        print("Bot finished.")


    # Run the game loop
    def run(self):
        running = True
        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_s:
                            if self.bot_algorithm:
                                self.run_solver_with_algorithm(self.bot_algorithm)

                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        result = self.handle_click(event.pos)
                        if result == True:
                            running = False

                self.update_hint_state()
                self.draw()
                self.clock.tick(60)
        except KeyboardInterrupt:
            print("\nGame closed by user.")
        finally:
            pygame.quit()
            return

if __name__ == "__main__":
    game_ui = CakeGameUI()
    game_ui.run()
