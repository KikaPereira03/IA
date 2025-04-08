import pygame
from typing import Tuple
from game.models import CakeSlice
import os
import time
import tracemalloc


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

def evaluate_board(grid, game=None, last_move=None):
    """
    Enhanced evaluation function that considers multiple strategic factors.
    
    Args:
        grid: List of plates to evaluate
        game: Optional CakeGame instance for additional context (adjacency info)
        last_move: Optional (queue_idx, grid_idx) tuple indicating the last move made
        
    Returns:
        Score value - higher is better
    """
    # Basic score: Count consecutive same-colored slices
    basic_score = 0
    for plate in grid:
        current = None
        streak = 0
        for slice in plate.slices:
            if slice.color == current:
                streak += 1
            else:
                current = slice.color
                streak = 1
            basic_score += streak
    
    # Enhanced scoring factors
    strategic_score = 0
    
    # Factor 1: Reward plates with uniform colors
    for plate in grid:
        if not plate.slices:
            continue
            
        colors = [s.color for s in plate.slices]
        unique_colors = set(colors)
        
        if len(unique_colors) == 1:
            # Single-color plate - big bonus that scales with count
            count = len(colors)
            strategic_score += count * 15
            
            # Extra bonus for plates close to completion (6 slices)
            if count >= 4:
                strategic_score += (count - 3) * 20
        else:
            # Mixed plate - small penalty based on number of different colors
            strategic_score -= (len(unique_colors) - 1) * 5
    
    # Factor 2: Consider color adjacency if game context is provided
    if game is not None and last_move is not None:
        _, g_idx = last_move
        plate = grid[g_idx]
        
        if plate.slices:
            plate_color = plate.slices[0].color
            adjacent_plates = game.get_adjacent_plates(g_idx)
            
            for adj_idx in adjacent_plates:
                if adj_idx < len(grid) and grid[adj_idx].slices:
                    adj_colors = [s.color for s in grid[adj_idx].slices]
                    
                    # Bonus for adjacent plates with matching colors
                    if plate_color in adj_colors:
                        strategic_score += 25
                    
                    # Smaller bonus for adjacency in general (clustering)
                    strategic_score += 5
    
    # Factor 3: Reward progress toward clearing plates
    # Count plates close to completion (6 slices of same color)
    near_complete_plates = 0
    for plate in grid:
        if len(plate.slices) == 6:
            colors = [s.color for s in plate.slices]
            if len(set(colors)) == 1:
                near_complete_plates += 1
    
    strategic_score += near_complete_plates * 30
    
    # Factor 4: Prefer boards with fewer mixed-color plates
    mixed_plates = sum(1 for plate in grid if 
                      plate.slices and len(set(s.color for s in plate.slices)) > 1)
    strategic_score -= mixed_plates * 10
    
    # Calculate final score with weighted components
    final_score = basic_score + strategic_score
    
    return final_score

