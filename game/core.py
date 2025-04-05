import pygame
from typing import List, Tuple, Optional
from game.utils import load_level_file
from dataclasses import dataclass
import os

# Represents a slice of cake with color and size
@dataclass
class CakeSlice:
    color: str
    size: int

    def __str__(self):
        return f"{self.color}{self.size}"

# Represents a plate that holds cake slices
class Plate:
    def __init__(self, max_capacity: int = 6):
        self.slices: List[CakeSlice] = []
        self.max_capacity = max_capacity

    def __str__(self):
        return " ".join(str(layer) for layer in self.slices)

# Main game class
class CakeGame:
    def __init__(self, width: int = 5, height: int = 4, max_capacity: int = 6):
        self.width = width
        self.height = height
        self.max_capacity = max_capacity
        self.plates: List[Plate] = [Plate(max_capacity) for _ in range(width * height)]
        self.moves = 0
        self.selected_plate = None
        self.selected_layer_pos = None
        self.score = 0
        self.base_score = 0  

    # Load initial game state and queue from level file
    def initialize_level(self, level_file: str):
        self.plates = [Plate(self.max_capacity) for _ in range(self.width * self.height)]
        self.moves = 0

        try:
            grid_lines = load_level_file(level_file)

            self.queue_data = []
            reading_queue = False

            for line in grid_lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                if line.lower().startswith("queue:"):
                    reading_queue = True
                    continue

                if reading_queue:
                    if ':' in line:
                        break
                    self.queue_data.append(list(line.strip()))
                    continue

                parts = line.strip().split(':')
                if len(parts) < 2:
                    continue

                plate_idx, slices_str = parts[0], parts[1]
                plate = self.plates[int(plate_idx)]

                for layer_str in slices_str.split():
                    if not layer_str:
                        continue
                    color = layer_str[0].upper()
                    size = int(layer_str[1:]) if len(layer_str) > 1 else 1
                    plate.slices.append(CakeSlice(color, size))

        except FileNotFoundError:
            print(f"Error: Level file {level_file} not found")

    # Create a hash of the game board state
    def get_state_hash(self) -> str:
        return "|".join(str(plate) for plate in self.plates)

    # Get indices of adjacent plates
    def get_adjacent_plates(self, plate_idx: int) -> List[int]:
        row = plate_idx // self.width
        col = plate_idx % self.width
        adjacent = []

        if row > 0:
            adjacent.append(plate_idx - self.width)
        if row < self.height - 1:
            adjacent.append(plate_idx + self.width)
        if col > 0:
            adjacent.append(plate_idx - 1)
        if col < self.width - 1:
            adjacent.append(plate_idx + 1)

        return adjacent
