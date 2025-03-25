"""
Cake theme management for the Cake Sort Puzzle game.
Defines colors and decorations for different cake layer types.
"""

class CakeTheme:
    def __init__(self, name, colors, decorations=None):
        self.name = name
        self.colors = colors  # Dictionary mapping color codes to RGB values
        self.decorations = decorations or {}  # Optional decorations for each color
        
    def get_layer_color(self, color_code):
        return self.colors.get(color_code, (200, 200, 200))
    
    def get_decoration(self, color_code):
        return self.decorations.get(color_code)

# Define available themes
THEMES = {
    "classic": CakeTheme(
        "Classic", 
        {'R': (255, 0, 0), 'G': (0, 255, 0), 'B': (0, 0, 255), 'Y': (255, 255, 0), 
         'P': (255, 0, 255), 'O': (255, 165, 0), 'C': (0, 255, 255), 'M': (150, 0, 150)}
    ),
    "pastel": CakeTheme(
        "Pastel", 
        {'R': (255, 182, 193), 'G': (152, 251, 152), 'B': (173, 216, 230), 
         'Y': (255, 255, 224), 'P': (221, 160, 221), 'O': (255, 218, 185), 
         'C': (175, 238, 238), 'M': (230, 230, 250)}
    ),
    "chocolate": CakeTheme(
        "Chocolate", 
        {'R': (139, 69, 19), 'G': (160, 82, 45), 'B': (101, 67, 33), 
         'Y': (210, 180, 140), 'P': (165, 42, 42), 'O': (205, 133, 63), 
         'C': (222, 184, 135), 'M': (160, 120, 90)}
    ),
    "frosting": CakeTheme(
        "Frosting",
        {'R': (255, 102, 102), 'G': (102, 255, 102), 'B': (102, 102, 255), 
         'Y': (255, 255, 102), 'P': (255, 102, 255), 'O': (255, 178, 102), 
         'C': (102, 255, 255), 'M': (178, 102, 255)},
        # Decorations are tuples with (decoration_type, parameters)
        {'R': ('sprinkles', (255, 255, 255)), 
         'Y': ('dots', (0, 0, 0)), 
         'G': ('swirl', (255, 255, 255)),
         'B': ('lines', (255, 255, 255))}
    )
}

def get_theme(theme_name):
    """Get a theme by name, defaulting to 'classic' if not found"""
    return THEMES.get(theme_name, THEMES["classic"])

def get_available_themes():
    """Return a list of available theme names"""
    return list(THEMES.keys())