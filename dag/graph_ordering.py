from __future__ import annotations

from collections import deque
from typing import Dict, Generic, Hashable, List, Mapping, Optional, Set, TypeVar

from .graph_storage import GraphStorage


NodeT = TypeVar("NodeT", bound=Hashable)


def topological_sort(storage: GraphStorage[NodeT]) -> List[NodeT]:
    """Return a topological ordering using Kahn's algorithm."""

    in_degree = {node: len(storage.predecessor_set(node)) for node in storage.nodes()}
    queue = deque(node for node in storage.nodes() if in_degree[node] == 0)

    ordered: List[NodeT] = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for downstream in storage.downstream(node):
            in_degree[downstream] -= 1
            if in_degree[downstream] == 0:
                queue.append(downstream)

    if len(ordered) != len(storage):
        raise ValueError("graph is not acyclic")
    return ordered


def topological_levels(storage: GraphStorage[NodeT]) -> List[List[NodeT]]:
    """Group nodes into execution levels based on in-degree zero frontiers."""

    in_degree = {node: len(storage.predecessor_set(node)) for node in storage.nodes()}
    frontier = [node for node in storage.nodes() if in_degree[node] == 0]
    levels: List[List[NodeT]] = []
    visited_count = 0

    while frontier:
        current_level = list(frontier)
        levels.append(current_level)
        next_frontier: List[NodeT] = []

        for node in current_level:
            visited_count += 1
            for child in storage.downstream(node):
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    next_frontier.append(child)

        frontier = next_frontier

    if visited_count != len(storage):
        raise ValueError("graph is not acyclic")
    return levels


def transitive_reduction(storage: GraphStorage[NodeT]) -> Dict[NodeT, Set[NodeT]]:
    """Remove edges implied by longer directed paths while preserving reachability.

    For each edge `u -> v`, the edge is redundant if some other neighbor of `u`
    can still reach `v`.
    """

    reduced = storage.clone_adjacency()
    for source in storage.nodes():
        direct_targets = list(storage.downstream(source))
        for target in direct_targets:
            alternative_starts = [candidate for candidate in direct_targets if candidate != target]
            if any(_has_path_in_adjacency(reduced, candidate, target) for candidate in alternative_starts):
                reduced[source].remove(target)
    return reduced


def critical_path(
    storage: GraphStorage[NodeT],
    durations: Optional[Mapping[NodeT, float]] = None,
) -> Dict[str, object]:
    """Compute the longest weighted path in a DAG.

    Node duration defaults to `1.0` when no explicit duration mapping is
    provided. The algorithm is dynamic programming over a topological order.
    """

    order = topological_sort(storage)
    if durations is None:
        durations = {}

    _validate_duration_keys(storage, durations)

    longest_to: Dict[NodeT, float] = {}
    predecessor: Dict[NodeT, Optional[NodeT]] = {}

    for node in order:
        node_duration = float(durations.get(node, 1.0))
        parents = storage.predecessors(node)
        if not parents:
            longest_to[node] = node_duration
            predecessor[node] = None
            continue

        best_parent = max(parents, key=lambda parent: longest_to[parent])
        longest_to[node] = longest_to[best_parent] + node_duration
        predecessor[node] = best_parent

    if not longest_to:
        return {"path": [], "duration": 0.0, "distances": {}}

    end_node = max(longest_to, key=longest_to.get)
    path: List[NodeT] = []
    current: Optional[NodeT] = end_node
    while current is not None:
        path.append(current)
        current = predecessor[current]
    path.reverse()

    return {"path": path, "duration": longest_to[end_node], "distances": longest_to}


class TopologyIndex(Generic[NodeT]):
    """Facade for DAG ordering, layering, and scheduling algorithms."""

    def __init__(self, storage: GraphStorage[NodeT]):
        self._storage = storage

    def topological_sort(self) -> List[NodeT]:
        return topological_sort(self._storage)

    def topological_levels(self) -> List[List[NodeT]]:
        return topological_levels(self._storage)

    def transitive_reduction(self) -> Dict[NodeT, Set[NodeT]]:
        return transitive_reduction(self._storage)

    def critical_path(
        self,
        durations: Optional[Mapping[NodeT, float]] = None,
    ) -> Dict[str, object]:
        return critical_path(self._storage, durations=durations)


def _validate_duration_keys(storage: GraphStorage[NodeT], durations: Mapping[NodeT, float]) -> None:
    unknown = [node for node in durations if node not in storage]
    if unknown:
        raise KeyError("unknown duration nodes: %s" % unknown)


def _has_path_in_adjacency(adjacency: Dict[NodeT, Set[NodeT]], source: NodeT, target: NodeT) -> bool:
    if source == target:
        return True

    stack = [source]
    visited = {source}
    while stack:
        current = stack.pop()
        for child in adjacency[current]:
            if child == target:
                return True
            if child not in visited:
                visited.add(child)
                stack.append(child)
    return False
