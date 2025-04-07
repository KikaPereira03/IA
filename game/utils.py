import pygame
from typing import Tuple
from game.models import CakeSlice


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

def evaluate_board(grid):
    from game.core import CakeSlice  
    # Heurística simples: soma total de blocos de cores iguais consecutivos
    score = 0
    for plate in grid:
        current = None
        streak = 0
        for slice in plate.slices:
            if slice.color == current:
                streak += 1
            else:
                current = slice.color
                streak = 1
            score += streak
    return score

