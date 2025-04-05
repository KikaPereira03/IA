import pygame
from typing import Tuple

# Load and optionally scale an image
def load_image(path: str, scale: float = 1.0) -> pygame.Surface:
    try:
        image = pygame.image.load(path)
        if scale != 1.0:
            new_size = (int(image.get_width() * scale), 
                        int(image.get_height() * scale))
            image = pygame.transform.scale(image, new_size)
        return image.convert_alpha()
    except pygame.error:
        return pygame.Surface((32, 32))  # fallback empty surface

# Draw text to a surface
def draw_text(surface: pygame.Surface, text: str, pos: Tuple[int, int], 
              font: pygame.font.Font, color: Tuple[int, int, int] = (0, 0, 0)):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, pos)

# Create a vertical color gradient
def create_gradient(width: int, height: int, 
                   start_color: Tuple[int, int, int], 
                   end_color: Tuple[int, int, int]) -> pygame.Surface:
    gradient = pygame.Surface((width, height))
    for y in range(height):
        ratio = y / height
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        pygame.draw.line(gradient, (r, g, b), (0, y), (width, y))
    return gradient

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

# Save updated score to a level file
def save_score_in_level_file(level, new_entry):
    filename = f"game/levels/level{level}.txt"
    grid, scoreboard = load_level_and_scoreboard(level)

    name, score = new_entry

    # Check if player already has a score
    updated = False
    for i, (existing_name, existing_score) in enumerate(scoreboard):
        if existing_name == name:
            if score > existing_score:
                scoreboard[i] = (name, score)
            updated = True
            break

    if not updated:
        scoreboard.append((name, score))

    # Sort scores in descending order
    scoreboard.sort(key=lambda x: x[1], reverse=True)

    # Rewrite level file with updated scoreboard
    with open(filename, "w") as f:
        for line in grid:
            f.write(f"{line}\n")
        f.write("\n# SCOREBOARD\n")
        for name, score in scoreboard:
            f.write(f"{name} {score}\n")