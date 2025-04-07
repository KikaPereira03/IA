import heapq
import copy
from game.utils import evaluate_board, CakeSlice
from collections import deque
from copy import deepcopy
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

def astar_bot_solver(grid, queue, apply_moves=False):
    from copy import deepcopy
    from game.core import CakeSlice, Plate, CakeGame

    start_state = (deepcopy(grid), deepcopy(queue))
    visited = set()
    heap = []

    # Cada item: (f_score, g_score, grid, queue, path)
    initial_h = heuristic(grid)
    heapq.heappush(heap, (initial_h, 0, start_state[0], start_state[1], []))

    while heap:
        f_score, g_score, grid, queue, path = heapq.heappop(heap)

        state_id = str([[s.color for s in p.slices] for p in grid]) + str(queue)
        if state_id in visited:
            continue
        visited.add(state_id)

        if all(len(p.slices) == 0 or all(s.color == p.slices[0].color for s in p.slices) for p in grid):
            # Objetivo atingido
            if apply_moves and path:
                return [path[0]]
            return path

        for qi, plate in queue[:3]:  # usar apenas os 3 primeiros
            for gi, target in enumerate(grid):
                if len(target.slices) == 0:
                    new_grid = deepcopy(grid)
                    new_queue = deepcopy(queue)
                    plate_copy = list(plate)
                    new_grid[gi].slices.extend([CakeSlice(c, 1) for c in plate_copy])
                    new_queue.pop(qi)

                    new_path = path + [(qi, gi)]
                    g_new = g_score + 1
                    h_new = heuristic(new_grid)
                    f_new = g_new + h_new

                    heapq.heappush(heap, (f_new, g_new, new_grid, new_queue, new_path))

    return []


def simulate_merges(grid):
    changed = True
    while changed:
        changed = False
        for plate in grid:
            if len(plate.slices) == 6:
                colors = [s.color for s in plate.slices]
                if all(c == colors[0] for c in colors):
                    plate.slices.clear()
                    changed = True
        # Aqui podes chamar outras funções de merge se tiveres, ex:
        # merge_adjacent_plates(grid)

# def bfs_bot_solver(grid, queue, apply_moves=False):
        from game.core import merge_all_possible_slices
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