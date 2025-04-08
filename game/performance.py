import time
import psutil
import os
from collections import defaultdict
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Any, Optional


@dataclass
class AlgorithmPerformance:
    """Class to store algorithm performance metrics"""
    algorithm_name: str
    states_explored: int
    states_generated: int
    solution_length: int
    solution_score: int
    time_seconds: float
    max_memory_mb: float
    solution_path: List
    solution_found: bool
    level_name: str
    
    def to_dict(self):
        return asdict(self)


class PerformanceTracker:
    """Class to track algorithm performance metrics"""
    def __init__(self, algorithm_name: str, level_name: str):
        self.algorithm_name = algorithm_name
        self.level_name = level_name
        self.start_time = None
        self.end_time = None
        self.time_seconds = 0
        self.states_explored = 0
        self.states_generated = 0
        self.max_memory = 0
        self.process = psutil.Process(os.getpid())
        self.solution_path = []
        self.solution_score = 0
        self.solution_found = False
        
    def start(self):
        """Start tracking performance"""
        self.start_time = time.time()
        self.update_memory()
        
    def stop(self, solution_path=None, solution_score=0, solution_found=False):
        """Stop tracking performance"""
        self.end_time = time.time()
        self.time_seconds = self.end_time - self.start_time
        self.update_memory()
        self.solution_path = solution_path or []
        self.solution_score = solution_score
        self.solution_found = solution_found
        
    def update_memory(self):
        """Update memory usage statistics"""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)  # Convert to MB
        self.max_memory = max(self.max_memory, memory_mb)
        
    def increment_explored(self, count=1):
        """Increment number of states explored"""
        self.states_explored += count
        self.update_memory()
        
    def increment_generated(self, count=1):
        """Increment number of states generated"""
        self.states_generated += count
        self.update_memory()
        
    def get_performance_data(self) -> AlgorithmPerformance:
        """Get all performance metrics as a data class"""
        return AlgorithmPerformance(
            algorithm_name=self.algorithm_name,
            states_explored=self.states_explored,
            states_generated=self.states_generated,
            solution_length=len(self.solution_path),
            solution_score=self.solution_score,
            time_seconds=self.time_seconds,
            max_memory_mb=self.max_memory,
            solution_path=self.solution_path,
            solution_found=self.solution_found,
            level_name=self.level_name
        )
        
    def print_summary(self):
        """Print a summary of the performance metrics"""
        print(f"\n===== {self.algorithm_name} Performance =====")
        print(f"Level: {self.level_name}")
        print(f"Time: {self.time_seconds:.4f} seconds")
        print(f"States explored: {self.states_explored}")
        print(f"States generated: {self.states_generated}")
        print(f"Maximum memory: {self.max_memory:.2f} MB")
        print(f"Solution length: {len(self.solution_path)}")
        print(f"Solution score: {self.solution_score}")
        print(f"Solution found: {'Yes' if self.solution_found else 'No'}")
        print("====================================\n")
        
    def save_to_file(self, directory="results"):
        """Save performance data to a JSON file"""
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Create filename based on algorithm, level, and timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{directory}/{self.algorithm_name}_{self.level_name}_{timestamp}.json"
        
        # Convert to dictionary and save
        data = self.get_performance_data().to_dict()
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Performance data saved to {filename}")
        return filename


class AlgorithmComparer:
    """Class to compare performance of multiple algorithms"""
    def __init__(self):
        self.results = []
        
    def add_result(self, performance: AlgorithmPerformance):
        """Add a performance result to the comparison"""
        self.results.append(performance)
        
    def print_comparison(self):
        """Print a comparison of all algorithms"""
        if not self.results:
            print("No results to compare")
            return
            
        print("\n====== Algorithm Comparison ======")
        print(f"Level: {self.results[0].level_name}")
        print("\nMetric         | " + " | ".join(f"{r.algorithm_name:10}" for r in self.results))
        print("-" * (15 + 14 * len(self.results)))
        
        # Time
        print(f"Time (s)       | " + " | ".join(f"{r.time_seconds:10.4f}" for r in self.results))
        
        # States
        print(f"States Explored | " + " | ".join(f"{r.states_explored:10}" for r in self.results))
        print(f"States Generated| " + " | ".join(f"{r.states_generated:10}" for r in self.results))
        
        # Memory
        print(f"Memory (MB)     | " + " | ".join(f"{r.max_memory_mb:10.2f}" for r in self.results))
        
        # Solution
        print(f"Solution Length | " + " | ".join(f"{r.solution_length:10}" for r in self.results))
        print(f"Solution Score  | " + " | ".join(f"{r.solution_score:10}" for r in self.results))
        print(f"Solution Found  | " + " | ".join(f"{'Yes':10}" if r.solution_found else f"{'No':10}" for r in self.results))
        print("==============================\n")
        
    def save_to_file(self, directory="results"):
        """Save comparison data to a JSON file"""
        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)
        
        # Create filename based on level and timestamp
        level_name = self.results[0].level_name if self.results else "unknown"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{directory}/comparison_{level_name}_{timestamp}.json"
        
        # Convert to list of dictionaries and save
        data = [result.to_dict() for result in self.results]
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Comparison data saved to {filename}")
        return filename