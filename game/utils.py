import pygame
from typing import Tuple

# Draw text to a surface
def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int], 
              font: pygame.font.Font, color: Tuple[int, int, int] = (0, 0, 0)):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)

# Load level file lines excluding comments
def load_level_file(filepath: str) -> list[str]:
    lines = []
    try:
        with open(filepath, "r") as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    lines.append(stripped)
    except FileNotFoundError:
        print(f"Could not find level file: {filepath}")
    return lines
