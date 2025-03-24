import pygame
from typing import Tuple

def load_image(path: str, scale: float = 1.0) -> pygame.Surface:
    """Load and scale an image"""
    try:
        image = pygame.image.load(path)
        if scale != 1.0:
            new_size = (int(image.get_width() * scale), 
                        int(image.get_height() * scale))
            image = pygame.transform.scale(image, new_size)
        return image.convert_alpha()
    except pygame.error:
        print(f"Warning: Could not load image {path}")
        return pygame.Surface((32, 32))  # Return blank surface as fallback

def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int], 
              font: pygame.font.Font, color: Tuple[int, int, int] = (0, 0, 0)):
    """Helper function to draw text"""
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)

def create_gradient(width: int, height: int, 
                   start_color: Tuple[int, int, int], 
                   end_color: Tuple[int, int, int]) -> pygame.Surface:
    """Create a vertical gradient surface"""
    gradient = pygame.Surface((width, height))
    for y in range(height):
        # Interpolate between start and end color
        ratio = y / height
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        pygame.draw.line(gradient, (r, g, b), (0, y), (width, y))
    return gradient