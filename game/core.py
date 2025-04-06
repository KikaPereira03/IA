import pygame
from typing import List, Tuple, Optional
from game.utils import load_level_file
from dataclasses import dataclass
import os

@dataclass
class CakeSlice:
    color: str # Color identifier (e.g. 'R', 'G', 'B')
    size: int

    def __str__(self):
        return f"{self.color}{self.size}"

class Plate:
    def __init__(self, max_capacity: int = 6):
        self.slices: List[CakeSlice] = []
        self.max_capacity = max_capacity 

    def __str__(self):
        return " ".join(str(layer) for layer in self.slices)

class CakeGame:
    # Core game logic
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


    # Load level from file: plates, queue, score requirement
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

                if line.lower().startswith("score:"):
                    self.required_score = int(line.split(":")[1].strip())
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

    
    def get_state_hash(self) -> str:
        return "|".join(str(plate) for plate in self.plates)
    
    def sort_plate_by_color(self, plate):
        plate.slices.sort(key=lambda slice: slice.color)
    

    # Get indexes of plates adjacent to the given plate
    def get_adjacent_plates(self, idx: int) -> List[int]:
        row = idx // self.width
        col = idx % self.width
        neighbors = []
        if row > 0:
            neighbors.append(idx - self.width)  # Up
        if row < self.height - 1:
            neighbors.append(idx + self.width)  # Down
        if col > 0:
            neighbors.append(idx - 1)  # Left
        if col < self.width - 1:
            neighbors.append(idx + 1)  # Right
        return neighbors


    def is_goal_state(self):
        for idx, plate in enumerate(self.plates):
            if not plate.slices:
                continue  
                
            first_color = plate.slices[0].color
            if any(s.color != first_color for s in plate.slices):
                return False
                
        return True


    # Specialized greedy algorithm designed for the specific mechanics of our cake sort game.

    # Main algorithm to consolidate same-colored slices
    # 1. Find common colors between adjacent plates
    # 2. Merge colors to prioritize consolidation
    # 3. Handle mixed plates by moving minority colors
    def merge_all_possible_slices(self):
        from collections import Counter
    
        merges_occurred = False
        
        while True:
            merged_this_round = False
            
            # PHASE 1: Check all adjacent plate pairs for color consolidation
            for plate_idx, plate in enumerate(self.plates):
                # Skip empty plates
                if not plate.slices:
                    continue
                
                # Get all adjacent plates
                adjacent_plates = self.get_adjacent_plates(plate_idx)
                
                # For each adjacent plate, check for common colors
                for adj_idx in adjacent_plates:
                    adj_plate = self.plates[adj_idx]
                    
                    if not adj_plate.slices:
                        continue
                    
                    # Find colors that appear in both plates
                    plate_colors = Counter([s.color for s in plate.slices])
                    adj_colors = Counter([s.color for s in adj_plate.slices])
                    
                    # Check each color in the plate
                    for color, count in plate_colors.items():
                        # Skip if color doesn't appear in adjacent plate
                        if color not in adj_colors:
                            continue
                            
                        # Determine which plate has more of this color
                        if adj_colors[color] > count:
                            # Adjacent plate has more, move from plate to adjacent
                            moved = self._move_color_between_plates(plate_idx, adj_idx, color)
                            if moved:
                                merged_this_round = True
                                merges_occurred = True
                                break
                        elif count > adj_colors[color]:
                            # This plate has more, move from adjacent to plate
                            moved = self._move_color_between_plates(adj_idx, plate_idx, color)
                            if moved:
                                merged_this_round = True
                                merges_occurred = True
                                break
                        elif count == adj_colors[color] and count > 0: 
                            # Equal counts - plate index as tiebreaker
                            if plate_idx < adj_idx:
                                moved = self._move_color_between_plates(adj_idx, plate_idx, color)
                            else:
                                moved = self._move_color_between_plates(plate_idx, adj_idx, color)
                            if moved:
                                merged_this_round = True
                                merges_occurred = True
                                break
                    
                    if merged_this_round:
                        break
                        
                if merged_this_round:
                    break
            

            if not merged_this_round:

                # PHASE 2: Handle mixed color plates
                mixed_plates = []
                for idx, plate in enumerate(self.plates):
                    if not plate.slices:
                        continue
                        
                    colors = set(s.color for s in plate.slices)
                    if len(colors) > 1:
                        mixed_plates.append(idx)
                
                if not mixed_plates:
                    break
                    
                for plate_idx in mixed_plates:
                    plate = self.plates[plate_idx]
                    color_counts = Counter([s.color for s in plate.slices])
                    
                    # Find majority and minority colors
                    colors_by_count = color_counts.most_common()
                    majority_color = colors_by_count[0][0]
                    
                    # Try to move minority colors out first
                    moved_minority = False
                    for color, _ in colors_by_count[1:]:
                        for adj_idx in self.get_adjacent_plates(plate_idx):
                            adj_plate = self.plates[adj_idx]
                            
                            if len(adj_plate.slices) >= adj_plate.max_capacity:
                                continue
                                
                            # If adjacent plate has this color, try to move
                            if any(s.color == color for s in adj_plate.slices):
                                if self._move_color_between_plates(plate_idx, adj_idx, color):
                                    moved_minority = True
                                    merged_this_round = True
                                    merges_occurred = True
                                    break

                        if moved_minority:
                            break
                    
                    if moved_minority:
                        break
                        
                    if not moved_minority:
                        majority_count = color_counts[majority_color]
                        
                        for adj_idx in self.get_adjacent_plates(plate_idx):
                            adj_plate = self.plates[adj_idx]
                            
                            adj_count = sum(1 for s in adj_plate.slices if s.color == majority_color)
                            
                            if adj_count > majority_count and len(adj_plate.slices) < adj_plate.max_capacity:
                                if self._move_color_between_plates(plate_idx, adj_idx, majority_color):
                                    merged_this_round = True
                                    merges_occurred = True
                                    break
                    
                    if merged_this_round:
                        break

            if not merged_this_round:
                break
        
        # Check for completed plates
        self._check_for_completed_plates()
        
        return merges_occurred


    # Move slices of specified color between plates
    def _move_color_between_plates(self, from_idx, to_idx, color):
        from_plate = self.plates[from_idx]
        to_plate = self.plates[to_idx]
        
        color_indices = [i for i, s in enumerate(from_plate.slices) if s.color == color]
        
        if not color_indices:
            return False
        
        available_space = to_plate.max_capacity - len(to_plate.slices)
        
        if available_space <= 0:
            return False
        
        moved = False
        for idx in sorted(color_indices, reverse=True)[:available_space]:
            slice_to_move = from_plate.slices[idx]
            to_plate.slices.append(slice_to_move)
            del from_plate.slices[idx]
            moved = True
            
            color_indices = [i for i, s in enumerate(from_plate.slices) if s.color == color]
        
        if moved and not from_plate.slices and hasattr(self, 'ui_callback') and self.ui_callback:
            self.ui_callback(from_idx)
        
        # Check for completions
        self._check_plate_completion(from_idx)
        self._check_plate_completion(to_idx)

        self.sort_plate_by_color(self.plates[from_idx])
        self.sort_plate_by_color(self.plates[to_idx])

        return moved


    # Check all plates for completion (6 same-color slices)
    def _check_for_completed_plates(self):
        for idx, plate in enumerate(self.plates):
            self._check_plate_completion(idx)


    def _check_plate_completion(self, plate_idx):
        plate = self.plates[plate_idx]
        
        # Skip empty plates or plates with wrong number of slices
        if not plate.slices or len(plate.slices) != 6:
            return False
            
        # Check if all slices are the same color
        first_color = plate.slices[0].color
        if all(s.color == first_color for s in plate.slices):
            # Award points
            self.score += len(plate.slices) * 10
            
            # Trigger animation
            if hasattr(self, 'ui_callback') and self.ui_callback:
                self.ui_callback(plate_idx)
                
            # Clear the plate
            plate.slices = []
            return True
        
        return False