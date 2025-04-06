import pygame
from typing import List, Tuple, Optional
from game.utils import load_level_file
from dataclasses import dataclass
import os

@dataclass
class CakeSlice:
    color: str
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
                    # Ensure the required_score is loaded properly for each level
                    self.required_score = int(line.split(":")[1].strip())
                    print(f"Required score for this level: {self.required_score}")  # Debug print to confirm loading
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
    
    def get_top_group(self, plate):
        if not plate.slices:
            return []
        top_color = plate.slices[-1].color
        group = []
        for s in reversed(plate.slices):
            if s.color == top_color:
                group.append(s)
            else:
                break
        return list(reversed(group))

    def is_valid_transfer(self, from_plate, to_plate, group):
        if not group:
            return False
        if len(to_plate.slices) + len(group) > to_plate.max_capacity:
            return False
        if not to_plate.slices:
            return True
        return to_plate.slices[-1].color == group[0].color
    
    def move_slices(self, from_idx, to_idx, count):
        group = self.plates[from_idx].slices[-count:]
        self.plates[to_idx].slices.extend(group)
        del self.plates[from_idx].slices[-count:]

    def is_goal_state(self):
        for plate in self.plates:
            if not plate.slices:
                continue
            first_color = plate.slices[0].color
            if any(s.color != first_color for s in plate.slices):
                return False
        return True

    def get_state_hash(self):
        return "|".join(".".join(s.color for s in plate.slices) for plate in self.plates)

    def merge_all_possible_slices(self):
        """
        Automatically merge cake slices between adjacent plates.
        First checks adjacency, then consolidates colors between adjacent plates.
        """
        from collections import Counter
        
        # Track whether any merges occurred
        merges_occurred = False
        
        # Process until no more merges are possible
        while True:
            # Flag to track if any merges happened in this iteration
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
                    
                    # Skip empty adjacent plates
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
                        elif count == adj_colors[color] and count > 0:  # ADD THIS BLOCK
                            # Equal counts - use plate index as tiebreaker
                            # Always move from higher index to lower index for consistency
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
            
            # If no consolidation happened, check for mixed plates
            if not merged_this_round:
                # PHASE 2: Handle mixed color plates
                mixed_plates = []
                for idx, plate in enumerate(self.plates):
                    if not plate.slices:
                        continue
                        
                    colors = set(s.color for s in plate.slices)
                    if len(colors) > 1:
                        mixed_plates.append(idx)
                
                # If no mixed plates, we're done
                if not mixed_plates:
                    break
                    
                # For each mixed plate
                for plate_idx in mixed_plates:
                    plate = self.plates[plate_idx]
                    color_counts = Counter([s.color for s in plate.slices])
                    
                    # Find majority and minority colors
                    colors_by_count = color_counts.most_common()
                    majority_color = colors_by_count[0][0]
                    
                    # Try to move minority colors out first
                    moved_minority = False
                    for color, _ in colors_by_count[1:]:  # Skip majority color
                        # First try adjacent plates that already have this color
                        for adj_idx in self.get_adjacent_plates(plate_idx):
                            adj_plate = self.plates[adj_idx]
                            
                            # Skip full plates
                            if len(adj_plate.slices) >= adj_plate.max_capacity:
                                continue
                                
                            # If adjacent plate has this color, try to move
                            if any(s.color == color for s in adj_plate.slices):
                                if self._move_color_between_plates(plate_idx, adj_idx, color):
                                    moved_minority = True
                                    merged_this_round = True
                                    merges_occurred = True
                                    break
                        
                        # If moved to an adjacent plate, break
                        if moved_minority:
                            break
                    
                    if moved_minority:
                        break
                        
                    # If couldn't move minority colors, try moving majority color
                    # to a plate that has more of it
                    if not moved_minority:
                        majority_count = color_counts[majority_color]
                        
                        for adj_idx in self.get_adjacent_plates(plate_idx):
                            adj_plate = self.plates[adj_idx]
                            
                            # Count this color in the adjacent plate
                            adj_count = sum(1 for s in adj_plate.slices if s.color == majority_color)
                            
                            # If adjacent plate has more of this color and has space
                            if adj_count > majority_count and len(adj_plate.slices) < adj_plate.max_capacity:
                                if self._move_color_between_plates(plate_idx, adj_idx, majority_color):
                                    merged_this_round = True
                                    merges_occurred = True
                                    break
                    
                    if merged_this_round:
                        break
            
            # If no merges happened this round, we're done
            if not merged_this_round:
                break
        
        # Check for completed plates
        self._check_for_completed_plates()
        
        return merges_occurred

    def _move_color_between_plates(self, from_idx, to_idx, color):
        """
        Moves slices of the specified color from one plate to another.
        Returns True if any slices were moved, False otherwise.
        """
        from_plate = self.plates[from_idx]
        to_plate = self.plates[to_idx]
        
        # Find indices of this color in the source plate
        color_indices = [i for i, s in enumerate(from_plate.slices) if s.color == color]
        
        # If no slices of this color, return False
        if not color_indices:
            return False
        
        # Calculate available space in the target plate
        available_space = to_plate.max_capacity - len(to_plate.slices)
        
        # If no space, return False
        if available_space <= 0:
            return False
        
        # Move slices (starting from the top to avoid index issues)
        moved = False
        for idx in sorted(color_indices, reverse=True)[:available_space]:
            slice_to_move = from_plate.slices[idx]
            to_plate.slices.append(slice_to_move)
            del from_plate.slices[idx]
            moved = True
            
            # Update indices after each move
            color_indices = [i for i, s in enumerate(from_plate.slices) if s.color == color]
        
        # Handle empty source plate
        if moved and not from_plate.slices and hasattr(self, 'ui_callback') and self.ui_callback:
            self.ui_callback(from_idx)
        
        # Check for completions
        self._check_plate_completion(from_idx)
        self._check_plate_completion(to_idx)

        self.sort_plate_by_color(self.plates[from_idx])
        self.sort_plate_by_color(self.plates[to_idx])

        
        return moved

    def _move_slice_between_plates(self, from_idx, to_idx, slice_idx):
        """
        Moves a single slice from one plate to another.
        Returns True if successful, False otherwise.
        """
        from_plate = self.plates[from_idx]
        to_plate = self.plates[to_idx]
        
        # Check if target plate has space
        if len(to_plate.slices) >= to_plate.max_capacity:
            return False
        
        # Get the slice and move it
        slice_to_move = from_plate.slices[slice_idx]
        to_plate.slices.append(slice_to_move)
        del from_plate.slices[slice_idx]
        
        # Check if source plate is now empty
        if not from_plate.slices and hasattr(self, 'ui_callback') and self.ui_callback:
            self.ui_callback(from_idx)
        
        # Check if either plate is now complete
        self._check_plate_completion(from_idx)
        self._check_plate_completion(to_idx)
        
        return True

    def _check_for_completed_plates(self):
        """Check all plates to see if any are completed (6 slices of same color)"""
        for idx, plate in enumerate(self.plates):
            self._check_plate_completion(idx)

    def _check_plate_completion(self, plate_idx):
        """Check if a specific plate is completed (6 slices of same color)"""
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