import pygame
from typing import List, Tuple, Optional
from dataclasses import dataclass
import os

@dataclass
class CakeGame:
    def __init__(self, width: int = 5, height: int = 4, max_capacity: int = 6):  # Changed to 5x4
        self.width = width
        self.height = height
        self.max_capacity = max_capacity
        self.tubes: List[Tube] = []
        self.moves = 0
        self.selected_tube = None
        self.selected_layer_pos = None

class Tube:
    def __init__(self, max_capacity: int = 6):
        self.layers: List[CakeLayer] = []
        self.max_capacity = max_capacity
    
    def can_add(self, layer: CakeLayer) -> bool:
        """Check if we can add this layer to the top"""
        return (len(self.layers) < self.max_capacity and 
                (self.is_empty() or self.top_layer().color == layer.color))
    
    def add_layer(self, layer: CakeLayer) -> bool:
        """Add layer to the top (stack behavior)"""
        if self.can_add(layer):
            self.layers.append(layer)
            return True
        return False
    
    def remove_layer(self, index: int) -> Optional[CakeLayer]:
        """Remove layer from any position (list behavior)"""
        if 0 <= index < len(self.layers):
            return self.layers.pop(index)
        return None
    
    def top_layer(self) -> Optional[CakeLayer]:
        """Get top layer without removing it"""
        return self.layers[-1] if self.layers else None
    
    def is_empty(self) -> bool:
        return len(self.layers) == 0
    
    def is_full(self) -> bool:
        return len(self.layers) == self.max_capacity
    
    def is_complete(self) -> bool:
        """All layers same color and filled to capacity"""
        if not self.is_full():
            return False
        first_color = self.layers[0].color if self.layers else None
        return all(layer.color == first_color for layer in self.layers)
    
    def __str__(self):
        return " ".join(str(layer) for layer in self.layers)

class CakeGame:
    def __init__(self, width: int = 5, height: int = 5, max_capacity: int = 6):
        self.width = width
        self.height = height
        self.max_capacity = max_capacity
        self.tubes: List[Tube] = []
        self.moves = 0
        self.selected_tube = None
        self.selected_layer_pos = None
    
    def initialize_level(self, level_file: str):
        """Load level from file"""
        self.tubes = []
        self.moves = 0
        
        try:
            with open(level_file, 'r') as f:
                for line in f:
                    tube = Tube(self.max_capacity)
                    layers = line.strip().split()
                    for layer_str in layers:
                        color = layer_str[0].lower()
                        size = int(layer_str[1:])
                        tube.add_layer(CakeLayer(color, size))
                    self.tubes.append(tube)
        except FileNotFoundError:
            print(f"Level file {level_file} not found. Starting empty level.")
            self.tubes = [Tube(self.max_capacity) for _ in range(self.width * self.height)]
    
    def move_layer(self, from_idx: int, layer_pos: int, to_idx: int) -> bool:
        """Move layer from one tube to another"""
        if from_idx == to_idx:
            return False
        if not (0 <= from_idx < len(self.tubes) and 0 <= to_idx < len(self.tubes)):
            return False
            
        from_tube = self.tubes[from_idx]
        to_tube = self.tubes[to_idx]
        
        layer = from_tube.remove_layer(layer_pos)
        if layer is None:
            return False
            
        if to_tube.add_layer(layer):
            self.moves += 1
            return True
        else:
            # Revert if move failed
            from_tube.layers.insert(layer_pos, layer)
            return False
    
    def is_solved(self) -> bool:
        """Check if all tubes are complete or empty"""
        return all(tube.is_complete() or tube.is_empty() for tube in self.tubes)
    
    def get_state_hash(self) -> str:
        """Get unique string representation of current state"""
        return "|".join(str(tube) for tube in self.tubes)
    
    def get_adjacent_tubes(self, tube_idx: int) -> List[int]:
        """Get indices of adjacent tubes (up, down, left, right)"""
        row = tube_idx // self.width
        col = tube_idx % self.width
        adjacent = []
        
        if row > 0:
            adjacent.append(tube_idx - self.width)  # Up
        if row < self.height - 1:
            adjacent.append(tube_idx + self.width)  # Down
        if col > 0:
            adjacent.append(tube_idx - 1)            # Left
        if col < self.width - 1:
            adjacent.append(tube_idx + 1)            # Right
            
        return adjacent