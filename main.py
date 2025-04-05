import pygame
import sys
import time
import random
import os
from typing import List, Tuple, Optional
from game.core import CakeGame, CakeSlice

class CakeGameUI:
    # Initialize the game UI
    def __init__(self, level_file="game/levels/level1.txt", width: int = 4, height: int = 5, max_capacity=6, player_name="Tropa"):
        pygame.init()
        self.level_file = level_file
        self.queue_slots = 3
        self.game = CakeGame(width, height)
        self.game.ui_level_switch = self.change_level
        self.load_level(level_file)
        self.game.ui_callback = self.animate_disappearing_plate
        self.player_name = player_name
        self.game.player_name = player_name

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
        grid_start_y = (self.screen_height - self.queue_height - grid_total_height) // 2
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
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 20))

        self.draw_scoreboard()
        pygame.display.flip()

    # Draw the scoreboard text
    def draw_scoreboard(self):
        font = pygame.font.SysFont("Arial", 32)
        title = font.render("SCOREBOARD", True, (50, 50, 50))
        self.screen.blit(title, (700, 100))
        score_text = font.render(f"Score: {self.game.score}", True, (255, 100, 100))
        self.screen.blit(score_text, (700, 150))

    # Load level and reset game state
    def load_level(self, level_file: str):
        self.game.initialize_level(level_file)

        self.queue_plates = [
            [CakeSlice(color, 1) for color in reversed(plate)]
            for plate in self.game.queue_data[:self.queue_slots]
        ]

        self.selected_queue_idx = None
        self.selected_plate = None

    # Handle all mouse click actions
    def handle_click(self, pos):
        for idx, plate in enumerate(self.queue_plates):
            if self.get_queue_slot_rect(idx).collidepoint(pos):
                if plate:
                    self.selected_queue_idx = idx
                    return

        if self.selected_queue_idx is not None:
            for idx, board_plate in enumerate(self.game.plates):
                if self.get_cell_rect(idx).collidepoint(pos) and not board_plate.is_full() and board_plate.is_empty():
                    selected_slices = self.queue_plates[self.selected_queue_idx]
                    if selected_slices:
                        board_plate.slices.extend(selected_slices)
                        self.queue_plates[self.selected_queue_idx] = None
                        try:
                            self.game.merge_all_possible_slices()
                        except Exception:
                            import traceback
                            traceback.print_exc()
                            return
                        self.selected_queue_idx = None
                        return

        if self.selected_plate is not None:
            for idx, plate in enumerate(self.game.plates):
                if self.get_cell_rect(idx).collidepoint(pos) and idx != self.selected_plate:
                    self.game.move_all_slices(self.selected_plate, idx)
                    try:
                        self.game.merge_all_possible_slices()
                    except Exception:
                        import traceback
                        traceback.print_exc()
                        return
                    self.draw()
                    pygame.display.update()
                    self.selected_plate = None
                    return
            self.selected_plate = None

        else:
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

    # Switch levels and reload the board
    def change_level(self, level_number: int):
        self.level_file = f"game/levels/level{level_number}.txt"
        if not os.path.exists(self.level_file):
            return
        current_score = self.game.score
        self.show_level_popup(level_number)
        self.game = CakeGame(self.game.width, self.game.height)
        self.game.score = current_score
        self.game.base_score = current_score
        self.game.player_name = self.player_name
        self.game.ui_callback = self.animate_disappearing_plate
        self.game.ui_level_switch = self.change_level
        self.game.initialize_level(self.level_file)
        self.selected_queue_idx = None
        self.selected_plate = None

    # Show popup UI when a level is complete
    def show_level_popup(self, level_number):
        popup_running = True
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        box_rect = pygame.Rect((self.screen_width - 500) // 2, (self.screen_height - 300) // 2, 500, 300)
        pygame.draw.rect(self.screen, (245, 245, 255), box_rect, border_radius=25)
        pygame.draw.rect(self.screen, (180, 180, 220), box_rect, 4, border_radius=25)
        title_font = pygame.font.SysFont("Arial", 48, bold=True)
        title = title_font.render(f"NÍVEL {level_number}", True, (80, 60, 150))
        self.screen.blit(title, (self.screen_width//2 - title.get_width()//2, box_rect.top + 30))
        subtitle = self.font.render("LEVEL COMPLETE!", True, (100, 100, 120))
        self.screen.blit(subtitle, (self.screen_width//2 - subtitle.get_width()//2, box_rect.top + 90))
        instruction = self.font.render("Clique ou prima qualquer tecla para continuar", True, (120, 120, 140))
        self.screen.blit(instruction, (self.screen_width//2 - instruction.get_width()//2, box_rect.top + 130))
        button_rect = pygame.Rect(self.screen_width//2 - 100, box_rect.bottom - 70, 200, 40)
        pygame.draw.rect(self.screen, (120, 220, 120), button_rect, border_radius=20)
        button_text = self.font.render("NEXT LEVEL", True, (255, 255, 255))
        self.screen.blit(button_text, (button_rect.centerx - button_text.get_width()//2, button_rect.centery - button_text.get_height()//2))
        pygame.display.flip()
        while popup_running:
            for event in pygame.event.get():
                if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    popup_running = False
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    # Run the game loop
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)
            self.draw()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game_ui = CakeGameUI()
    game_ui.run()
