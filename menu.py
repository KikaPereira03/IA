import pygame
import sys
import random
from game.core import CakeLayer
from game.utils import draw_text

class CakeMenuUI:
    def __init__(self, game_ui_class):
        pygame.init()
        self.game_ui_class = game_ui_class

        self.screen_width = 1000
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cake Sort Puzzle - Menu")

        self.bg_color = (230, 220, 240)
        self.button_color = (180, 170, 230)
        self.button_border_color = (150, 140, 200)
        self.text_color = (80, 80, 100)
        self.highlight_color = (200, 190, 240)

        self.title_font = pygame.font.SysFont('Arial', 64)
        self.button_font = pygame.font.SysFont('Arial', 36)
        self.text_font = pygame.font.SysFont('Arial', 24)

        self.levels = ["Level 1", "Level 2", "Level 3"]
        self.selected_level = 0

        self.button_width = 300
        self.button_height = 80
        self.button_padding = 20

        self.clock = pygame.time.Clock()
        self.rules_expanded = False

        self.rules = [
            "• Arrange matching cake pieces on plates",
            "• Click a cake to select it, then click a destination plate",
            "• You can only place cakes of the same color on top of each other",
            "• Complete levels by sorting all cakes by color",
            "• Use the queue at the bottom to place new cakes"
        ]

    def get_button_rect(self, y_position):
        x = (self.screen_width - self.button_width) // 2
        return pygame.Rect(x, y_position, self.button_width, self.button_height)

    def draw_button(self, text, y_position, hover=False):
        button_rect = self.get_button_rect(y_position)
        color = self.highlight_color if hover else self.button_color
        pygame.draw.rect(self.screen, color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)
        text_surf = self.button_font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)
        return button_rect

    def draw_level_selector(self, y_position):
        button_rect = self.get_button_rect(y_position)
        pygame.draw.rect(self.screen, self.button_color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)
        level_text = self.levels[self.selected_level]
        text_surf = self.button_font.render(level_text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

        left_arrow_rect = pygame.Rect(button_rect.x - 60, button_rect.y, 50, button_rect.height)
        pygame.draw.rect(self.screen, self.button_color, left_arrow_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, left_arrow_rect, 2, 15)
        left_text = self.button_font.render("<", True, self.text_color)
        left_text_rect = left_text.get_rect(center=left_arrow_rect.center)
        self.screen.blit(left_text, left_text_rect)

        right_arrow_rect = pygame.Rect(button_rect.x + button_rect.width + 10, button_rect.y, 50, button_rect.height)
        pygame.draw.rect(self.screen, self.button_color, right_arrow_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, right_arrow_rect, 2, 15)
        right_text = self.button_font.render(">", True, self.text_color)
        right_text_rect = right_text.get_rect(center=right_arrow_rect.center)
        self.screen.blit(right_text, right_text_rect)

        return button_rect, left_arrow_rect, right_arrow_rect

    def draw_rules_dropdown(self, y_position):
        hover = self.is_mouse_over_button(y_position)
        button_rect = self.get_button_rect(y_position)
        color = self.highlight_color if hover else self.button_color
        pygame.draw.rect(self.screen, color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)

        dropdown_symbol = "▼" if not self.rules_expanded else "▲"
        text = f"Game Rules {dropdown_symbol}"
        text_surf = self.button_font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

        if self.rules_expanded:
            rules_height = len(self.rules) * 30 + 40
            rules_rect = pygame.Rect(
                button_rect.x, button_rect.bottom + 5,
                button_rect.width, rules_height
            )
            pygame.draw.rect(self.screen, (255, 255, 255, 200), rules_rect, 0, 15)
            pygame.draw.rect(self.screen, self.button_border_color, rules_rect, 2, 15)
            header = "How to Play:"
            header_surf = self.text_font.render(header, True, self.text_color)
            self.screen.blit(header_surf, (rules_rect.x + 20, rules_rect.y + 15))

            for i, line in enumerate(self.rules):
                text_surf = self.text_font.render(line, True, self.text_color)
                self.screen.blit(text_surf, (rules_rect.x + 20, rules_rect.y + 45 + i * 30))

            return button_rect, rules_rect

        return button_rect, None

    def is_mouse_over_button(self, button_y):
        mouse_pos = pygame.mouse.get_pos()
        button_rect = self.get_button_rect(button_y)
        return button_rect.collidepoint(mouse_pos)

    def draw(self):
        self.screen.fill(self.bg_color)

        title_surf = self.title_font.render("Cake Sort Puzzle", True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title_surf, title_rect)

        level_rects = self.draw_level_selector(200)
        rules_button_y = 300
        rules_rects = self.draw_rules_dropdown(rules_button_y)

        if self.rules_expanded and rules_rects[1]:
            start_button_y = rules_rects[1].bottom + 30
        else:
            start_button_y = rules_button_y + self.button_height + 30

        start_rect = self.draw_button("Start Game", start_button_y, 
                                     self.is_mouse_over_button(start_button_y))

        pygame.display.flip()

        return {
            'level': level_rects,
            'rules': rules_rects[0],
            'start': start_rect
        }

    def handle_events(self, button_rects):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, None

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                level_rect, left_arrow, right_arrow = button_rects['level']
                if left_arrow.collidepoint(mouse_pos):
                    self.selected_level = (self.selected_level - 1) % len(self.levels)
                elif right_arrow.collidepoint(mouse_pos):
                    self.selected_level = (self.selected_level + 1) % len(self.levels)

                if button_rects['rules'].collidepoint(mouse_pos):
                    self.rules_expanded = not self.rules_expanded

                if button_rects['start'].collidepoint(mouse_pos):
                    return False, 'start_game'

        return True, None

    def run(self):
        running = True
        while running:
            button_rects = self.draw()
            running, action = self.handle_events(button_rects)

            if action == 'start_game':
                level_file = f"game/levels/level{self.selected_level + 1}.txt"
                game_ui = self.game_ui_class(level_file=level_file)
                game_ui.run()


                pygame.display.set_mode((self.screen_width, self.screen_height))
                pygame.display.set_caption("Cake Sort Puzzle - Menu")
                running = True

            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    from main import CakeGameUI
    menu = CakeMenuUI(CakeGameUI)
    menu.run()