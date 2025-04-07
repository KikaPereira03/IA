import heapq
from copy import deepcopy
from game.core import CakeSlice


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


def evaluate_board(grid):
    score = 0
    for plate in grid:
        if not plate.slices:
            continue
        colors = [s.color for s in plate.slices]
        if len(colors) == 6 and all(c == colors[0] for c in colors):
            score += 100  # prato completo
        else:
            first = colors[0]
            wrong = sum(1 for c in colors if c != first)
            score -= wrong * 2  # penalização
    return score


def greedy_bot_solver(grid, queue, apply_moves=False):
    best_score = -float('inf')
    best_move = (-1, -1)

    for q_index, plate in queue:
        for g_index, cell in enumerate(grid):
            if len(cell.slices) > 0:
                continue  # só colocamos em pratos vazios
            if len(plate) > 6:
                continue
            temp_grid = deepcopy(grid)
            temp_grid[g_index].slices.extend([CakeSlice(c, 1) for c in plate])
            simulate_merges(temp_grid)
            score = evaluate_board(temp_grid)
            if score > best_score:
                best_score = score
                best_move = (q_index, g_index)

    return [best_move]


def astar_bot_solver(grid, queue, apply_moves=False):
    class State:
        def __init__(self, grid, queue, path, g_score):
            self.grid = grid
            self.queue = queue
            self.path = path
            self.g = g_score
            self.h = heuristic(grid)
            self.f = self.g + self.h

        def __lt__(self, other):
            return self.f < other.f

    def heuristic(grid):
        score = 0
        for plate in grid:
            if not plate.slices:
                continue
            colors = [s.color for s in plate.slices]
            if len(colors) == 6 and all(c == colors[0] for c in colors):
                score -= 10
            else:
                first = colors[0]
                wrong = sum(1 for c in colors if c != first)
                score += wrong
        return score

    visited = set()
    heap = []

    initial_grid = deepcopy(grid)
    initial_queue = deepcopy(queue)
    initial_path = []

    heapq.heappush(heap, State(initial_grid, initial_queue, initial_path, 0))

    while heap:
        current = heapq.heappop(heap)
        state_id = str([[s.color for s in p.slices] for p in current.grid]) + str(current.queue)
        if state_id in visited:
            continue
        visited.add(state_id)

        if not current.queue:
            if apply_moves and current.path:
                return [current.path[0]]
            return current.path

        for q_index, plate in current.queue[:3]:
            for g_index, target in enumerate(current.grid):
                if len(target.slices) > 0:
                    continue  # só em pratos vazios
                if len(plate) > 6:
                    continue

                new_grid = deepcopy(current.grid)
                new_queue = [item for item in current.queue if item[0] != q_index]
                new_grid[g_index].slices.extend([CakeSlice(c, 1) for c in plate])
                simulate_merges(new_grid)

                new_path = current.path + [(q_index, g_index)]
                new_state = State(new_grid, new_queue, new_path, current.g + 1)
                heapq.heappush(heap, new_state)

    return []

# def bfs_bot_solver(grid, queue, apply_moves=False):
        
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