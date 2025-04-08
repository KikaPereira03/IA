import pygame
import sys
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

        self.title_font = pygame.font.SysFont('Arial', 40)
        self.button_font = pygame.font.SysFont('Arial', 20)
        self.text_font = pygame.font.SysFont('Arial', 15)

        self.levels = ["Level 1", "Level 2", "Level 3"]
        self.selected_level = 0
        self.button_width = 250
        self.button_height = 70
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

        self.bot_popup_visible = False
        self.bot_options = ["Greedy", "A*", "BFS", "DFS"]
        self.selected_bot = None
        self.bot_option_rects = []

    # -------------------------
    # Drawing Helpers
    # -------------------------

    def get_button_rect(self, y_position):
        x = (self.screen_width - self.button_width) // 2
        return pygame.Rect(x, y_position, self.button_width, self.button_height)

    def is_mouse_over_button(self, y):
        return self.get_button_rect(y).collidepoint(pygame.mouse.get_pos())

    def draw_button(self, text, y_position, hover=False):
        button_rect = self.get_button_rect(y_position)
        color = self.highlight_color if hover else self.button_color
        pygame.draw.rect(self.screen, color, button_rect, 0, border_radius=10)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, border_radius=10)

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
        right_arrow_rect = pygame.Rect(button_rect.x + button_rect.width + 10, button_rect.y, 50, button_rect.height)

        for arrow_rect, symbol in zip([left_arrow_rect, right_arrow_rect], ["<", ">"]):
            pygame.draw.rect(self.screen, self.button_color, arrow_rect, 0, 15)
            pygame.draw.rect(self.screen, self.button_border_color, arrow_rect, 2, 15)
            text = self.button_font.render(symbol, True, self.text_color)
            self.screen.blit(text, text.get_rect(center=arrow_rect.center))

        return button_rect, left_arrow_rect, right_arrow_rect

    def draw_rules_dropdown(self, y_position):
        hover = self.is_mouse_over_button(y_position)
        button_rect = self.get_button_rect(y_position)
        color = self.highlight_color if hover else self.button_color
        pygame.draw.rect(self.screen, color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)

        text = "Game Rules"
        text_surf = self.button_font.render(text, True, self.text_color)
        self.screen.blit(text_surf, text_surf.get_rect(center=button_rect.center))

        if self.rules_expanded:
            rules_height = len(self.rules) * 50 + 40
            rules_rect = pygame.Rect(button_rect.x, button_rect.bottom + 5, button_rect.width, rules_height)
            pygame.draw.rect(self.screen, (255, 255, 255, 200), rules_rect, 0, 15)
            pygame.draw.rect(self.screen, self.button_border_color, rules_rect, 2, 15)

            header = self.text_font.render("How to Play:", True, self.text_color)
            self.screen.blit(header, (rules_rect.x + 20, rules_rect.y + 15))

            def wrap_text(text, max_width):
                words = text.split(' ')
                lines = []
                current_line = ""
                for word in words:
                    if self.text_font.size(current_line + " " + word)[0] <= max_width:
                        current_line += " " + word
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                return lines

            for i, line in enumerate(self.rules):
                wrapped_lines = wrap_text(line, button_rect.width - 40)
                line_y_position = rules_rect.y + 45 + i * 50
                for j, wrapped_line in enumerate(wrapped_lines):
                    rule_text = self.text_font.render(wrapped_line, True, self.text_color)
                    self.screen.blit(rule_text, (rules_rect.x + 20, line_y_position + j * 20))

            return button_rect, rules_rect

        return button_rect, None

    def show_bot_selection_popup(self):
        popup_running = True
        popup_width, popup_height = 300, 250
        popup_rect = pygame.Rect(
            self.screen_width // 2 - popup_width // 2,
            self.screen_height // 2 - popup_height // 2,
            popup_width,
            popup_height
        )

        bot_options = self.bot_options
        selected_bot = None

        while popup_running:
            self.screen.fill((0, 0, 0, 120))
            pygame.draw.rect(self.screen, (250, 250, 255), popup_rect, border_radius=20)
            pygame.draw.rect(self.screen, (180, 180, 220), popup_rect, 3, border_radius=20)

            title = self.button_font.render("Choose Bot Algorithm", True, (80, 60, 120))
            self.screen.blit(title, (popup_rect.centerx - title.get_width() // 2, popup_rect.top + 20))

            for i, bot in enumerate(bot_options):
                btn_rect = pygame.Rect(popup_rect.left + 40, popup_rect.top + 60 + i * 45, 220, 35)
                pygame.draw.rect(self.screen, (200, 180, 250), btn_rect, border_radius=10)
                pygame.draw.rect(self.screen, (140, 120, 200), btn_rect, 2, border_radius=10)

                label = self.button_font.render(bot, True, (60, 60, 80))
                self.screen.blit(label, (btn_rect.centerx - label.get_width() // 2, btn_rect.centery - label.get_height() // 2))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = pygame.mouse.get_pos()
                    for i, bot in enumerate(bot_options):
                        btn_rect = pygame.Rect(popup_rect.left + 40, popup_rect.top + 60 + i * 45, 220, 35)
                        if btn_rect.collidepoint(mouse_pos):
                            selected_bot = bot.lower()
                            popup_running = False
                            break

        if selected_bot:
            from main import CakeGameUI
            game_ui = CakeGameUI(level_file=f"game/levels/level{self.selected_level + 1}.txt", bot_algorithm=selected_bot)
            game_ui.run()

    # -------------------------
    # Main Menu Logic
    # -------------------------

    def draw(self):
        self.screen.fill(self.bg_color)
        title_surf = self.title_font.render("Cake Sort Puzzle", True, self.text_color)
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.screen_width // 2, 140)))

        level_rects = self.draw_level_selector(200)
        rules_button_y = 300
        rules_rects = self.draw_rules_dropdown(rules_button_y)

        start_button_y = rules_rects[1].bottom + 30 if self.rules_expanded and rules_rects[1] else rules_button_y + self.button_height + 30
        start_rect = self.draw_button("Start Game", start_button_y, self.is_mouse_over_button(start_button_y))

        bot_button_y = start_button_y + self.button_height + 20
        bot_rect = self.draw_button("Bot", bot_button_y, self.is_mouse_over_button(bot_button_y))

        pygame.display.flip()
        return {
            'level': level_rects,
            'rules': rules_rects[0],
            'start': start_rect,
            'bot': bot_rect
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
                if button_rects['bot'].collidepoint(mouse_pos):
                    self.show_bot_selection_popup()
        return True, None

    def run(self):
        running = True
        try:
            while running:
                button_rects = self.draw()
                running, action = self.handle_events(button_rects)
                if action == 'start_game':
                    level_file = f"game/levels/level{self.selected_level + 1}.txt"
                    game_ui = self.game_ui_class(level_file=level_file)
                    try:
                        game_ui.run()
                    except KeyboardInterrupt:
                        print("\nGame closed by user.")
                    pygame.display.set_mode((self.screen_width, self.screen_height))
                    pygame.display.set_caption("Cake Sort Puzzle - Menu")
                    running = True
                self.clock.tick(60)
        except KeyboardInterrupt:
            print("\nExiting game...")
        finally:
            pygame.quit()
            sys.exit(0) 

# -------------------------
# Entry Point
# -------------------------

if __name__ == "__main__":
    from main import CakeGameUI
    menu = CakeMenuUI(CakeGameUI)
    menu.run()
