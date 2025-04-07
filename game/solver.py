import heapq
import copy
from game.utils import evaluate_board, CakeSlice
from collections import deque
from copy import deepcopy
import game.core
#from game.core import merge_all_possible_slices



class SearchNode:
    def __init__(self, state, parent=None, action=None, cost=0, heuristic=0):
        self.state = state  # A CakeGame instance
        self.parent = parent  # The SearchNode we came from
        self.action = action  # A tuple like (from_idx, to_idx)
        self.cost = cost  # g(n)
        self.heuristic = heuristic  # h(n)
        self.f_score = cost + heuristic  # f(n) = g(n) + h(n)

    def __lt__(self, other):
        return self.f_score < other.f_score


def reconstruct_path(node):
    path = []
    while node.parent is not None:
        path.append(node.action)
        node = node.parent
    path.reverse()
    return path


def a_star_solver(initial_game, heuristic_fn):
    start_node = SearchNode(
        state=copy.deepcopy(initial_game),
        cost=0,
        heuristic=heuristic_fn(initial_game)
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
                    h = heuristic_fn(new_state)
                    new_node = SearchNode(
                        state=new_state,
                        parent=current,
                        action=(from_idx, to_idx),
                        cost=current.cost + 1,
                        heuristic=h
                    )
                    heapq.heappush(open_list, new_node)

    return None  # No solution found

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
    # Heurística: número de fatias mal organizadas
    h = 0
    for plate in grid:
        colors = [s.color for s in plate.slices]
        if colors:
            first = colors[0]
            if any(c != first for c in colors):
                h += 1
    return h

def dfs_bot_solver(game, *, apply_moves=False, max_depth=1000):
    print("\n🔍 Starting DFS...")

    plates = game.plates
    width = game.width
    height = game.height

    grid = [plates[i * width:(i + 1) * width] for i in range(height)]

    # Derive queue directly from plates (e.g., flattened and reversed plates)
    queue = []
    for plate in plates:
        if plate.slices:  # only if plate has slices
            queue.append([s.color for s in plate.slices[::-1]])

    initial_game = GameState(grid=grid, queue=deepcopy(queue))

    root = SearchNode(state=initial_game)
    frontier = [root]  # Stack (LIFO)
    visited = set()
    step = 0

    while frontier:
        node = frontier.pop()
        current_game = node.state

        print(f"\n🧩 Step {step}")
        for r, row in enumerate(current_game.grid):
            for c, plate in enumerate(row):
                print(f"  Plate ({r}, {c}): {plate}")
        print(f"  Queue: {current_game.queue}")
        step += 1

        if current_game.is_goal():
            print("✅ Goal found!")
            path = reconstruct_path(node)
            if apply_moves:
                for (r, c), plate in path:
                    game.plates[r * width + c] = plate
                return path
            else:
                return path

        if node.cost >= max_depth:
            continue

        for successor in current_game.successors():
            state_id = (str(successor.grid), str(successor.queue))
            if state_id not in visited:
                visited.add(state_id)
                frontier.append(SearchNode(
                    state=successor,
                    parent=node,
                    action=successor.path[-1] if successor.path else None,
                    cost=node.cost + 1
                ))

    print("❌ No solution found!")
    return []