import heapq
import copy
from game.utils import evaluate_board, CakeSlice
from collections import deque
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
    """
    Pure A* search algorithm for finding optimal cake placements.
    Optimized for the cake game with better state representation and heuristics.
    
    Args:
        grid: List of Plate objects representing the current game grid
        queue: List of (index, plate_data) tuples where plate_data is a list of color chars
        apply_moves: Whether to return only the first move or all moves
    
    Returns:
        List containing a single (queue_index, grid_index) move
    """
    import heapq
    from copy import deepcopy
    from game.models import CakeSlice
    
    # Debug information
    print(f"A* search started")
    print(f"Queue received: {queue}")
    
    # Handle empty grid as a special case for better performance
    empty_slots = [i for i, plate in enumerate(grid) if not plate.slices]
    if all(not plate.slices for plate in grid) and queue:
        print(f"Initial empty grid detected - using optimized first move")
        return [(queue[0][0], empty_slots[0])]
    
    # Initialize open list (priority queue) and closed set
    open_list = []
    closed_set = set()
    
    # Initial state
    initial_state = {
        'grid': deepcopy(grid),
        'queue': deepcopy(queue),
        'path': [],
        'g_score': 0,
    }
    
    # Calculate initial heuristic
    h_score = calculate_heuristic(initial_state)
    f_score = h_score  # f = g + h, but g=0 initially
    
    # Add to open list: (f_score, tiebreaker, state)
    state_id = 0  # Used for tiebreaking when f_scores are equal
    heapq.heappush(open_list, (f_score, state_id, initial_state))
    
    # Track expansions
    expansions = 0
    max_expansions = 2000  # Increased to handle more complex states
    
    # Main A* search loop
    while open_list and expansions < max_expansions:
        expansions += 1
        
        # Get state with lowest f_score
        current_f, _, current_state = heapq.heappop(open_list)
        
        # Extract components
        current_grid = current_state['grid']
        current_queue = current_state['queue']
        current_path = current_state['path']
        current_g = current_state['g_score']
        
        # Only log every 100 expansions to reduce console spam
        if expansions % 100 == 0:
            print(f"Expanded {expansions} states, current f_score: {current_f}")
        
        # Create a state signature for the closed set
        grid_signature = tuple(tuple(s.color for s in p.slices) if p.slices else () 
                              for p in current_grid)
        queue_signature = tuple((i, tuple(colors)) for i, colors in current_queue[:3])
        state_signature = (grid_signature, queue_signature)
        
        # Skip if we've seen this state before
        if state_signature in closed_set:
            continue
            
        # Add to closed set
        closed_set.add(state_signature)
        
        # Check if we've reached a goal state
        if is_goal_state(current_grid, current_queue):
            print(f"A* found optimal solution after {expansions} expansions!")
            if apply_moves:
                return [current_path[0]] if current_path else []
            return current_path
            
        # Generate successor states by trying all valid moves
        for q_idx, (queue_pos, cake_colors) in enumerate(current_queue[:3]):  # First 3 visible
            # Find all empty plates - this is the only valid move in this game
            for g_idx, plate in enumerate(current_grid):
                if not plate.slices:
                    # Create new game state
                    new_grid = deepcopy(current_grid)
                    new_queue = deepcopy(current_queue)
                    
                    # Apply move - place cake on plate
                    new_grid[g_idx].slices.extend([CakeSlice(color, 1) for color in cake_colors])
                    new_queue.pop(q_idx)
                    
                    # Create new state
                    new_state = {
                        'grid': new_grid,
                        'queue': new_queue,
                        'path': current_path + [(queue_pos, g_idx)],
                        'g_score': current_g + 1
                    }
                    
                    # Calculate new scores
                    new_h = calculate_heuristic(new_state)
                    new_f = new_state['g_score'] + new_h
                    
                    # Add to open list
                    state_id += 1
                    heapq.heappush(open_list, (new_f, state_id, new_state))
    
    print(f"A* search exhausted after {expansions} expansions")
    
    # If we reached the expansion limit but have explored some valid paths,
    # return the best move we've found so far
    if open_list:
        best_f, _, best_state = heapq.heappop(open_list)
        if best_state['path']:
            print(f"Returning best partial solution with f_score={best_f}")
            return [best_state['path'][0]] if apply_moves else best_state['path']
    
    # Last resort: If there are still empty plates and queue items, make a simple move
    empty_slots = [i for i, plate in enumerate(grid) if not plate.slices]
    if empty_slots and queue:
        print(f"Falling back to simple placement - {len(empty_slots)} empty slots available")
        return [(queue[0][0], empty_slots[0])]
    
    print("A* could not find any valid moves")
    return []


def calculate_heuristic(state):
    grid = state['grid']
    queue = state['queue']
    
    h_score = 0
    
    # Penalty for remaining cakes in queue (directly affects distance to goal)
    h_score += len(queue) * 2
    
    # Process all plates
    for plate in grid:
        if not plate.slices:
            continue
            
        # Get color distribution
        color_counts = {}
        for slice in plate.slices:
            color_counts[slice.color] = color_counts.get(slice.color, 0) + 1
            
        if len(color_counts) > 1:
            # Mixed color plate - worse situation
            h_score += len(color_counts) * 5
            
            # Penalty based on how mixed the plate is
            dominant_color = max(color_counts, key=color_counts.get)
            dominant_count = color_counts[dominant_color]
            
            # Calculate 'purity' - how close to single-color the plate is
            for color, count in color_counts.items():
                if color != dominant_color:
                    h_score += count * 2  # Higher penalty for non-dominant colors
        else:
            # Single color plate - good situation
            color = next(iter(color_counts))
            count = color_counts[color]
            
            # Give bonus for plates close to completion
            if count == 6:
                h_score -= 10  # Big bonus for completed plate
            elif count == 5:
                h_score -= 8   # Almost there
            elif count == 4:
                h_score -= 6   # Getting close
            elif count == 3:
                h_score -= 3   # On the way
    
    # Bonus for empty plates (more placement options)
    empty_count = sum(1 for plate in grid if not plate.slices)
    h_score -= empty_count  # Slight bonus for having empty plates
    
    return h_score


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