import pygame
import sys
import time
import random

from typing import List, Tuple, Optional
from game.core import CakeGame, CakeLayer
from game.solver import GameSolver

class CakeGameUI:
    def __init__(self, level_file="game/levels/level1.txt", width: int = 4, height: int = 5, max_capacity = 6):
        pygame.init()
        self.level_file = level_file  # guarda o nome do nível atual
        self.queue_slots = 3
        self.game = CakeGame(width, height)
        self.load_level(level_file)
        self.solver = GameSolver(self.game)
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
        self.queue_plates = [self.generate_random_plate() for _ in range(self.queue_slots)]
        self.selected_queue_idx = None
        self.selected_tube = None

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

    def generate_random_plate(self) -> List[CakeLayer]:
        if "level1" in self.level_file:
            colors = ['R', 'G']
        elif "level2" in self.level_file:
            colors = ['R', 'G', 'B']
        elif "level3" in self.level_file:
            colors = ['R', 'G', 'B', 'Y']
        else:
            colors = ['R', 'G', 'B', 'Y', 'P', 'O', 'C', 'M']  # default todas

        return [CakeLayer(random.choice(colors), 1) for _ in range(random.randint(2, 4))]

    def get_cell_rect(self, tube_idx: int) -> pygame.Rect:
        grid_width = self.game.width
        grid_total_width = grid_width * self.cell_size + (grid_width - 1) * self.grid_padding
        grid_total_height = self.game.height * self.cell_size + (self.game.height - 1) * self.grid_padding
        grid_start_x = (self.screen_width - grid_total_width) // 2
        grid_start_y = (self.screen_height - self.queue_height - grid_total_height) // 2
        col = tube_idx % grid_width
        row = tube_idx // grid_width
        x = grid_start_x + col * (self.cell_size + self.grid_padding)
        y = grid_start_y + row * (self.cell_size + self.grid_padding)
        return pygame.Rect(x, y, self.cell_size, self.cell_size)

    def get_queue_slot_rect(self, slot_idx: int) -> pygame.Rect:
        slot_width = self.cell_size
        queue_total_width = self.queue_slots * slot_width + (self.queue_slots - 1) * self.grid_padding
        queue_start_x = (self.screen_width - queue_total_width) // 2
        x = queue_start_x + slot_idx * (slot_width + self.grid_padding)
        y = self.queue_y_position + (self.queue_height - slot_width) // 2
        return pygame.Rect(x, y, slot_width, slot_width)

    def draw_plate_with_layers(self, surface, center_x, center_y, layers):
    # Desenha o prato
        pygame.draw.ellipse(surface, (255, 250, 240), (center_x - 42, center_y + 36, 84, 18))  # prato suave

        num_layers = len(layers)
        total_height = num_layers * (self.layer_height + 6)
        base_y = center_y + total_height // 2

        for i, layer in enumerate(layers):
            layer_y = base_y - i * (self.layer_height + 6)
            layer_width = self.cake_radius * 1.5
            layer_height = self.layer_height + 2

            # Obter cor da camada
            color = self.color_map.get(layer.color, (220, 220, 220))
            shadow = tuple(max(0, c - 30) for c in color)
            highlight = tuple(min(255, c + 50) for c in color)

            # Base sombra (fundo da fatia)
            shadow_rect = pygame.Rect(center_x - layer_width//2, layer_y + 2, layer_width, layer_height)
            pygame.draw.ellipse(surface, shadow, shadow_rect)

            # Fatia principal
            main_rect = pygame.Rect(center_x - layer_width//2, layer_y, layer_width, layer_height)
            pygame.draw.ellipse(surface, color, main_rect)

            # Glacê/brilho
            icing_rect = main_rect.inflate(-layer_width * 0.4, -layer_height * 0.4)
            icing_rect.move_ip(0, -1)
            pygame.draw.ellipse(surface, highlight, icing_rect)

            # Contorno fino
            pygame.draw.ellipse(surface, (80, 80, 80), main_rect, 1)

    def draw(self):
        self.screen.fill(self.bg_color)

        for idx, tube in enumerate(self.game.tubes):
            rect = self.get_cell_rect(idx)
            pygame.draw.rect(self.screen, self.grid_color, rect, 0, 15)
            pygame.draw.rect(self.screen, self.grid_border_color, rect, 2, 15)
            center_x, center_y = rect.center
            self.draw_plate_with_layers(self.screen, center_x, center_y, tube.layers)

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
                self.draw_plate_with_layers(self.screen, cx, cy, plate)

        title = self.big_font.render("Cake Sort Puzzle", True, self.text_color)
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 20))

        self.draw_scoreboard()
        pygame.display.flip()

    def draw_scoreboard(self):
        font = pygame.font.SysFont("Arial", 32)

        # Título
        title = font.render("SCOREBOARD", True, (50, 50, 50))
        self.screen.blit(title, (700, 100))  # ajusta posição conforme teu layout

        # Pontuação atual
        score_text = font.render(f"Score: {self.game.score}", True, (255, 100, 100))
        self.screen.blit(score_text, (700, 150))


    def load_level(self, filename: str):
        """Carrega um nível e reinicia o estado do jogo"""
        self.game.initialize_level(filename)
        self.selected_tube = None
        self.selected_queue_idx = None
        self.queue_plates = [self.generate_random_plate() for _ in range(self.queue_slots)]

    def handle_click(self, pos):
        for idx, plate in enumerate(self.queue_plates):
            if self.get_queue_slot_rect(idx).collidepoint(pos):
                if plate:
                    self.selected_queue_idx = idx
                    return

        if self.selected_queue_idx is not None:
            for idx, tube in enumerate(self.game.tubes):
                if self.get_cell_rect(idx).collidepoint(pos) and not tube.is_full() and tube.is_empty():
                    plate = self.queue_plates[self.selected_queue_idx]
                    if plate:
                        tube.add_layers_any_color(plate)

                        self.queue_plates[self.selected_queue_idx] = self.generate_random_plate()
                        try:
                            print("🔁 A correr merge_all_possible_layers()")
                            self.game.merge_all_possible_layers()
                            print("✅ Merge completo")
                        except Exception as e:
                            print("❌ ERRO DENTRO DO MERGE!")
                            import traceback
                            traceback.print_exc()
                            return

                        self.selected_queue_idx = None
                        return


        # Do tabuleiro para outro tubo: move todas as fatias
        if self.selected_tube is not None:
            for idx, tube in enumerate(self.game.tubes):
                if self.get_cell_rect(idx).collidepoint(pos) and idx != self.selected_tube:
                    self.game.move_all_layers(self.selected_tube, idx)
                    self.game.merge_all_possible_layers()
                    try:
                        print("🔁 A correr merge_all_possible_layers()")
                        self.game.merge_all_possible_layers()
                        print("✅ Merge completo")
                    except Exception as e:
                            print("❌ ERRO DENTRO DO MERGE!")
                            import traceback
                            traceback.print_exc()
                            return
                    self.draw()  # força atualização imediata
                    pygame.display.update()
                    self.selected_tube = None
                    return
            self.selected_tube = None

        else:
            for idx, tube in enumerate(self.game.tubes):
                if self.get_cell_rect(idx).collidepoint(pos) and tube.layers:
                    self.selected_tube = idx
                    return
                
                
    def animate_disappearing_plate(self, tube_idx):
        rect = self.get_cell_rect(tube_idx)
        center_x, center_y = rect.center
        original_layers = self.game.tubes[tube_idx].layers[:]

        for scale in reversed(range(1, 11)):  # de 10 → 1 (shrinking)
            self.draw()  # desenha normalmente
            scaled_layers = []

            for layer in original_layers:
                # copiar e marcar visualmente como encolhendo
                new_layer = CakeLayer(layer.color, layer.size)
                scaled_layers.append(new_layer)

            # desenhar as camadas com escala decrescente
            shrink_radius = int(self.cake_radius * (scale / 10))
            shrink_layer_height = int(self.layer_height * (scale / 10))

            pygame.draw.circle(self.screen, self.plate_color, (center_x, center_y), shrink_radius)
            num_layers = len(scaled_layers)
            total_height = num_layers * (shrink_layer_height + 2) - 2
            base_y = center_y + total_height // 2 - shrink_layer_height // 2

            for i, layer in enumerate(scaled_layers):
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
            pygame.time.delay(30)  # controla a velocidade da animação


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
