import heapq
import copy
from game.core import CakeGame
from game.utils import evaluate_board, CakeSlice
from collections import deque, Counter
from copy import deepcopy
from game.models import CakeSlice
from copy import deepcopy
#from game.core import merge_all_possible_slices



class SearchNode:
    def __init__(self, state, parent=None, action=None, cost=0, heuristic=0, use_greedy=False):
        self.state = state  # A CakeGame instance
        self.parent = parent  # The SearchNode we came from
        self.action = action  # A tuple like (from_idx, to_idx)
        self.cost = cost  # g(n)
        self.heuristic = heuristic  # h(n)
        self.f_score = heuristic if use_greedy else cost + heuristic  # f(n)

    def __lt__(self, other):
        return self.f_score < other.f_score


def reconstruct_path(node):
    path = []
    while node.parent is not None:
        path.append(node.action)
        node = node.parent
    path.reverse()
    return path


def generic_solver(initial_game, heuristic_fn, use_greedy=False):
    start_node = SearchNode(
        state=copy.deepcopy(initial_game),
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
                    new_state = copy.deepcopy(current.state)
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
    return generic_solver(initial_game, heuristic_fn, use_greedy=False)

def greedy_solver(initial_game, heuristic_fn):
    return generic_solver(initial_game, heuristic_fn, use_greedy=True)

class GameState:
    def __init__(self, grid, queue, path=None):
        # Copia profunda para não partilhar estado entre objetos
        self.grid = [row.copy() for row in grid]
        self.queue = [p.copy() for p in queue]
        self.path = path or []

    def get_top_group(self, plate):
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
        return all(cell is None for row in self.grid for cell in row) and not self.queue

    def successors(self):
        succs = []
        if not self.queue:
            return succs

        next_plate = self.queue[0]  # prato da vez
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
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                plate = grid[r][c]
                if plate is not None and len(plate) == 6 and all(f == plate[0] for f in plate):
                    grid[r][c] = None
        return grid

    def __eq__(self, other):
        return self.grid == other.grid and self.queue == other.queue

    def __hash__(self):
        return hash(str(self.grid) + str(self.queue))


# Heurística muito simples: contar número de pratos ocupados + pratos restantes na queue
def simple_heuristic(state: GameState):
    pratos_na_grid = sum(1 for row in state.grid for cell in row if cell is not None)
    return pratos_na_grid + len(state.queue)


# Exemplo de função para correr o solver com um estado inicial
def solve_game(grid, queue):
    initial_state = GameState(grid, queue)
    path = a_star_solver(initial_state, heuristic_fn=simple_heuristic)
    return path


def evaluate_best_placement(grid, queue):
    best_score = -float("inf")
    best_move = (-1, -1)  # (queue_index, grid_index)

    for q_index, plate in enumerate(queue[:3]):  # Só os 3 primeiros pratos visíveis
        for g_index, cell in enumerate(grid):
            if len(cell.slices) + len(plate.slices) > 6:
                continue

            if not cell.slices:
                score = 1
            else:
                top_color = cell.slices[-1].color
                same = sum(1 for s in plate.slices if s.color == top_color)
                diff = sum(1 for s in plate.slices if s.color != top_color)
                score = same * 2 - diff

            if score > best_score:
                best_score = score
                best_move = (q_index, g_index)

    return best_move


def greedy_bot_solver(grid, queue, apply_moves=False):
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

import heapq

def heuristic(grid):
    """Simple heuristic: count mixed-color plates"""
    h_score = 0
    for plate in grid:
        if plate.slices:
            colors = set(s.color for s in plate.slices)
            if len(colors) > 1:
                h_score += 1
    return h_score

def astar_bot_solver(grid, queue, apply_moves=False):
    import heapq
    from copy import deepcopy
    from game.models import CakeSlice

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


def improved_heuristic(state):
    """
    Enhanced heuristic that better prioritizes states leading to plate completions and merges
    """
    grid = state['grid']
    queue = state['queue']
    
    # Initialize the score
    h_score = 0
    
    # Analyze plates on the grid
    plate_colors = {}  # Track colors across plates for potential merges
    uniform_plates = 0
    
    for idx, plate in enumerate(grid):
        if not plate.slices:
            continue
            
        color_counts = {}
        for slice in plate.slices:
            color_counts[slice.color] = color_counts.get(slice.color, 0) + 1
            
            # Also track colors across all plates for potential merges
            plate_colors[slice.color] = plate_colors.get(slice.color, 0) + 1
            
        if len(color_counts) == 1:  # Single-color plate
            uniform_plates += 1
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
            max_color = max(color_counts.keys(), key=lambda k: color_counts[k])
            max_count = color_counts[max_color]
            if max_count >= 3:
                h_score -= 8  # Smaller bonus for plates with dominant color
                
                # Check if we have potential to complete this plate with queue items
                for _, cake_colors in queue:
                    if max_color in cake_colors:
                        h_score -= 5  # Extra bonus when the queue has matching colors
    
    # Reward states with many uniform plates
    h_score -= uniform_plates * 10
    
    # Look ahead at the queue - favor moves that would work well with upcoming pieces
    if queue:
        queue_colors = []
        for _, colors in queue[:min(3, len(queue))]:
            queue_colors.extend(colors)
            
        # Reward states where queue colors match existing plates
        for color, count in plate_colors.items():
            matching_in_queue = queue_colors.count(color)
            if matching_in_queue > 0:
                h_score -= matching_in_queue * 2  # Bonus for potential merges
    
    return h_score  # Lower is better

def improved_simulate_merge(grid, placed_idx, current_score):
    from collections import Counter
    from game.core import CakeGame  # Import to use the get_adjacent_plates method
    
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
        grid_size = len(grid)
        grid_width = int(grid_size ** 0.5)
        if grid_width * grid_width < grid_size:
            grid_width += 1
        grid_height = (grid_size + grid_width - 1) // grid_width
        
        temp_game = CakeGame(grid_width, grid_height)
        adjacent_indices = temp_game.get_adjacent_plates(placed_idx)
        
        # Filter to ensure indices are valid (additional safety check)
        adjacent_indices = [idx for idx in adjacent_indices if 0 <= idx < len(grid)]
        
        # Process adjacent plates
        for adj_idx in adjacent_indices:
            adj_plate = grid[adj_idx]
            if not adj_plate.slices or not plate.slices:
                continue
                
            # Your merging logic would go here
            # This is just a placeholder to ensure the function works
            
    except Exception as e:
        print(f"Warning in adjacency calculation: {e}")
        # Continue without merging if there's an error
    
    return score



def simulate_move_colors(grid, from_idx, to_idx, color):
    """
    Simulate moving slices of a specific color between plates
    """
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

def improved_heuristic(state):
    """
    Enhanced heuristic that better guides the search toward achieving required score
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

def simulate_merge(grid):
    """Simplified version of merge_all_possible_slices to estimate state after merges"""
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


def calculate_heuristic(state):
    score = evaluate_board(state['grid'])
    goal_score = 1000  # or fetch dynamically
    score_gap = max(0, goal_score - score)
    
    # Bonus if plates are close to disappearing
    bonus = 0
    for plate in state['grid']:
        if len(plate.slices) == 6:
            if all(s.color == plate.slices[0].color for s in plate.slices):
                bonus += 100  # big boost
            elif len(set(s.color for s in plate.slices)) <= 2:
                bonus += 10  # small bonus for nearly uniform

    return score_gap - bonus

def is_goal_state(grid, queue):
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

# def bfs_bot_solver(grid, queue, apply_moves=False):
#        from game.core import merge_all_possible_slices
#     initial_state = (deepcopy(grid), deepcopy(queue), [])
#     queue_bfs = deque([initial_state])
#     visited = set()

#     def serialize(g, q):
#         return str([[s.color for s in plate.slices] for plate in g]) + str(q)

#     while queue_bfs:
#         g, q, path = queue_bfs.popleft()
#         state_key = serialize(g, q)
#         if state_key in visited:
#             continue
#         visited.add(state_key)

#         for q_index, plate in enumerate(q[:3]):
#             for g_index, cell in enumerate(g):
#                 if len(cell.slices) + len(plate) > 6:
#                     continue  # não cabe

#                 new_g = deepcopy(g)
#                 new_q = deepcopy(q)
#                 new_path = list(path)

#                 new_g[g_index].slices.extend([CakeSlice(c, 1) for c in plate])
#                 merge_all_possible_slices(new_g)
#                 del new_q[q_index]
#                 new_path.append((q_index, g_index))

#                 if not new_q:
#                     return new_path if apply_moves else [new_path[0]]

#                 queue_bfs.append((new_g, new_q, new_path))

#     return []


# def dfs_bot_solver(grid, queue, apply_moves=False):
#     initial_state = (deepcopy(grid), deepcopy(queue), [])
#     stack_dfs = [(initial_state)]
#     visited = set()

#     def serialize(g, q):
#         return str([[s.color for s in plate.slices] for plate in g]) + str(q)

#     while stack_dfs:
#         g, q, path = stack_dfs.pop()
#         state_key = serialize(g, q)
#         if state_key in visited:
#             continue
#         visited.add(state_key)

#         for q_index, plate in enumerate(q[:3]):
#             for g_index, cell in enumerate(g):
#                 if len(cell.slices) + len(plate) > 6:
#                     continue  # não cabe

#                 new_g = deepcopy(g)
#                 new_q = deepcopy(q)
#                 new_path = list(path)

#                 new_g[g_index].slices.extend([CakeSlice(c, 1) for c in plate])
#                 merge_all_possible_slices(new_g)
#                 del new_q[q_index]
#                 new_path.append((q_index, g_index))

#                 if not new_q:
#                     return new_path if apply_moves else [new_path[0]]

#                 stack_dfs.append((new_g, new_q, new_path))

#     return []