import heapq
from collections import Counter, deque
from copy import deepcopy

from game.models import CakeSlice
from game.utils import evaluate_board


# -------------------------
# Data Structures
# -------------------------

class SearchNode:
    """Node class for search algorithms like A* and Greedy."""
    def __init__(self, state, parent=None, action=None, cost=0, heuristic=0, use_greedy=False):
        self.state = state           # A CakeGame instance
        self.parent = parent         # The SearchNode we came from
        self.action = action         # A tuple like (from_idx, to_idx)
        self.cost = cost             # g(n)
        self.heuristic = heuristic   # h(n)
        self.f_score = heuristic if use_greedy else cost + heuristic  # f(n)

    def __lt__(self, other):
        """For priority queue comparison."""
        return self.f_score < other.f_score


class GameState:
    """Represents a game state for search algorithms."""
    def __init__(self, grid, queue, path=None):
        # Deep copy to avoid sharing state between objects
        self.grid = [row.copy() for row in grid]
        self.queue = [p.copy() for p in queue]
        self.path = path or []

    def get_top_group(self, plate):
        """Gets a group of same-colored slices from the top of a plate."""
        if not plate:
            return []
        top_color = plate[-1]
        group = []
        for slice in reversed(plate):
            if slice == top_color:
                group.append(slice)
            else:
                break
        return group
    
    def is_goal(self):
        """Checks if we've reached a goal state (all plates properly sorted)."""
        return all(cell is None for row in self.grid for cell in row) and not self.queue

    def successors(self):
        """Generates all possible successor states."""
        succs = []
        if not self.queue:
            return succs

        next_plate = self.queue[0]  # Current plate
        for r in range(len(self.grid)):
            for c in range(len(self.grid[0])):
                if self.grid[r][c] is None:
                    new_grid = [row.copy() for row in self.grid]
                    new_queue = self.queue[1:]
                    new_grid[r][c] = next_plate.copy()
                    new_grid = self.resolve_disappear(new_grid)
                    new_state = GameState(new_grid, new_queue, self.path + [((r, c), next_plate)])
                    succs.append(new_state)
        return succs

    def resolve_disappear(self, grid):
        """Resolves plates that should disappear (6 same-colored slices)."""
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                plate = grid[r][c]
                if plate is not None and len(plate) == 6 and all(f == plate[0] for f in plate):
                    grid[r][c] = None
        return grid

    def __eq__(self, other):
        """For equality comparison."""
        return self.grid == other.grid and self.queue == other.queue

    def __hash__(self):
        """For use in sets and as dictionary keys."""
        return hash(str(self.grid) + str(self.queue))


# -------------------------
# Helper Functions
# -------------------------

def reconstruct_path(node):
    """Reconstructs the path from start to goal."""
    path = []
    while node.parent is not None:
        path.append(node.action)
        node = node.parent
    path.reverse()
    return path


def is_goal_state(grid, queue):
    """Checks if the current state is a goal state."""
    # If queue still has items, we haven't reached the goal
    if queue:
        return False
        
    # Check all plates are properly sorted
    for plate in grid:
        if plate.slices:
            colors = set(slice.color for slice in plate.slices)
            if len(colors) > 1:
                # Found a mixed-color plate, not a goal state
                return False
    
    # Queue is empty and all plates are sorted
    return True


def improved_simulate_merge(grid, placed_idx, current_score):
    """Simulates merging plates after a placement."""
    score = current_score
    
    # First check for plate completion at placed position
    plate = grid[placed_idx]
    if len(plate.slices) == 6:
        color = plate.slices[0].color
        if all(s.color == color for s in plate.slices):
            score += 50  # Already got +10 for placement
            plate.slices = []  # Clear the plate
    
    try:
        # Create a temporary game object to use its get_adjacent_plates method
        # Estimate dimensions based on grid length
        from game.core import CakeGame
        grid_size = len(grid)
        grid_width = int(grid_size ** 0.5)
        if grid_width * grid_width < grid_size:
            grid_width += 1
        grid_height = (grid_size + grid_width - 1) // grid_width
        
        temp_game = CakeGame(grid_width, grid_height)
        adjacent_indices = temp_game.get_adjacent_plates(placed_idx)
        
        # Filter to ensure indices are valid
        adjacent_indices = [idx for idx in adjacent_indices if 0 <= idx < len(grid)]
        
    except Exception as e:
        print(f"Warning in adjacency calculation: {e}")
        # Continue without merging if there's an error
    
    return score


def simulate_move_colors(grid, from_idx, to_idx, color):
    """Simulates moving slices of a specific color between plates."""
    from_plate = grid[from_idx]
    to_plate = grid[to_idx]
    
    color_indices = [i for i, s in enumerate(from_plate.slices) if s.color == color]
    
    if not color_indices:
        return False
    
    available_space = 6 - len(to_plate.slices)  # Assuming max capacity is 6
    
    if available_space <= 0:
        return False
    
    moved = False
    for idx in sorted(color_indices, reverse=True)[:available_space]:
        slice_to_move = from_plate.slices[idx]
        to_plate.slices.append(slice_to_move)
        from_plate.slices.pop(idx)
        moved = True
        
        # Update color indices
        color_indices = [i for i, s in enumerate(from_plate.slices) if s.color == color]
    
    return moved


def simulate_merge(grid):
    """Simplified version of merge_all_possible_slices to estimate state after merges."""
    # First check for plate completions
    for plate_idx, plate in enumerate(grid):
        # Check for plate completion
        if len(plate.slices) == 6:
            first_color = plate.slices[0].color if plate.slices else None
            if first_color and all(s.color == first_color for s in plate.slices):
                plate.slices = []  # Clear the plate
                
    # Simple color consolidation
    for plate_idx, plate in enumerate(grid):
        if not plate.slices:
            continue
            
        colors = [s.color for s in plate.slices]
        if len(set(colors)) > 1:
            # Sort slices by color to simulate some consolidation
            plate.slices.sort(key=lambda s: s.color)


# -------------------------
# Heuristic Functions
# -------------------------

def improved_heuristic(state):
    """
    Enhanced heuristic that better guides the search toward achieving required score.
    Lower scores are better.
    """
    grid = state['grid']
    queue = state['queue']
    
    # Initialize the score
    h_score = 0
    
    # Analyze plates on the grid
    for plate in grid:
        if not plate.slices:
            continue
            
        color_counts = {}
        for slice in plate.slices:
            color_counts[slice.color] = color_counts.get(slice.color, 0) + 1
            
        if len(color_counts) == 1:  # Single-color plate
            color = next(iter(color_counts))
            count = color_counts[color]
            
            # Strongly favor plates that are close to completion
            if count == 6:  # Complete plate (unlikely as these would disappear)
                h_score -= 100
            elif count == 5:  # One away from completion
                h_score -= 80
            elif count == 4:  # Two away from completion
                h_score -= 60
            elif count == 3:  # Three away from completion
                h_score -= 30
            else:
                h_score -= count * 5
        else:
            # Heavily penalize mixed-color plates based on diversity
            h_score += (len(color_counts) - 1) * 15
            
            # Less penalty if there's a dominant color
            max_count = max(color_counts.values())
            if max_count >= 3:
                h_score -= 10
    
    # Look ahead at the queue - favor moves that would work well with upcoming pieces
    if len(queue) >= 2:
        # Check if consecutive queue items have matching colors
        upcoming_colors = []
        for _, colors in queue[:min(3, len(queue))]:
            if colors:
                upcoming_colors.append(colors[0])  # Most accessible color is at index 0
                
        if len(set(upcoming_colors)) < len(upcoming_colors):  # Duplicate colors exist
            h_score -= 15  # Bonus for potential future matches
    
    return h_score  # Lower is better


# -------------------------
# Search Algorithms
# -------------------------

def generic_solver(initial_game, heuristic_fn, use_greedy=False):
    """Generic solver that can be configured for A* or Greedy search."""
    start_node = SearchNode(
        state=deepcopy(initial_game),
        cost=0,
        heuristic=heuristic_fn(initial_game),
        use_greedy=use_greedy
    )

    open_list = []
    heapq.heappush(open_list, start_node)
    closed_set = set()

    while open_list:
        current = heapq.heappop(open_list)

        state_hash = hash(current.state)

        if state_hash in closed_set:
            continue

        closed_set.add(state_hash)

        if current.state.is_goal():
            return reconstruct_path(current)

        for from_idx, from_plate in enumerate(current.state.queue):
            group = current.state.get_top_group(from_plate)
            if not group:
                continue

            color = group[0].color
            for to_idx in current.state.get_adjacent_plates(from_idx):
                to_plate = current.state.plates[to_idx]
                if current.state.is_valid_transfer(from_plate, to_plate, group):
                    new_state = deepcopy(current.state)
                    new_state.move_slices(from_idx, to_idx, len(group))
                    new_state.merge_all_possible_slices()
                    new_cost = current.cost + 1
                    new_heuristic = heuristic_fn(new_state)
                    new_node = SearchNode(
                        state=new_state,
                        parent=current,
                        action=(from_idx, to_idx),
                        cost=new_cost,
                        heuristic=new_heuristic,
                        use_greedy=use_greedy
                    )
                    heapq.heappush(open_list, new_node)

    return None  # No solution found


def a_star_solver(initial_game, heuristic_fn):
    """A* search implementation using the generic solver."""
    return generic_solver(initial_game, heuristic_fn, use_greedy=False)


def greedy_solver(initial_game, heuristic_fn):
    """Greedy search implementation using the generic solver."""
    return generic_solver(initial_game, heuristic_fn, use_greedy=True)


# -------------------------
# Bot Algorithms
# -------------------------

def greedy_bot_solver(grid, queue, apply_moves=False):
    """
    Greedy bot solver that evaluates each possible move and chooses the best one.
    
    Args:
        grid: List of plates on the board
        queue: Queue of upcoming cake plates
        apply_moves: Whether to apply the moves directly
        
    Returns:
        List of moves to make [(queue_index, grid_index)]
    """
    best_score = -float('inf')
    best_move = (-1, -1)

    for q_index, plate in queue:
        for g_index, cell in enumerate(grid):
            if len(cell.slices) + len(plate) > 6:
                continue

            temp_grid = deepcopy(grid)
            temp_grid[g_index].slices.extend([CakeSlice(c, 1) for c in plate])

            score = evaluate_board(temp_grid)

            if score > best_score:
                best_score = score
                best_move = (q_index, g_index)

    return [best_move]


def astar_bot_solver(grid, queue, apply_moves=False):
    """
    A* bot solver that uses heuristic search to find optimal moves.
    
    Args:
        grid: List of plates on the board
        queue: Queue of upcoming cake plates
        apply_moves: Whether to apply the moves directly
        
    Returns:
        List of moves to make [(queue_index, grid_index)]
    """
    print(f"A* search started")
    print(f"Queue received: {queue}")
    
    # Debug settings
    DEBUG = True  # Set to False in production
    
    # Handle empty grid as a special case
    empty_slots = [i for i, plate in enumerate(grid) if not plate.slices]
    if all(not plate.slices for plate in grid) and queue:
        print(f"Initial empty grid detected - using optimized first move")
        return [(queue[0][0], empty_slots[0])]

    # Parameters
    max_depth = 3  # Only look ahead 3 moves
    max_expansions = 1000  # Lower than before for faster decisions
    expansions = 0
    state_id = 0

    open_list = []
    closed_set = set()

    # Calculate initial score more accurately
    initial_score = 0
    for plate in grid:
        if len(plate.slices) == 6:
            color = plate.slices[0].color if plate.slices else None
            if color and all(s.color == color for s in plate.slices):
                initial_score += 60
    
    if DEBUG:
        print(f"Initial score: {initial_score}")
        print(f"Empty slots: {len(empty_slots)}/{len(grid)}")
        plate_status = []
        for i, plate in enumerate(grid):
            if plate.slices:
                colors = [s.color for s in plate.slices]
                plate_status.append(f"Plate {i}: {colors}")
        print(f"Plate status: {plate_status[:5]}...")

    # Initial state
    initial_state = {
        'grid': deepcopy(grid),
        'queue': deepcopy(queue),
        'path': [],
        'g_score': 0,
        'score': initial_score,
        'depth': 0,
        'last_action': None
    }

    # Initial heuristic evaluation
    h_score = improved_heuristic(initial_state)
    f_score = h_score
    
    if DEBUG:
        print(f"Initial heuristic score: {h_score}")
    
    heapq.heappush(open_list, (f_score, state_id, initial_state))

    best_partial_state = None
    best_score_improvement = -float('inf')
    
    # For debugging - track best states at each depth
    best_states_by_depth = {0: None, 1: None, 2: None, 3: None}
    best_scores_by_depth = {0: -float('inf'), 1: -float('inf'), 2: -float('inf'), 3: -float('inf')}

    while open_list and expansions < max_expansions:
        expansions += 1
        current_f, _, current_state = heapq.heappop(open_list)

        current_grid = current_state['grid']
        current_queue = current_state['queue']
        current_path = current_state['path']
        current_g = current_state['g_score']
        current_score = current_state['score']
        current_depth = current_state['depth']
        
        # Track best states at each depth for debugging
        if current_score > best_scores_by_depth[current_depth]:
            best_scores_by_depth[current_depth] = current_score
            best_states_by_depth[current_depth] = current_state

        if current_depth >= max_depth:
            # At max depth, evaluate score improvement
            score_improvement = current_score - initial_score
            if score_improvement > best_score_improvement and current_path:
                best_score_improvement = score_improvement
                best_partial_state = current_state
                if DEBUG and score_improvement > 0:
                    print(f"Found better move sequence at depth {current_depth}: +{score_improvement} points")
                    print(f"Path: {current_path}")
            continue

        # Create state signature
        grid_signature = tuple(tuple(s.color for s in p.slices) if p.slices else () 
                              for p in current_grid)
        queue_signature = tuple((i, tuple(colors)) for i, colors in current_queue[:3])
        state_signature = (grid_signature, queue_signature, current_depth)
        
        if state_signature in closed_set:
            continue
        closed_set.add(state_signature)

        # Generate successor states by trying each possible move
        for q_idx, (queue_pos, cake_colors) in enumerate(current_queue[:3]):
            for g_idx, plate in enumerate(current_grid):
                if not plate.slices:  # Can only place on empty plates
                    new_grid = deepcopy(current_grid)
                    new_queue = deepcopy(current_queue)
                    
                    # Apply move - more accurate queue management
                    new_grid[g_idx].slices.extend([CakeSlice(color, 1) for color in cake_colors])
                    new_queue.pop(q_idx)  # Remove the used queue item
                    
                    # Add simulated merging using actual game mechanics
                    new_score = current_score + 10  # Base score for placement
                    new_score = improved_simulate_merge(new_grid, g_idx, new_score)
                    
                    # Create new state
                    new_state = {
                        'grid': new_grid,
                        'queue': new_queue,
                        'path': current_path + [(queue_pos, g_idx)],
                        'g_score': current_g + 1,
                        'score': new_score,
                        'depth': current_depth + 1,
                        'last_action': (queue_pos, g_idx)
                    }
                    
                    # Calculate new heuristic
                    new_h = improved_heuristic(new_state)
                    new_f = new_state['g_score'] + new_h
                    
                    state_id += 1
                    heapq.heappush(open_list, (new_f, state_id, new_state))

    if DEBUG:
        print(f"A* search completed after {expansions} expansions")
        print(f"States explored by depth: {[len([s for s in closed_set if s[2] == d]) for d in range(4)]}")
        print(f"Best scores by depth: {best_scores_by_depth}")
        if best_partial_state:
            print(f"Best move sequence: {best_partial_state['path']}")
            print(f"Best score improvement: +{best_partial_state['score'] - initial_score}")
        
        # Visualize best sequence found
        if best_partial_state and len(best_partial_state['path']) > 0:
            print("\nBest move sequence visualization:")
            temp_grid = deepcopy(grid)
            temp_queue = deepcopy(queue)
            for step, (q_pos, g_idx) in enumerate(best_partial_state['path']):
                q_idx = next(i for i, (pos, _) in enumerate(temp_queue) if pos == q_pos)
                colors = temp_queue[q_idx][1]
                print(f"Step {step+1}: Place {colors} from queue position {q_pos} to grid position {g_idx}")
                
                # Simulate the placement
                temp_grid[g_idx].slices.extend([CakeSlice(color, 1) for color in colors])
                temp_queue.pop(q_idx)
                
                # Simplified plate status after move
                relevant_plates = [(i, [s.color for s in p.slices]) for i, p in enumerate(temp_grid) if p.slices]
                print(f"   Relevant plates after move: {relevant_plates[:3]}...")

    # Return the best move found
    if best_partial_state and best_partial_state['path']:
        print(f"Found move with score improvement: +{best_partial_state['score'] - initial_score}")
        return [best_partial_state['path'][0]] if apply_moves else best_partial_state['path']
    
    # Fallback to simple placement if no good moves found
    if empty_slots and queue:
        print(f"Falling back to simple placement")
        # Try to make a smarter fallback by choosing plates with adjacent matches
        best_slot = empty_slots[0]
        best_match = -1
        
        from game.core import CakeGame
        
        try:
            # Create a temporary game object to use its get_adjacent_plates method
            grid_size = len(grid)
            grid_width = int(grid_size ** 0.5)
            if grid_width * grid_width < grid_size:
                grid_width += 1
            grid_height = (grid_size + grid_width - 1) // grid_width
            
            temp_game = CakeGame(grid_width, grid_height)
            
            for slot_idx in empty_slots:
                # Check adjacent plates for color matching
                adjacent_plates = temp_game.get_adjacent_plates(slot_idx)
                # Ensure indices are within range
                adjacent_plates = [idx for idx in adjacent_plates if 0 <= idx < len(grid)]
                
                match_score = 0
                
                for adj_idx in adjacent_plates:
                    adj_plate = grid[adj_idx]
                    if adj_plate.slices:
                        adj_colors = [s.color for s in adj_plate.slices]
                        # Check if queue colors match adjacent plates
                        for _, colors in queue[:3]:
                            for color in colors:
                                if color in adj_colors:
                                    match_score += 1
                
                if match_score > best_match:
                    best_match = match_score
                    best_slot = slot_idx
        except Exception as e:
            print(f"Warning in fallback placement: {e}")
            # Use first empty slot as fallback
            best_slot = empty_slots[0]
                    
        if DEBUG and best_match > 0:
            print(f"Smart fallback: Found slot {best_slot} with {best_match} color matches")
                
        return [(queue[0][0], best_slot)]
    
    print("A* could not find any valid moves")
    return []