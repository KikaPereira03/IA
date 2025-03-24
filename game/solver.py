from .core import CakeGame, Tube
from typing import List, Tuple, Dict, Optional
import heapq
import time
from collections import deque

class GameSolver:
    def __init__(self, game: CakeGame):
        self.game = game
    
    def solve_bfs(self) -> Optional[List[Tuple[int, int, int]]]:
        """Breadth-First Search solver"""
        queue = deque()
        visited = set()
        parent = {}
        move_history = {}
        
        initial_state = self.game.get_state_hash()
        queue.append(initial_state)
        visited.add(initial_state)
        parent[initial_state] = None
        
        while queue:
            current_state = queue.popleft()
            
            # Reconstruct game state
            temp_game = CakeGame(self.game.width, self.game.height, self.game.max_capacity)
            self._load_state(temp_game, current_state)
            
            if temp_game.is_solved():
                return self._reconstruct_path(parent, move_history, current_state)
            
            # Generate all possible moves
            for from_idx, from_tube in enumerate(temp_game.tubes):
                if from_tube.is_empty():
                    continue
                
                # Can remove any layer (list behavior)
                for layer_pos in range(len(from_tube.layers)):
                    for to_idx in temp_game.get_adjacent_tubes(from_idx):
                        # Create new game state for simulation
                        new_game = CakeGame(temp_game.width, temp_game.height, temp_game.max_capacity)
                        self._load_state(new_game, current_state)
                        
                        if new_game.move_layer(from_idx, layer_pos, to_idx):
                            new_state = new_game.get_state_hash()
                            if new_state not in visited:
                                visited.add(new_state)
                                parent[new_state] = current_state
                                move_history[new_state] = (from_idx, layer_pos, to_idx)
                                queue.append(new_state)
        
        return None
    
    def solve_a_star(self, heuristic_fn: str = 'basic') -> Optional[List[Tuple[int, int, int]]]:
        """A* Search with selectable heuristic"""
        open_set = []
        heapq.heappush(open_set, (0, self.game.get_state_hash()))
        
        came_from = {}
        g_score = {self.game.get_state_hash(): 0}
        f_score = {self.game.get_state_hash(): self._get_heuristic(self.game, heuristic_fn)}
        
        while open_set:
            _, current_state = heapq.heappop(open_set)
            
            temp_game = CakeGame(self.game.width, self.game.height, self.game.max_capacity)
            self._load_state(temp_game, current_state)
            
            if temp_game.is_solved():
                return self._reconstruct_path(came_from, {}, current_state)
            
            # Generate all possible moves
            for from_idx, from_tube in enumerate(temp_game.tubes):
                if from_tube.is_empty():
                    continue
                
                for layer_pos in range(len(from_tube.layers)):
                    for to_idx in temp_game.get_adjacent_tubes(from_idx):
                        new_game = CakeGame(temp_game.width, temp_game.height, temp_game.max_capacity)
                        self._load_state(new_game, current_state)
                        
                        if new_game.move_layer(from_idx, layer_pos, to_idx):
                            new_state = new_game.get_state_hash()
                            tentative_g = g_score[current_state] + 1
                            
                            if new_state not in g_score or tentative_g < g_score[new_state]:
                                came_from[new_state] = current_state
                                g_score[new_state] = tentative_g
                                f_score[new_state] = tentative_g + self._get_heuristic(new_game, heuristic_fn)
                                heapq.heappush(open_set, (f_score[new_state], new_state))
        
        return None
    
    def _get_heuristic(self, game: CakeGame, heuristic_fn: str) -> float:
        """Calculate heuristic value for state"""
        if heuristic_fn == 'basic':
            return self._basic_heuristic(game)
        elif heuristic_fn == 'advanced':
            return self._advanced_heuristic(game)
        else:
            return 0
    
    def _basic_heuristic(self, game: CakeGame) -> int:
        """Count of non-complete tubes"""
        return sum(1 for tube in game.tubes if not tube.is_complete() and not tube.is_empty())
    
    def _advanced_heuristic(self, game: CakeGame) -> int:
        """More sophisticated heuristic considering color diversity and blocking"""
        score = 0
        for tube in game.tubes:
            if tube.is_complete():
                continue
                
            # Color diversity penalty
            colors = set(layer.color for layer in tube.layers)
            score += len(colors) * 2
            
            # Blocking penalty
            if tube.layers:
                target_color = tube.layers[-1].color
                for layer in reversed(tube.layers):
                    if layer.color != target_color:
                        score += 1
        return score
    
    def _load_state(self, game: CakeGame, state_str: str):
        """Load game state from string representation"""
        tube_strs = state_str.split('|')
        game.tubes = []
        for tube_str in tube_strs:
            tube = Tube(game.max_capacity)
            layers = tube_str.split()
            for layer in layers:
                if layer:  # Skip empty strings
                    color = layer[0].lower()
                    size = int(layer[1:])
                    tube.add_layer(CakeLayer(color, size))
            game.tubes.append(tube)
    
    def _reconstruct_path(self, parent: Dict[str, str], moves: Dict[str, Tuple[int, int, int]], 
                         end_state: str) -> List[Tuple[int, int, int]]:
        """Reconstruct solution path from search"""
        path = []
        current = end_state
        while parent[current] is not None:
            path.append(moves[current])
            current = parent[current]
        return path[::-1]