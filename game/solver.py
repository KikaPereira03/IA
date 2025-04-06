import heapq
import copy

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

        for from_idx, from_plate in enumerate(current.state.plates):
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