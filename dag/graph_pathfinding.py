from __future__ import annotations

import heapq
from collections import deque
from typing import Callable, Dict, Generic, Hashable, List, Optional, Tuple, TypeVar

from .graph_storage import GraphStorage


NodeT = TypeVar("NodeT", bound=Hashable)
WeightFn = Callable[[NodeT, NodeT], float]


def shortest_path(storage: GraphStorage[NodeT], source: NodeT, target: NodeT) -> List[NodeT]:
    """Return the shortest unweighted path using breadth-first search."""

    _ensure_nodes_exist(storage, source, target)
    if source == target:
        return [source]

    queue = deque([source])
    predecessor: Dict[NodeT, Optional[NodeT]] = {source: None}

    while queue:
        current = queue.popleft()
        for child in storage.downstream(current):
            if child in predecessor:
                continue
            predecessor[child] = current
            if child == target:
                return _reconstruct_path(predecessor, target)
            queue.append(child)

    return []


def dijkstra_shortest_path(
    storage: GraphStorage[NodeT],
    source: NodeT,
    target: NodeT,
    weight: WeightFn,
) -> Dict[str, object]:
    """Return the lowest-cost directed path using Dijkstra's algorithm."""

    _ensure_nodes_exist(storage, source, target)
    if source == target:
        return {"path": [source], "distance": 0.0}

    distances: Dict[NodeT, float] = {source: 0.0}
    predecessor: Dict[NodeT, Optional[NodeT]] = {source: None}
    heap: List[Tuple[float, NodeT]] = [(0.0, source)]

    while heap:
        current_distance, current = heapq.heappop(heap)
        if current_distance > distances.get(current, float("inf")):
            continue
        if current == target:
            return {"path": _reconstruct_path(predecessor, target), "distance": current_distance}

        for child in storage.downstream(current):
            edge_weight = float(weight(current, child))
            if edge_weight < 0:
                raise ValueError("Dijkstra's algorithm does not support negative weights")
            new_distance = current_distance + edge_weight
            if new_distance < distances.get(child, float("inf")):
                distances[child] = new_distance
                predecessor[child] = current
                heapq.heappush(heap, (new_distance, child))

    return {"path": [], "distance": float("inf")}


class PathFinder(Generic[NodeT]):
    """Facade for shortest-path algorithms on directed graphs."""

    def __init__(self, storage: GraphStorage[NodeT]):
        self._storage = storage

    def shortest_path(self, source: NodeT, target: NodeT) -> List[NodeT]:
        return shortest_path(self._storage, source, target)

    def dijkstra_shortest_path(
        self,
        source: NodeT,
        target: NodeT,
        weight: WeightFn,
    ) -> Dict[str, object]:
        return dijkstra_shortest_path(self._storage, source, target, weight)


def _ensure_nodes_exist(storage: GraphStorage[NodeT], *nodes: NodeT) -> None:
    missing = [node for node in nodes if node not in storage]
    if missing:
        raise KeyError("one or more nodes do not exist in graph")


def _reconstruct_path(predecessor: Dict[NodeT, Optional[NodeT]], target: NodeT) -> List[NodeT]:
    path: List[NodeT] = []
    current: Optional[NodeT] = target
    while current is not None:
        path.append(current)
        current = predecessor[current]
    path.reverse()
    return path
