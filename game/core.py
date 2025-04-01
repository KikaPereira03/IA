import pygame
from typing import List, Tuple, Optional
from dataclasses import dataclass
import os

@dataclass
class CakeLayer:
    color: str
    size: int

    def __str__(self):
        return f"{self.color}{self.size}"

class Tube:
    def __init__(self, max_capacity: int = 6):
        self.layers: List[CakeLayer] = []
        self.max_capacity = max_capacity
    
    def can_add(self, layer: CakeLayer) -> bool:
        return (len(self.layers) < self.max_capacity and 
                (self.is_empty() or self.top_layer().color == layer.color))
    
    def add_layer(self, layer: CakeLayer) -> bool:
        if self.can_add(layer):
            self.layers.append(layer)
            return True
        return False
    
    def add_layers_any_color(self, layers: List[CakeLayer]):
        """Adiciona várias camadas ao tubo sem verificar cores."""
        for layer in layers:
            if len(self.layers) < self.max_capacity:
                self.layers.append(layer)


    def remove_layer(self, index: int) -> Optional[CakeLayer]:
        if -len(self.layers) <= index < len(self.layers):
            return self.layers.pop(index)
        return None

    
    def top_layer(self) -> Optional[CakeLayer]:
        return self.layers[-1] if self.layers else None
    
    def is_empty(self) -> bool:
        return len(self.layers) == 0
    
    def is_full(self) -> bool:
        return len(self.layers) == self.max_capacity
    
    def is_complete(self) -> bool:
        if not self.is_full():
            return False
        first_color = self.layers[0].color if self.layers else None
        return all(layer.color == first_color for layer in self.layers)
    
    def __str__(self):
        return " ".join(str(layer) for layer in self.layers)

class CakeGame:
    def __init__(self, width: int = 5, height: int = 4, max_capacity: int = 6):
        self.width = width
        self.height = height
        self.max_capacity = max_capacity
        self.tubes: List[Tube] = [Tube(max_capacity) for _ in range(width * height)]
        self.moves = 0
        self.selected_tube = None
        self.selected_layer_pos = None
    
    def initialize_level(self, level_file: str):
        self.tubes = [Tube(self.max_capacity) for _ in range(self.width * self.height)]
        self.moves = 0
        
        try:
            with open(level_file, 'r') as f:
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    
                    parts = line.strip().split(':')
                    if len(parts) < 2:
                        continue
                        
                    tube_idx, layers_str = parts[0], parts[1]
                    tube = self.tubes[int(tube_idx)]
                    
                    for layer_str in layers_str.split():
                        if not layer_str:
                            continue
                        color = layer_str[0].upper()
                        size = int(layer_str[1:]) if len(layer_str) > 1 else 1
                        tube.add_layer(CakeLayer(color, size))
        except FileNotFoundError:
            print(f"Error: Level file {level_file} not found")
    
    def move_layer(self, from_idx: int, layer_pos: int, to_idx: int) -> bool:
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
            from_tube.layers.insert(layer_pos, layer)
            return False
    
    def is_solved(self) -> bool:
        return all(tube.is_complete() or tube.is_empty() for tube in self.tubes)
    
    def get_state_hash(self) -> str:
        return "|".join(str(tube) for tube in self.tubes)
    
    def get_adjacent_tubes(self, tube_idx: int) -> List[int]:
        row = tube_idx // self.width
        col = tube_idx % self.width
        adjacent = []
        
        if row > 0:
            adjacent.append(tube_idx - self.width)
        if row < self.height - 1:
            adjacent.append(tube_idx + self.width)
        if col > 0:
            adjacent.append(tube_idx - 1)
        if col < self.width - 1:
            adjacent.append(tube_idx + 1)
            
        return adjacent
    
    def merge_adjacent_layers(self, tube_idx: int):
            main_tube = self.tubes[tube_idx]
            if main_tube.is_full() or main_tube.is_empty():
                return

            top_color = main_tube.top_layer().color
            adjacent_idxs = self.get_adjacent_tubes(tube_idx)

            for adj_idx in adjacent_idxs:
                adj_tube = self.tubes[adj_idx]
                while not main_tube.is_full() and not adj_tube.is_empty():
                    adj_top = adj_tube.top_layer()
                    if adj_top.color == top_color:
                        main_tube.add_layer(adj_tube.remove_layer(-1))
                    else:
                        break

    # ✅ Função nova para mover todas as fatias
    def move_all_layers(self, from_idx: int, to_idx: int) -> bool:
        """Move todas as fatias possíveis do tubo origem para o tubo destino."""
        if from_idx == to_idx:
            return False

        from_tube = self.tubes[from_idx]
        to_tube = self.tubes[to_idx]

        if from_tube.is_empty() or to_tube.is_full():
            return False

        layers_to_move = from_tube.layers[::-1]
        space_available = to_tube.max_capacity - len(to_tube.layers)

        layers_to_transfer = []
        for layer in layers_to_move:
            if len(layers_to_transfer) < space_available:
                layers_to_transfer.append(layer)
            else:
                break

        for layer in reversed(layers_to_transfer):
            to_tube.add_layer(layer)

        from_tube.layers = from_tube.layers[:-len(layers_to_transfer)]
        self.moves += 1
        return True
    
        