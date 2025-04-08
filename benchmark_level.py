#TO RUN METRICS
#python benchmark_level.py game/levels/level1.txt --algorithm 'greedy'
#python benchmark_level.py game/levels/level1.txt --algorithm 'a*'

#!/usr/bin/env python3
import argparse
import os
import re
import pygame
import time
import sys

# Hide pygame welcome message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

class SingleLevelGameUI:
    """Modified CakeGameUI that only runs a single level"""
    def __init__(self, original_ui_class, level_file, algorithm):
        self.original_class = original_ui_class
        self.level_file = level_file
        self.algorithm = algorithm
        
    def create_instance(self):
        """Create a game instance that doesn't proceed to next level"""
        from game.metrics_collector import MetricsCollector
        from game.solver import metrics
        
        # Reset metrics for this run
        metrics.reset()
        
        # Extract level name from file path
        match = re.search(r'level(\d+)', self.level_file)
        level_name = f"level{match.group(1)}" if match else os.path.basename(self.level_file)
        
        # Start tracking metrics
        metrics.start_tracking(level_name, self.algorithm)
        
        # Create the game instance
        instance = self.original_class(level_file=self.level_file, bot_algorithm=None)
        
        # Override the level switch method to prevent changing levels
        original_level_switch = instance.game.ui_level_switch
        def no_level_switch(level_number):
            print(f"Level complete with score: {instance.game.score}")
            # Don't change to the next level
            return False
        
        # Apply our override
        instance.game.ui_level_switch = no_level_switch
        
        return instance
    
    def run(self):
        """Run the level with metrics tracking"""
        from game.solver import metrics, greedy_bot_solver, astar_bot_solver
        from game.models import CakeSlice
        
        instance = self.create_instance()
        
        # Get the appropriate solver
        solver_map = {
            'greedy': greedy_bot_solver,
            'a*': astar_bot_solver,
        }
        solver = solver_map.get(self.algorithm.lower())
        
        # Track steps for this run
        steps_taken = 0
        
        # Run the solver manually (don't use instance.run_solver_with_algorithm)
        print(f"Bot running ({self.algorithm})...")
        
        while instance.game.queue_data:
            queue = list(enumerate(instance.game.queue_data[:3]))
            
            # Handle the difference in parameters between solvers
            if self.algorithm.lower() == 'greedy':
                moves = solver(instance.game.plates, queue, apply_moves=True, game_instance=instance.game)
            else:
                # For A* and other solvers that don't take game_instance
                moves = solver(instance.game.plates, queue, apply_moves=True)
            
            if not moves:
                print("No valid moves.")
                break
                
            q_index, g_index = moves[0]
            if q_index == -1:
                print("Invalid move.")
                break
                
            steps_taken += 1
            metrics.increment_steps()
            
            # Apply the move
            plate = instance.game.queue_data.pop(q_index)
            
            instance.queue_plates = [
                [CakeSlice(color, 1) for color in reversed(p)]
                for p in instance.game.queue_data[:instance.queue_slots]
            ]
            
            print(f"Move: placed queue {q_index} → grid {g_index}")
            instance.game.plates[g_index].slices.extend([CakeSlice(color, 1) for color in plate])
            instance.game._check_plate_completion(g_index)
            instance.game.merge_all_possible_slices()
            
            # Check if level is completed (but don't change levels)
            if instance.game.score >= getattr(instance.game, 'required_score', 100):
                print(f"Level completed with score: {instance.game.score}")
                break
                
            # Draw the state
            instance.draw()
            pygame.time.delay(100)
        
        # Save final metrics
        metrics.stop_tracking(instance.game.score)
        metrics.print_summary()
        
        print("Benchmark complete!")
        return True

def benchmark_level(level_file, algorithm, visualize=False):
    """Run a benchmark for a specific algorithm on a specific level"""
    try:
        # Import required components
        from main import CakeGameUI
        from game.metrics_collector import MetricsCollector
        from game.solver import metrics
        
        # Initialize pygame
        pygame.init()
        if visualize:
            # Use normal display
            pygame.display.set_mode((1000, 800))
        else:
            # Run in headless mode
            pygame.display.set_mode((1, 1))
        
        # Extract level name from file path
        match = re.search(r'level(\d+)', level_file)
        level_name = f"level{match.group(1)}" if match else os.path.basename(level_file)
        
        print(f"Benchmarking {algorithm} on {level_name}...")
        
        # Create a single-level game instance with the algorithm
        game_ui = SingleLevelGameUI(CakeGameUI, level_file, algorithm)
        
        # Run the bot
        game_ui.run()
        
        print("\nBenchmark complete.")
        
    except Exception as e:
        print(f"Error during benchmark: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up pygame
        pygame.quit()

def main():
    parser = argparse.ArgumentParser(description='Benchmark a specific algorithm on a level')
    parser.add_argument('level', help='Level file to benchmark (e.g., game/levels/level1.txt)')
    parser.add_argument('--algorithm', default='greedy', choices=['greedy', 'a*'], 
                        help='Algorithm to benchmark (default: greedy)')
    parser.add_argument('--visualize', action='store_true', 
                        help='Show game window during benchmark')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.level):
        print(f"Error: Level file '{args.level}' not found.")
        return 1
    
    benchmark_level(args.level, args.algorithm, args.visualize)
    return 0

if __name__ == "__main__":
    sys.exit(main())