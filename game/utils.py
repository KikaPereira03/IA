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

def load_level_and_scoreboard(level):
    filename = f"game/levels/level{level}.txt" 
    grid = []
    scoreboard = []
    reading_scoreboard = False
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("# SCOREBOARD"):
                    reading_scoreboard = True
                    continue
                if reading_scoreboard:
                    parts = line.split()
                    if len(parts) == 2:
                        name, score = parts[0], int(parts[1])
                        scoreboard.append((name, score))
                else:
                    grid.append(line)
    except FileNotFoundError:
        pass
    return grid, scoreboard

def save_score_in_level_file(level, new_entry):
    filename = f"game/levels/level{level}.txt"
    grid, scoreboard = load_level_and_scoreboard(level)

    name, score = new_entry

    # 🔁 Verifica se o jogador já está no scoreboard
    updated = False
    for i, (existing_name, existing_score) in enumerate(scoreboard):
        if existing_name == name:
            if score > existing_score:
                scoreboard[i] = (name, score)  # atualiza se for maior
            updated = True
            break

    if not updated:
        scoreboard.append((name, score))

    # 🔽 Ordena por score decrescente
    scoreboard.sort(key=lambda x: x[1], reverse=True)

    # 💾 Reescreve o ficheiro todo
    with open(filename, "w") as f:
        for line in grid:
            f.write(f"{line}\n")
        f.write("\n# SCOREBOARD\n")
        for name, score in scoreboard:
            f.write(f"{name} {score}\n")


