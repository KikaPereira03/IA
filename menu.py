# Main menu interface for Cake Sort Puzzle
import pygame
import sys
import random
from game.core import CakeSlice
from game.utils import draw_text

class CakeMenuUI:
    # Initialize menu settings and layout
    def __init__(self, game_ui_class):
        pygame.init()
        self.game_ui_class = game_ui_class

        self.screen_width = 1000
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cake Sort Puzzle - Menu")

        # Colors and fonts
        self.bg_color = (230, 220, 240)
        self.button_color = (180, 170, 230)
        self.button_border_color = (150, 140, 200)
        self.text_color = (80, 80, 100)
        self.highlight_color = (200, 190, 240)

        self.title_font = pygame.font.SysFont('Arial', 64)
        self.button_font = pygame.font.SysFont('Arial', 36)
        self.text_font = pygame.font.SysFont('Arial', 24)

        # Level and button config
        self.levels = ["Level 1", "Level 2", "Level 3"]
        self.selected_level = 0
        self.button_width = 300
        self.button_height = 80
        self.button_padding = 20
        self.clock = pygame.time.Clock()
        self.rules_expanded = False

        # Rules text
        self.rules = [
            "• Arrange matching cake pieces on plates",
            "• Click a cake to select it, then click a destination plate",
            "• You can only place cakes of the same color on top of each other",
            "• Complete levels by sorting all cakes by color",
            "• Use the queue at the bottom to place new cakes"
        ]

    # Get the rectangle for a button
    def get_button_rect(self, y_position):
        x = (self.screen_width - self.button_width) // 2
        return pygame.Rect(x, y_position, self.button_width, self.button_height)

    # Draw a single button
    def draw_button(self, text, y_position, hover=False):
        button_rect = self.get_button_rect(y_position)
        color = self.highlight_color if hover else self.button_color
        pygame.draw.rect(self.screen, color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)
        text_surf = self.button_font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)
        return button_rect

    # Draw level selector with < > arrows
    def draw_level_selector(self, y_position):
        button_rect = self.get_button_rect(y_position)
        pygame.draw.rect(self.screen, self.button_color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)
        level_text = self.levels[self.selected_level]
        text_surf = self.button_font.render(level_text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)

        # Draw left/right arrows
        left_arrow_rect = pygame.Rect(button_rect.x - 60, button_rect.y, 50, button_rect.height)
        right_arrow_rect = pygame.Rect(button_rect.x + button_rect.width + 10, button_rect.y, 50, button_rect.height)

        pygame.draw.rect(self.screen, self.button_color, left_arrow_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_color, right_arrow_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, left_arrow_rect, 2, 15)
        pygame.draw.rect(self.screen, self.button_border_color, right_arrow_rect, 2, 15)

        # Add arrow symbols
        left_text = self.button_font.render("<", True, self.text_color)
        right_text = self.button_font.render(">", True, self.text_color)
        self.screen.blit(left_text, left_text.get_rect(center=left_arrow_rect.center))
        self.screen.blit(right_text, right_text.get_rect(center=right_arrow_rect.center))

        return button_rect, left_arrow_rect, right_arrow_rect

    # Draw dropdown to show game rules
    def draw_rules_dropdown(self, y_position):
        hover = self.is_mouse_over_button(y_position)
        button_rect = self.get_button_rect(y_position)
        color = self.highlight_color if hover else self.button_color
        pygame.draw.rect(self.screen, color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)

        dropdown_symbol = "▼" if not self.rules_expanded else "▲"
        text = f"Game Rules {dropdown_symbol}"
        text_surf = self.button_font.render(text, True, self.text_color)
        self.screen.blit(text_surf, text_surf.get_rect(center=button_rect.center))

        # If expanded, show all rules
        if self.rules_expanded:
            rules_height = len(self.rules) * 30 + 40
            rules_rect = pygame.Rect(button_rect.x, button_rect.bottom + 5, button_rect.width, rules_height)
            pygame.draw.rect(self.screen, (255, 255, 255, 200), rules_rect, 0, 15)
            pygame.draw.rect(self.screen, self.button_border_color, rules_rect, 2, 15)

            # Draw rules text
            header = self.text_font.render("How to Play:", True, self.text_color)
            self.screen.blit(header, (rules_rect.x + 20, rules_rect.y + 15))
            for i, line in enumerate(self.rules):
                rule = self.text_font.render(line, True, self.text_color)
                self.screen.blit(rule, (rules_rect.x + 20, rules_rect.y + 45 + i * 30))

            return button_rect, rules_rect

        return button_rect, None

    # Check if mouse is over a given button
    def is_mouse_over_button(self, button_y):
        return self.get_button_rect(button_y).collidepoint(pygame.mouse.get_pos())

    # Draw the full menu screen
    def draw(self):
        self.screen.fill(self.bg_color)

        # Title
        title_surf = self.title_font.render("Cake Sort Puzzle", True, self.text_color)
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.screen_width // 2, 100)))

        # Buttons
        level_rects = self.draw_level_selector(200)
        rules_button_y = 300
        rules_rects = self.draw_rules_dropdown(rules_button_y)

        # Adjust position based on dropdown
        start_button_y = rules_rects[1].bottom + 30 if self.rules_expanded and rules_rects[1] else rules_button_y + self.button_height + 30
        start_rect = self.draw_button("Start Game", start_button_y, self.is_mouse_over_button(start_button_y))

        pygame.display.flip()
        return {'level': level_rects, 'rules': rules_rects[0], 'start': start_rect}

    # Handle mouse events
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

    # Prompt user for name input
    def ask_player_name(self):
        input_active = True
        name = ""
        clock = pygame.time.Clock()

        while input_active:
            self.screen.fill((30, 30, 30))
            # Input box
            box_rect = pygame.Rect((self.screen.get_width() - 500) // 2, (self.screen.get_height() - 250) // 2, 500, 250)
            pygame.draw.rect(self.screen, (245, 245, 255), box_rect, border_radius=25)
            pygame.draw.rect(self.screen, (180, 180, 220), box_rect, 4, border_radius=25)

            # Title
            title = pygame.font.SysFont("Arial", 38, bold=True).render("Qual é o teu nome?", True, (60, 60, 100))
            self.screen.blit(title, (self.screen.get_width() // 2 - title.get_width() // 2, box_rect.top + 30))

            # Input box
            input_rect = pygame.Rect(self.screen.get_width() // 2 - 150, box_rect.top + 100, 300, 40)
            pygame.draw.rect(self.screen, (255, 255, 255), input_rect, border_radius=10)
            pygame.draw.rect(self.screen, (150, 150, 200), input_rect, 2, border_radius=10)

            # User input
            font = pygame.font.SysFont("Arial", 28)
            self.screen.blit(font.render(name + "|", True, (80, 80, 120)), (input_rect.x + 10, input_rect.y + 5))

            # Instruction
            instruction = font.render("Enter para confirmar", True, (120, 120, 140))
            self.screen.blit(instruction, (self.screen.get_width() // 2 - instruction.get_width() // 2, box_rect.bottom - 50))

            pygame.display.flip()

            # Keyboard events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and name.strip():
                        input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif len(name) < 12 and event.unicode.isprintable():
                        name += event.unicode

            clock.tick(30)

        return name.strip()

    # Run the menu loop
    def run(self):
        running = True
        while running:
            button_rects = self.draw()
            running, action = self.handle_events(button_rects)

            if action == 'start_game':
                level_file = f"game/levels/level{self.selected_level + 1}.txt"
                player_name = self.ask_player_name()
                game_ui = self.game_ui_class(level_file=level_file, player_name=player_name)
                game_ui.run()

                # Return to menu
                pygame.display.set_mode((self.screen_width, self.screen_height))
                pygame.display.set_caption("Cake Sort Puzzle - Menu")
                running = True

            self.clock.tick(60)

        pygame.quit()
        sys.exit()

# Launch menu if script is run directly
if __name__ == "__main__":
    from main import CakeGameUI
    menu = CakeMenuUI(CakeGameUI)
    menu.run()
