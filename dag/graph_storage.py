from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Generic, Hashable, List, MutableMapping, MutableSet, Set, TypeVar


NodeT = TypeVar("NodeT", bound=Hashable)


@dataclass
class GraphStorage(Generic[NodeT]):
    """Owns adjacency indexes and keeps them internally consistent.

    The storage maintains both outbound and inbound adjacency indexes.
    Keeping both indexes synchronized makes predecessor lookup, reachability,
    deletion, and topological operations efficient without repeatedly
    rescanning the whole graph.
    """

    _downstream: MutableMapping[NodeT, MutableSet[NodeT]] = field(default_factory=dict)
    _predecessors: MutableMapping[NodeT, MutableSet[NodeT]] = field(default_factory=dict)

    def clear(self) -> None:
        self._downstream = {}
        self._predecessors = {}

    def __contains__(self, node: NodeT) -> bool:
        return node in self._downstream

    def __len__(self) -> int:
        return len(self._downstream)

    def add_node(self, node: NodeT) -> None:
        if node in self._downstream:
            raise KeyError("node %s already exists" % node)
        self._downstream[node] = set()
        self._predecessors[node] = set()

    def remove_node(self, node: NodeT) -> None:
        if node not in self._downstream:
            raise KeyError("node %s does not exist" % node)

        for predecessor in list(self._predecessors[node]):
            self._downstream[predecessor].remove(node)
        for downstream in list(self._downstream[node]):
            self._predecessors[downstream].remove(node)

        del self._downstream[node]
        del self._predecessors[node]

    def add_edge(self, source: NodeT, target: NodeT) -> None:
        self._downstream[source].add(target)
        self._predecessors[target].add(source)

    def remove_edge(self, source: NodeT, target: NodeT) -> None:
        if target not in self._downstream.get(source, set()):
            raise KeyError("this edge does not exist in graph")
        self._downstream[source].remove(target)
        self._predecessors[target].remove(source)

    def rename_node(self, old: NodeT, new: NodeT) -> None:
        if old not in self._downstream:
            raise KeyError("node %s does not exist" % old)
        if new in self._downstream and new != old:
            raise KeyError("node %s already exists" % new)
        if old == new:
            return

        downstream = self._downstream.pop(old)
        predecessors = self._predecessors.pop(old)

        self._downstream[new] = set(downstream)
        self._predecessors[new] = set(predecessors)

        for predecessor in predecessors:
            self._downstream[predecessor].remove(old)
            self._downstream[predecessor].add(new)

        for target in downstream:
            self._predecessors[target].remove(old)
            self._predecessors[target].add(new)

    def nodes(self) -> List[NodeT]:
        return list(self._downstream.keys())

    def downstream(self, node: NodeT) -> List[NodeT]:
        if node not in self._downstream:
            raise KeyError("node %s is not in graph" % node)
        return list(self._downstream[node])

    def downstream_set(self, node: NodeT) -> Set[NodeT]:
        if node not in self._downstream:
            raise KeyError("node %s is not in graph" % node)
        return set(self._downstream[node])

    def predecessors(self, node: NodeT) -> List[NodeT]:
        if node not in self._predecessors:
            raise KeyError("node %s is not in graph" % node)
        return list(self._predecessors[node])

    def predecessor_set(self, node: NodeT) -> Set[NodeT]:
        if node not in self._predecessors:
            raise KeyError("node %s is not in graph" % node)
        return set(self._predecessors[node])

    def leaves(self) -> List[NodeT]:
        return [node for node, edges in self._downstream.items() if not edges]

    def independent_nodes(self) -> List[NodeT]:
        return [node for node, dependencies in self._predecessors.items() if not dependencies]

    def clone_adjacency(self) -> Dict[NodeT, Set[NodeT]]:
        return {node: set(edges) for node, edges in self._downstream.items()}
