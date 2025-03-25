"""
Game progress tracking for Cake Sort Puzzle.
Handles saving/loading player progress, level completion, and rewards.
"""

import json
import os

class GameProgress:
    def __init__(self, save_file="game/data/progress.json"):
        self.save_file = save_file
        self.current_level = 1
        self.max_level = 1
        self.stars = {}  # Level -> stars earned (1-3)
        self.theme = "classic"
        self.coins = 0
        self.unlocked_themes = ["classic"]  # Themes the player has unlocked
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_file), exist_ok=True)
        
        self.load()
    
    def load(self):
        """Load progress from save file"""
        try:
            with open(self.save_file, 'r') as f:
                data = json.load(f)
                self.current_level = data.get('current_level', 1)
                self.max_level = data.get('max_level', 1)
                self.stars = data.get('stars', {})
                self.theme = data.get('theme', "classic")
                self.coins = data.get('coins', 0)
                self.unlocked_themes = data.get('unlocked_themes', ["classic"])
        except (FileNotFoundError, json.JSONDecodeError):
            # Default values already set
            self.save()  # Create the file with default values
    
    def save(self):
        """Save progress to file"""
        data = {
            'current_level': self.current_level,
            'max_level': self.max_level,
            'stars': self.stars,
            'theme': self.theme,
            'coins': self.coins,
            'unlocked_themes': self.unlocked_themes
        }
        try:
            with open(self.save_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving progress: {e}")
    
    def complete_level(self, level, moves, par_moves):
        """
        Mark a level as complete and calculate stars earned
        
        Args:
            level: Level number
            moves: Number of moves taken to complete
            par_moves: Par (target) number of moves for 3 stars
            
        Returns:
            Number of stars earned (1-3)
        """
        # Calculate stars based on moves compared to par
        if moves <= par_moves:
            stars = 3
        elif moves <= par_moves * 1.5:
            stars = 2
        else:
            stars = 1
            
        # Update progress
        self.stars[str(level)] = max(self.stars.get(str(level), 0), stars)
        if level == self.max_level:
            self.max_level += 1
        
        # Award coins
        self.coins += stars * 10
        self.save()
        
        return stars
    
    def unlock_theme(self, theme_name):
        """Unlock a new theme if the player has enough coins"""
        theme_costs = {
            "pastel": 100,
            "chocolate": 200,
            "frosting": 300
        }
        
        if theme_name in self.unlocked_themes:
            return True, "Theme already unlocked"
        
        cost = theme_costs.get(theme_name, 0)
        if self.coins >= cost:
            self.coins -= cost
            self.unlocked_themes.append(theme_name)
            self.save()
            return True, f"Unlocked {theme_name} theme!"
        else:
            return False, f"Not enough coins. Need {cost - self.coins} more."
    
    def get_total_stars(self):
        """Get total number of stars earned across all levels"""
        return sum(self.stars.values())