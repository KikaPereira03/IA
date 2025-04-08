import time
import os
import tracemalloc
from datetime import datetime

class MetricsCollector:
    """Class to collect performance metrics for different algorithms."""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset all metrics to initial values."""
        self.start_time = None
        self.end_time = None
        self.states_generated = 0
        self.steps_taken = 0
        self.peak_memory = 0
        self.score = 0
        self.level_name = ""
        self.algorithm_name = ""
        
    def start_tracking(self, level_name, algorithm_name):
        """Start performance tracking."""
        self.reset()
        self.level_name = level_name
        self.algorithm_name = algorithm_name
        tracemalloc.start()
        self.start_time = time.time()
        print(f"Starting metrics tracking for {level_name} with {algorithm_name}")
        
    def stop_tracking(self, final_score):
        """Stop performance tracking and record final metrics."""
        self.end_time = time.time()
        self.score = final_score
        _, self.peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
    def increment_states(self, count=1):
        """Increment the number of states generated."""
        self.states_generated += count
        
    def increment_steps(self, count=1):
        """Increment the number of steps taken."""
        self.steps_taken += count
        
    def get_elapsed_time(self):
        """Get the elapsed time in seconds."""
        if self.start_time is None:
            return 0
        end = self.end_time if self.end_time is not None else time.time()
        return end - self.start_time
        
    def print_summary(self):
        """Print a summary of the metrics."""
        elapsed = self.get_elapsed_time()
        
        print("\nBot finished.")
        print(f"Level: {self.level_name}")
        print(f"Algorithm: {self.algorithm_name.upper()}")
        print(f"Final Score: {self.score}")
        print(f"States Generated: {self.states_generated}")
        print(f"Steps Taken: {self.steps_taken}")
        print(f"Time Taken: {elapsed:.2f} seconds")
        print(f"Peak Memory Used: {self.peak_memory / 1024:.2f} KB")
        
        # Save to file
        self.save_results_to_file()
        
    def save_results_to_file(self):
        """Save the metrics to a file."""
        # Ensure results directory exists
        os.makedirs("results", exist_ok=True)
        
        result_path = f"results/{self.level_name}_{self.algorithm_name}.txt"
        with open(result_path, "w") as f:
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Level: {self.level_name}\n")
            f.write(f"Algorithm: {self.algorithm_name.upper()}\n")
            f.write(f"Final Score: {self.score}\n")
            f.write(f"States Generated: {self.states_generated}\n")
            f.write(f"Steps Taken: {self.steps_taken}\n")
            f.write(f"Time Taken: {self.get_elapsed_time():.2f} seconds\n")
            f.write(f"Peak Memory Used: {self.peak_memory / 1024:.2f} KB\n")
        
        print(f"Results saved to: {result_path}")
        
    def get_metrics_dict(self):
        """Return the metrics as a dictionary."""
        return {
            "level_name": self.level_name,
            "algorithm": self.algorithm_name,
            "score": self.score,
            "states_generated": self.states_generated,
            "steps_taken": self.steps_taken,
            "time_taken": self.get_elapsed_time(),
            "peak_memory_kb": self.peak_memory / 1024
        }