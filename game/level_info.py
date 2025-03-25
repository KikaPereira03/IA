"""
Level information and management for Cake Sort Puzzle.
Handles loading levels and storing metadata about each level.
"""

import os
from typing import Dict, List, Tuple, Optional

class LevelInfo:
    def __init__(self, level_num, difficulty, par_moves, width, height):
        self.level_num = level_num
        self.difficulty = difficulty
        self.par_moves = par_moves
        self.width = width
        self.height = height

class LevelManager:
    def __init__(self, levels_dir="game/levels"):
        self.levels_dir = levels_dir
        self.levels = {}  # Dictionary mapping level numbers to LevelInfo objects
        self.load_level_metadata()
    
    def load_level_metadata(self):
        """Load metadata for all level files"""
        # Create levels directory if it doesn't exist
        os.makedirs(self.levels_dir, exist_ok=True)
        
        try:
            for filename in os.listdir(self.levels_dir):
                if filename.endswith(".txt") and filename.startswith("level"):
                    level_path = os.path.join(self.levels_dir, filename)
                    
                    try:
                        # Extract level number from filename (e.g., "level1.txt" -> 1)
                        level_num = int(filename.split("level")[1].split(".")[0])
                        
                        # Extract metadata from level file
                        with open(level_path, 'r') as f:
                            lines = f.readlines()
                            
                            # Parse header comments for metadata
                            difficulty = "Medium"
                            par_moves = 10
                            width = 4
                            height = 3
                            
                            for line in lines:
                                line = line.strip()
                                if line.startswith("# Difficulty:"):
                                    difficulty = line.split(":")[1].strip()
                                elif line.startswith("# Moves:"):
                                    par_moves = int(line.split(":")[1].strip())
                                elif line.startswith("width:"):
                                    width = int(line.split(":")[1].strip())
                                elif line.startswith("height:"):
                                    height = int(line.split(":")[1].strip())
                            
                            self.levels[level_num] = LevelInfo(
                                level_num, difficulty, par_moves, width, height
                            )
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing level file {filename}: {e}")
        except Exception as e:
            print(f"Error loading level data: {e}")
            
        # If no levels found, create a default level
        if not self.levels:
            self.create_default_levels()
    
    def create_default_levels(self):
        """Create default levels if none exist"""
        # Make sure the levels directory exists
        os.makedirs(self.levels_dir, exist_ok=True)
        
        # Create level 1 (Easy)
        level1_path = os.path.join(self.levels_dir, "level1.txt")
        if not os.path.exists(level1_path):
            with open(level1_path, 'w') as f:
                f.write("# Level 1\n")
                f.write("# Difficulty: Easy\n")
                f.write("# Moves: 8\n")
                f.write("width: 4\n")
                f.write("height: 3\n")
                f.write("0: R2 R2 R2\n")
                f.write("1: G3 G3 G3\n")
                f.write("2: B1 B1 B1\n")
                f.write("3: Y4 Y4 Y4\n")
                f.write("4: \n")
                f.write("5: \n")
            
            self.levels[1] = LevelInfo(1, "Easy", 8, 4, 3)
        
        # Create level 2 (Medium)
        level2_path = os.path.join(self.levels_dir, "level2.txt")
        if not os.path.exists(level2_path):
            with open(level2_path, 'w') as f:
                f.write("# Level 2\n")
                f.write("# Difficulty: Medium\n")
                f.write("# Moves: 12\n")
                f.write("width: 4\n")
                f.write("height: 3\n")
                f.write("0: R1 G2 B3\n")
                f.write("1: G2 B3 R1\n")
                f.write("2: B3 R1 G2\n")
                f.write("3: Y4 Y4 Y4\n")
                f.write("4: \n")
                f.write("5: \n")
            
            self.levels[2] = LevelInfo(2, "Medium", 12, 4, 3)
        
        # Create level 3 (Hard)
        level3_path = os.path.join(self.levels_dir, "level3.txt")
        if not os.path.exists(level3_path):
            with open(level3_path, 'w') as f:
                f.write("# Level 3\n")
                f.write("# Difficulty: Hard\n")
                f.write("# Moves: 20\n")
                f.write("width: 5\n")
                f.write("height: 4\n")
                f.write("0: R2 G3 B1 Y4\n")
                f.write("1: P5 O6 M7 C8\n")
                f.write("2: Y4 B1 G3 R2\n")
                f.write("3: C8 M7 O6 P5\n")
                f.write("4: G3 R2 Y4 B1\n")
                f.write("5: M7 P5 C8 O6\n")
                f.write("6: \n")
                f.write("7: \n")
            
            self.levels[3] = LevelInfo(3, "Hard", 20, 5, 4)
    
    def get_level_info(self, level_num):
        """Get information about a specific level"""
        if level_num in self.levels:
            return self.levels[level_num]
        return None
    
    def get_level_count(self):
        """Get the total number of available levels"""
        return len(self.levels)
    
    def get_level_path(self, level_num):
        """Get the file path for a level"""
        return os.path.join(self.levels_dir, f"level{level_num}.txt")
    
    def create_level(self, level_num, difficulty, par_moves, width, height, tube_data):
        """Create a new level file"""
        level_path = os.path.join(self.levels_dir, f"level{level_num}.txt")
        
        # Create levels directory if it doesn't exist
        os.makedirs(self.levels_dir, exist_ok=True)
        
        with open(level_path, 'w') as f:
            f.write(f"# Level {level_num}\n")
            f.write(f"# Difficulty: {difficulty}\n")
            f.write(f"# Moves: {par_moves}\n")
            f.write(f"width: {width}\n")
            f.write(f"height: {height}\n")
            
            # Write tube data
            for tube_idx, layers in tube_data.items():
                f.write(f"{tube_idx}: {' '.join(layers)}\n")
        
        # Update level info
        self.levels[level_num] = LevelInfo(level_num, difficulty, par_moves, width, height)
        return True