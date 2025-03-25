import pygame
import sys
from game.core import CakeGame
from game.utils import draw_text

class CakeMenuUI:
    def __init__(self, game_ui_class):
        pygame.init()
        
        # Store the game UI class for starting the game
        self.game_ui_class = game_ui_class
        
        # UI Settings
        self.screen_width = 1000
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Cake Sort Puzzle - Menu")
        
        # Colors - Match the game UI colors
        self.bg_color = (230, 220, 240)  # Lighter purple background
        self.button_color = (180, 170, 230)  # Light purple
        self.button_border_color = (150, 140, 200)  # Darker purple
        self.text_color = (80, 80, 100)  # Darker text
        self.highlight_color = (200, 190, 240)  # Highlight color for hover
        
        # Fonts
        self.title_font = pygame.font.SysFont('Arial', 64)
        self.button_font = pygame.font.SysFont('Arial', 36)
        self.text_font = pygame.font.SysFont('Arial', 24)
        
        # Current level selection
        self.levels = ["Level 1", "Level 2", "Level 3"]  # Only 3 levels
        self.selected_level = 0
        
        # Button dimensions
        self.button_width = 300
        self.button_height = 80
        self.button_padding = 20
        
        # Clock for frame rate
        self.clock = pygame.time.Clock()
        
        # Rules dropdown state
        self.rules_expanded = False
        
        # Rules text
        self.rules = [
            "• Arrange matching cake pieces on plates",
            "• Click a cake to select it, then click a destination plate",
            "• You can only place cakes of the same color on top of each other",
            "• Complete levels by sorting all cakes by color",
            "• Use the queue at the bottom to place new cakes"
        ]
    
    def get_button_rect(self, y_position):
        """Get centered button rectangle at specified y position"""
        x = (self.screen_width - self.button_width) // 2
        return pygame.Rect(x, y_position, self.button_width, self.button_height)
    
    def draw_button(self, text, y_position, hover=False):
        """Draw a button with text at the specified y position"""
        button_rect = self.get_button_rect(y_position)
        
        # Button background
        color = self.highlight_color if hover else self.button_color
        pygame.draw.rect(self.screen, color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)
        
        # Button text
        text_surf = self.button_font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)
        
        return button_rect
    
    def draw_level_selector(self, y_position):
        """Draw a level selector with left/right arrows"""
        # Main button with level text
        button_rect = self.get_button_rect(y_position)
        
        # Button background
        pygame.draw.rect(self.screen, self.button_color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)
        
        # Level text
        level_text = self.levels[self.selected_level]
        text_surf = self.button_font.render(level_text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)
        
        # Left arrow button
        left_arrow_rect = pygame.Rect(button_rect.x - 60, button_rect.y, 50, button_rect.height)
        pygame.draw.rect(self.screen, self.button_color, left_arrow_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, left_arrow_rect, 2, 15)
        left_text = self.button_font.render("<", True, self.text_color)
        left_text_rect = left_text.get_rect(center=left_arrow_rect.center)
        self.screen.blit(left_text, left_text_rect)
        
        # Right arrow button
        right_arrow_rect = pygame.Rect(button_rect.x + button_rect.width + 10, button_rect.y, 50, button_rect.height)
        pygame.draw.rect(self.screen, self.button_color, right_arrow_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, right_arrow_rect, 2, 15)
        right_text = self.button_font.render(">", True, self.text_color)
        right_text_rect = right_text.get_rect(center=right_arrow_rect.center)
        self.screen.blit(right_text, right_text_rect)
        
        return button_rect, left_arrow_rect, right_arrow_rect
    
    def draw_rules_dropdown(self, y_position):
        """Draw rules dropdown button and content if expanded"""
        # Rules button
        hover = self.is_mouse_over_button(y_position)
        button_rect = self.get_button_rect(y_position)
        
        # Button background
        color = self.highlight_color if hover else self.button_color
        pygame.draw.rect(self.screen, color, button_rect, 0, 15)
        pygame.draw.rect(self.screen, self.button_border_color, button_rect, 2, 15)
        
        # Button text with dropdown indicator
        dropdown_symbol = "▼" if not self.rules_expanded else "▲"
        text = f"Game Rules"
        text_surf = self.button_font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        self.screen.blit(text_surf, text_rect)
        
        # Draw expanded content if needed
        if self.rules_expanded:
            rules_height = len(self.rules) * 30 + 40  # Height based on number of lines
            rules_rect = pygame.Rect(
                button_rect.x,
                button_rect.bottom + 5,
                button_rect.width,
                rules_height
            )
            
            # Rules content background
            pygame.draw.rect(self.screen, (255, 255, 255, 200), rules_rect, 0, 15)
            pygame.draw.rect(self.screen, self.button_border_color, rules_rect, 2, 15)
            
            # Rules text
            header = "How to Play:"
            header_surf = self.text_font.render(header, True, self.text_color)
            self.screen.blit(header_surf, (rules_rect.x + 20, rules_rect.y + 15))
            
            for i, line in enumerate(self.rules):
                text_surf = self.text_font.render(line, True, self.text_color)
                self.screen.blit(text_surf, (rules_rect.x + 20, rules_rect.y + 45 + i * 30))
            
            return button_rect, rules_rect
        
        return button_rect, None
    
    def draw(self):
        """Draw the menu screen"""
        self.screen.fill(self.bg_color)
        
        # Title
        title_surf = self.title_font.render("Cake Sort Puzzle", True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 100))
        self.screen.blit(title_surf, title_rect)
        
        # Level selector (y position 200)
        level_rects = self.draw_level_selector(200)
        
        # Rules dropdown (y position 300)
        rules_button_y = 300
        rules_rects = self.draw_rules_dropdown(rules_button_y)
        
        # Calculate start button position based on whether rules are expanded
        if self.rules_expanded and rules_rects[1]:
            start_button_y = rules_rects[1].bottom + 30
        else:
            start_button_y = rules_button_y + self.button_height + 30
        
        # Start button 
        start_rect = self.draw_button("Start Game", start_button_y, 
                                     self.is_mouse_over_button(start_button_y))
        
        pygame.display.flip()
        
        return {
            'level': level_rects,
            'rules': rules_rects[0],
            'start': start_rect
        }
    
    def is_mouse_over_button(self, button_y):
        """Check if mouse is over a button at the specified y position"""
        mouse_pos = pygame.mouse.get_pos()
        button_rect = self.get_button_rect(button_y)
        return button_rect.collidepoint(mouse_pos)
    
    def handle_events(self, button_rects):
        """Handle user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, None
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Left click
                mouse_pos = pygame.mouse.get_pos()
                
                # Check level selector
                level_rect, left_arrow, right_arrow = button_rects['level']
                if left_arrow.collidepoint(mouse_pos):
                    self.selected_level = (self.selected_level - 1) % len(self.levels)
                elif right_arrow.collidepoint(mouse_pos):
                    self.selected_level = (self.selected_level + 1) % len(self.levels)
                
                # Check rules button
                if button_rects['rules'].collidepoint(mouse_pos):
                    self.rules_expanded = not self.rules_expanded
                
                # Check start button
                if button_rects['start'].collidepoint(mouse_pos):
                    return False, 'start_game'
        
        return True, None
    
    def run(self):
        """Main menu loop"""
        running = True
        while running:
            button_rects = self.draw()
            running, action = self.handle_events(button_rects)
            
            if action == 'start_game':
                # Start the game with the selected level
                level_file = f"game/levels/level{self.selected_level + 1}.txt"
                game_ui = self.game_ui_class()
                game_ui.load_level(level_file)
                game_ui.run()
                
                # After the game loop ends, recreate the menu display
                pygame.display.set_mode((self.screen_width, self.screen_height))
                pygame.display.set_caption("Cake Sort Puzzle - Menu")
                running = True
            
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()


# Example usage
if __name__ == "__main__":
    # Import the game UI class to avoid circular imports
    from main import CakeGameUI
    
    menu = CakeMenuUI(CakeGameUI)
    menu.run()


# Example usage
if __name__ == "__main__":
    # Import the game UI class to avoid circular imports
    from main import CakeGameUI
    
    menu = CakeMenuUI(CakeGameUI)
    menu.run()

if __name__ == "__main__":
    # Import the game UI class to avoid circular imports
    from main import CakeGameUI
    
    menu = CakeMenuUI(CakeGameUI)
    menu.run()