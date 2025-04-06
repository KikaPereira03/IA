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

