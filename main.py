import pygame
import re
import sys
import time
import os
from typing import List, Tuple, Optional
from game.core import Plate, CakeGame, CakeSlice
from game.solver import solve_game


class CakeGameUI:
    # Initialize the game UI
    def __init__(self, level_file="game/levels/level1.txt", width: int = 4, height: int = 5, max_capacity=6):
        pygame.init()
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
        self.queue_slots = 3
        self.selected_queue_idx = None
        self.selected_plate = None

        self.bg_color = (230, 220, 240)
        self.grid_color = (180, 170, 230)
        self.grid_border_color = (150, 140, 200)
        self.plate_color = (250, 250, 250)
        self.selected_color = (255, 255, 0, 100)
        self.text_color = (80, 80, 100)

        self.color_map = {
            'R': (255, 80, 80),
            'G': (100, 200, 100),
            'B': (100, 150, 255),
            'Y': (255, 230, 100),
            'P': (230, 100, 230),
            'O': (255, 160, 80),
            'C': (100, 230, 230),
            'M': (200, 100, 180)
        }

        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cake Sort Puzzle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 36)

    # Get plate position on grid
    def get_cell_rect(self, plate_idx: int) -> pygame.Rect:
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

    # Get plate position in queue
    def get_queue_slot_rect(self, slot_idx: int) -> pygame.Rect:
        slot_width = self.cell_size
        queue_total_width = self.queue_slots * slot_width + (self.queue_slots - 1) * self.grid_padding
        queue_start_x = (self.screen_width - queue_total_width) // 2
        x = queue_start_x + slot_idx * (slot_width + self.grid_padding)
        y = self.queue_y_position + (self.queue_height - slot_width) // 2
        return pygame.Rect(x, y, slot_width, slot_width)

    # Draw a single plate and its slices
    def draw_plate_with_slices(self, surface, center_x, center_y, slices):
        pygame.draw.ellipse(surface, (255, 250, 240), (center_x - 42, center_y + 36, 84, 18))
        num_slices = len(slices)
        total_height = num_slices * (self.layer_height + 6)
        base_y = center_y + total_height // 2

        for i, layer in enumerate(slices):
            layer_y = base_y - i * (self.layer_height + 6)
            layer_width = self.cake_radius * 1.5
            layer_height = self.layer_height + 2
            color = self.color_map.get(layer.color, (220, 220, 220))
            shadow = tuple(max(0, c - 30) for c in color)
            highlight = tuple(min(255, c + 50) for c in color)

            shadow_rect = pygame.Rect(center_x - layer_width//2, layer_y + 2, layer_width, layer_height)
            pygame.draw.ellipse(surface, shadow, shadow_rect)

            main_rect = pygame.Rect(center_x - layer_width//2, layer_y, layer_width, layer_height)
            pygame.draw.ellipse(surface, color, main_rect)

            icing_rect = main_rect.inflate(-layer_width * 0.4, -layer_height * 0.4)
            icing_rect.move_ip(0, -1)
            pygame.draw.ellipse(surface, highlight, icing_rect)

            pygame.draw.ellipse(surface, (80, 80, 80), main_rect, 1)

    def draw_score_bar(self):
        bar_width, bar_height = 220, 18
        bar_x = self.screen_width // 2 - bar_width // 2
        bar_y = 110

        # Get required score with a safe default
        required_score = getattr(self.game, 'required_score', 100)
        
        progress = min(self.game.score / required_score, 1.0)

        # Background
        pygame.draw.rect(self.screen, (210, 210, 250), (bar_x, bar_y, bar_width, bar_height), border_radius=10)

        # Progress fill
        fill_width = int(bar_width * progress)
        fill_color = (140, 80, 255) if progress < 1.0 else (80, 200, 120)
        pygame.draw.rect(self.screen, fill_color, (bar_x, bar_y, fill_width, bar_height), border_radius=10)

        # Text above the bar
        self.score_font = pygame.font.SysFont("Arial", 16)
        score_text = self.score_font.render(f"{self.game.score} / {required_score}", True, (70, 70, 70))
        self.screen.blit(score_text, (self.screen_width // 2 - score_text.get_width() // 2, bar_y - 26))


    # Draw the entire screen
    def draw(self):
        self.screen.fill(self.bg_color)
        for idx, plate in enumerate(self.game.plates):
            rect = self.get_cell_rect(idx)
            pygame.draw.rect(self.screen, self.grid_color, rect, 0, 15)
            pygame.draw.rect(self.screen, self.grid_border_color, rect, 2, 15)
            center_x, center_y = rect.center
            self.draw_plate_with_slices(self.screen, center_x, center_y, plate.slices)

        for idx, plate in enumerate(self.queue_plates):
            slot_rect = self.get_queue_slot_rect(idx)
            pygame.draw.rect(self.screen, self.grid_color, slot_rect, 0, 15)
            pygame.draw.rect(self.screen, self.grid_border_color, slot_rect, 2, 15)

            if idx == self.selected_queue_idx:
                highlight = pygame.Surface((slot_rect.width, slot_rect.height), pygame.SRCALPHA)
                highlight.fill(self.selected_color)
                self.screen.blit(highlight, slot_rect.topleft)

            if plate:
                cx, cy = slot_rect.center
                self.draw_plate_with_slices(self.screen, cx, cy, plate)

        title = self.big_font.render("Cake Sort Puzzle", True, self.text_color)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 40))
        self.draw_score_bar()

        pygame.display.flip()

    # Load level and reset game state
    def load_level(self, level_file: str):
        self.game.initialize_level(level_file)

        self.queue_plates = [
            [CakeSlice(color, 1) for color in reversed(plate)]
            for plate in self.game.queue_data[:self.queue_slots]
        ]

        self.selected_queue_idx = None
        self.selected_plate = None

    # Check if level is complete based on score
    def check_level_completion(self):
        print(f"Checking level completion: Goal state: {self.game.is_goal_state()}, Score: {self.game.score}, Required Score: {self.game.required_score}")
        
        # Check if we have enough score
        score_met = self.game.score >= self.game.required_score
        
        # Check if all plates are properly sorted (no mixed colors)
        goal_met = self.game.is_goal_state()
        
        if score_met and not goal_met:
            for idx, plate in enumerate(self.game.plates):
                if plate.slices:
                    first_color = plate.slices[0].color
                    is_uniform = all(s.color == first_color for s in plate.slices)
        
        if score_met:
            print(f"Level {self.current_level_number} completed. Transitioning to next level.")
            next_level = self.current_level_number + 1
            self.change_level(next_level)


    # Show popup when game is over 
    def show_game_over_popup(self):
        popup_running = True
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        box_width = 400
        box_height = 200
        box_rect = pygame.Rect(
            (self.screen_width - box_width) // 2,
            (self.screen_height - box_height) // 2,
            box_width,
            box_height
        )

        pygame.draw.rect(self.screen, (245, 245, 255), box_rect, border_radius=25)
        pygame.draw.rect(self.screen, (180, 180, 220), box_rect, 4, border_radius=25)
        
        # Title
        title_font = pygame.font.SysFont("Arial", 40, bold=True)
        title = title_font.render("GAME OVER", True, (200, 60, 60))
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, box_rect.top + 30))

        # Subtitle
        subtitle = self.font.render("No empty plates left on the grid!", True, (100, 100, 120))
        self.screen.blit(subtitle, (self.screen_width//2 - subtitle.get_width()//2, box_rect.top + 90))

        # Score
        score_text = self.font.render(f"Final Score: {self.game.score}", True, (100, 100, 120))
        self.screen.blit(score_text, (self.screen_width//2 - score_text.get_width()//2, box_rect.top + 120))

        # Button
        button_rect = pygame.Rect(self.screen_width//2 - 80, box_rect.bottom - 50, 160, 36)
        pygame.draw.rect(self.screen, (120, 220, 120), button_rect, border_radius=18)
        button_text = self.font.render("EXIT", True, (255, 255, 255)) 
        self.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, button_rect.centery - button_text.get_height()//2))

        pygame.display.flip()
        while popup_running:
            for event in pygame.event.get():
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    popup_running = False
                    return True  
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()


    # Handle mouse click events on plates and queue
    # Check for game over condition
    def handle_click(self, pos):
        # Step 1: Handle click on queue plates
        for idx, plate in enumerate(self.queue_plates):
            if self.get_queue_slot_rect(idx).collidepoint(pos):
                if plate:
                    self.selected_queue_idx = idx
                    return
                    
        # Step 2: If a queue plate is selected, handle click on board plate
        if self.selected_queue_idx is not None:
            queue_idx = self.selected_queue_idx
            selected_plate = self.queue_plates[queue_idx]

            if selected_plate is not None:
                # Check if there's any empty plate on the grid
                empty_plates = any(len(board_plate.slices) == 0 for board_plate in self.game.plates)
                
                if not empty_plates:
                    # No empty plates - show game over
                    self.show_game_over_popup()
                    return
                    
                # Continue with normal plate placement logic
                for idx, board_plate in enumerate(self.game.plates):
                    if self.get_cell_rect(idx).collidepoint(pos) and len(board_plate.slices) == 0:
                        selected_slices = list(selected_plate)
                        if selected_slices:
                            board_plate.slices.extend(selected_slices)
                            self.game.score += 10
                            self.game.merge_all_possible_slices()
                            self.check_level_completion()

                            if self.queue_pointer < len(self.game.queue_data):
                                next_plate = self.game.queue_data[self.queue_pointer]
                                self.queue_plates[queue_idx] = [
                                    CakeSlice(color, 1) for color in reversed(next_plate)
                                ]
                                self.queue_pointer += 1
                            else:
                                self.queue_plates[queue_idx] = None

                            self.selected_queue_idx = None
                            return

                # If clicked somewhere invalid, deselect queue plate
                self.selected_queue_idx = None
                return

            # Step 3: Select a plate on the grid (used later for other interactions)
            for idx, plate in enumerate(self.game.plates):
                if self.get_cell_rect(idx).collidepoint(pos) and plate.slices:
                    self.selected_plate = idx
                    return

    # Animate a plate shrinking visually
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


    # Switch to a different level
    def change_level(self, level_number: int):
        self.level_file = f"game/levels/level{level_number}.txt"
        print(f"Attempting to load level: {self.level_file}")
        
        if not os.path.exists(self.level_file):
            print(f"Level file {self.level_file} does not exist!")
            if level_number > 1: 
                self.show_game_completed_popup()
            return
        
        print(f"Loading level {level_number}...")
        
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
        
        print(f"Level {level_number} loaded successfully")


     # Show "Level complete" popup
    def show_level_popup(self, level_number):
        popup_running = True
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        box_width = 380
        box_height = 180
        box_rect = pygame.Rect(
            (self.screen_width - box_width) // 2,
            (self.screen_height - box_height) // 2,
            box_width,
            box_height
        )

        pygame.draw.rect(self.screen, (245, 245, 255), box_rect, border_radius=25)
        pygame.draw.rect(self.screen, (180, 180, 220), box_rect, 4, border_radius=25)
        title_font = pygame.font.SysFont("Arial", 48, bold=True)

        # Title
        title = title_font.render(f"LEVEL {level_number}", True, (80, 60, 150))
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, box_rect.top + 20))

        # Subtitle
        subtitle = self.font.render("LEVEL COMPLETE!", True, (100, 100, 120))
        self.screen.blit(subtitle, (self.screen_width//2 - subtitle.get_width()//2, box_rect.top + 78))

        # Button
        button_rect = pygame.Rect(self.screen_width//2 - 80, box_rect.bottom - 50, 160, 36)
        pygame.draw.rect(self.screen, (120, 220, 120), button_rect, border_radius=18)

        button_text = self.font.render("NEXT", True, (255, 255, 255))
        self.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, button_rect.centery - button_text.get_height()//2))

        pygame.display.flip()
        while popup_running:
            for event in pygame.event.get():
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    popup_running = False
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()


    # Show popup when all levels are completed
    def show_game_completed_popup(self):
        popup_running = True
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        box_width = 400
        box_height = 200
        box_rect = pygame.Rect(
            (self.screen_width - box_width) // 2,
            (self.screen_height - box_height) // 2,
            box_width,
            box_height
        )

        pygame.draw.rect(self.screen, (245, 245, 255), box_rect, border_radius=25)
        pygame.draw.rect(self.screen, (180, 180, 220), box_rect, 4, border_radius=25)
        
        # Title
        title_font = pygame.font.SysFont("Arial", 40, bold=True)
        title = title_font.render("CONGRATULATIONS!", True, (80, 60, 150))
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, box_rect.top + 30))

        # Subtitle
        subtitle = self.font.render("All levels have been passed!", True, (100, 100, 120))
        self.screen.blit(subtitle, (self.screen_width//2 - subtitle.get_width()//2, box_rect.top + 90))

        # Button
        button_rect = pygame.Rect(self.screen_width//2 - 80, box_rect.bottom - 50, 160, 36)
        pygame.draw.rect(self.screen, (120, 220, 120), button_rect, border_radius=18)
        button_text = self.font.render("MENU", True, (255, 255, 255))
        self.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, button_rect.centery - button_text.get_height()//2))

        pygame.display.flip()
        while popup_running:
            for event in pygame.event.get():
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    popup_running = False
                    # Return to menu by exiting the game loop
                    return True  # Signal to main game loop to exit
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()  

            # Dentro de CakeGameUI (main.py)
    def get_grid_state(self):
        # Converte os pratos da grid para listas simples de cores (ex: ["R", "R", "R"])
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
        # Converte os pratos da fila para listas simples de cores
        return [[slice.color for slice in plate] for plate in self.game.queue_data]

    def run_solver(self):
       

        grid = self.get_grid_state()
        queue = self.get_queue_state()

        solution = solve_game(grid, queue)

        if solution is None:
            print("❌ Não foi encontrada solução.")
            return

        print("✅ Solução encontrada. A aplicar...")

        # Limpa o tabuleiro atual
        for i in range(len(self.game.plates)):
            self.game.plates[i] = Plate()

        # Aplica todos os movimentos da solução
        for pos, plate in solution:
            r, c = pos
            idx = r * self.game.width + c

            novo_prato = Plate()
            for color in plate:
                novo_prato.slices.append(CakeSlice(color=color, size=1))  # cada fatia com tamanho 1

            self.game.plates[idx] = novo_prato

            # Se tiveres função para verificar desaparecimentos automáticos, chama aqui:
            if hasattr(self.game, "check_plate_disappearance"):
                self.game.check_plate_disappearance()

            # Atualiza o ecrã
            self.draw()
            pygame.display.flip()
            pygame.time.wait(300)  # tempo entre jogadas (ajusta se quiseres) 

    # Run the game loop
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        self.run_solver()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    result = self.handle_click(event.pos)
                    if result == True:  # If a popup returns True, exit to menu
                        running = False
            self.draw()
            self.clock.tick(60)
        pygame.quit()
        return 


if __name__ == "__main__":
    game_ui = CakeGameUI()
    game_ui.run()
