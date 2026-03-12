from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Generic, Hashable, Mapping as TypingMapping, Optional, Set, TypeVar

from .graph_connectivity import ConnectivityIndex
from .graph_ordering import TopologyIndex
from .graph_pathfinding import PathFinder
from .graph_reachability import ReachabilityIndex
from .graph_storage import GraphStorage
from .graph_validation import CycleValidator


NodeT = TypeVar("NodeT", bound=Hashable)


class DAG(Generic[NodeT]):
    """Directed acyclic graph with focused algorithm modules.

    Design:
    - `GraphStorage` owns adjacency and predecessor indexes
    - `CycleValidator` rejects edge mutations that would introduce cycles
    - `ReachabilityIndex` handles ancestry, descendants, path existence, and
      transitive closure
    - `TopologyIndex` handles topological order, layered scheduling,
      transitive reduction, and critical path
    - `ConnectivityIndex` exposes generic connectivity algorithms
    - `PathFinder` exposes shortest-path algorithms

    Core algorithms:
    - Incremental cycle prevention uses directed reachability before adding an
      edge.
    - Whole-graph ordering and validation use Kahn's algorithm.
    - Strong connectivity uses Tarjan's algorithm.
    - Unweighted shortest path uses breadth-first search.
    - Weighted shortest path uses Dijkstra's algorithm.
    """

    def __init__(self):
        self._storage = GraphStorage[NodeT]()
        self._validator = CycleValidator(self._storage)
        self._reachability = ReachabilityIndex(self._storage)
        self._topology = TopologyIndex(self._storage)
        self._connectivity = ConnectivityIndex(self._storage)
        self._pathfinder = PathFinder(self._storage)
        self.reset_graph()

    def add_node(self, node_name, graph=None):
        """Add a node if it does not already exist."""
        self._require_internal_graph(graph)
        self._storage.add_node(node_name)

    def add_node_if_not_exists(self, node_name, graph=None):
        try:
            self.add_node(node_name, graph=graph)
        except KeyError:
            pass

    def delete_node(self, node_name, graph=None):
        """Delete a node and all incident edges."""
        self._require_internal_graph(graph)
        self._storage.remove_node(node_name)

    def delete_node_if_exists(self, node_name, graph=None):
        try:
            self.delete_node(node_name, graph=graph)
        except KeyError:
            pass

    def add_edge(self, ind_node, dep_node, graph=None):
        """Add a directed edge after verifying that no cycle is introduced."""
        self._require_internal_graph(graph)
        self._ensure_nodes_exist(ind_node, dep_node)
        self._validator.ensure_edge_can_be_added(ind_node, dep_node)
        self._storage.add_edge(ind_node, dep_node)

    def delete_edge(self, ind_node, dep_node, graph=None):
        """Delete a directed edge."""
        self._require_internal_graph(graph)
        self._storage.remove_edge(ind_node, dep_node)

    def rename_edges(self, old_task_name, new_task_name, graph=None):
        """Rename a node and update all inbound and outbound references."""
        self._require_internal_graph(graph)
        self._storage.rename_node(old_task_name, new_task_name)

    def predecessors(self, node, graph=None):
        """Return direct predecessors of `node`."""
        self._require_internal_graph(graph)
        return self._storage.predecessors(node)

    def downstream(self, node, graph=None):
        """Return direct downstream nodes of `node`."""
        self._require_internal_graph(graph)
        return self._storage.downstream(node)

    def all_downstreams(self, node, graph=None):
        """Return all reachable downstream nodes in topological order."""
        self._require_internal_graph(graph)
        descendants = set(self.descendants(node))
        return [candidate for candidate in self.topological_sort() if candidate in descendants]

    def descendants(self, node):
        """Return all nodes reachable from `node`."""
        return self._reachability.descendants(node)

    def ancestors(self, node):
        """Return all nodes that can reach `node`."""
        return self._reachability.ancestors(node)

    def has_path(self, source, target):
        """Return whether a directed path exists from `source` to `target`."""
        return self._reachability.has_path(source, target)

    def transitive_closure(self):
        """Return the reachability set for every node in the graph."""
        return self._reachability.transitive_closure()

    def shortest_path(self, source, target):
        """Return the shortest unweighted path using breadth-first search."""
        return self._pathfinder.shortest_path(source, target)

    def dijkstra_shortest_path(self, source, target, weight):
        """Return the minimum-cost path using Dijkstra's algorithm."""
        return self._pathfinder.dijkstra_shortest_path(source, target, weight)

    def all_leaves(self, graph=None):
        """Return all leaves, defined as nodes with no outbound edges."""
        self._require_internal_graph(graph)
        return self._storage.leaves()

    def from_dict(self, graph_dict):
        """Reset the graph and build it from `{node: iterable_of_edges}`."""
        self.reset_graph()
        if not isinstance(graph_dict, Mapping):
            raise TypeError("graph_dict must be a mapping")

        for new_node in graph_dict.keys():
            self.add_node(new_node)

        for ind_node, dep_nodes in graph_dict.items():
            if not isinstance(dep_nodes, Iterable) or isinstance(dep_nodes, (str, bytes)):
                raise TypeError("dict values must be iterable collections of nodes")
            for dep_node in dep_nodes:
                self.add_edge(ind_node, dep_node)

    def reset_graph(self):
        """Restore the graph to an empty state."""
        self._storage.clear()

    def ind_nodes(self, graph=None):
        """Return nodes with no predecessors."""
        self._require_internal_graph(graph)
        return self._storage.independent_nodes()

    def validate(self, graph=None):
        """Validate acyclicity with topological sorting."""
        self._require_internal_graph(graph)
        if self.size() == 0:
            return (True, "valid")
        if len(self.ind_nodes()) == 0:
            return (False, "no independent nodes detected")
        try:
            self.topological_sort()
        except ValueError:
            return (False, "failed topological sort")
        return (True, "valid")

    def topological_sort(self, graph=None):
        """Return a topological ordering using Kahn's algorithm."""
        self._require_internal_graph(graph)
        return self._topology.topological_sort()

    def topological_levels(self):
        """Return nodes grouped into layered topological levels."""
        return self._topology.topological_levels()

    def transitive_reduction(self):
        """Return the adjacency map with redundant edges removed."""
        return self._topology.transitive_reduction()

    def critical_path(self, durations: Optional[TypingMapping[NodeT, float]] = None):
        """Return the longest weighted path through the DAG."""
        return self._topology.critical_path(durations=durations)

    def strongly_connected_components(self):
        """Return strongly connected components using Tarjan's algorithm."""
        return self._connectivity.strongly_connected_components()

    def weakly_connected_components(self):
        """Return weakly connected components while ignoring edge direction."""
        return self._connectivity.weakly_connected_components()

    def size(self):
        return len(self._storage)

    @property
    def graph(self):
        """Return a backward-compatible adjacency snapshot."""
        return self._storage.clone_adjacency()

    def _ensure_nodes_exist(self, *nodes) -> None:
        missing = [node for node in nodes if node not in self._storage]
        if missing:
            raise KeyError("one or more nodes do not exist in graph")

    def _require_internal_graph(self, graph: Optional[TypingMapping[NodeT, Set[NodeT]]]) -> None:
        if graph is not None:
            raise NotImplementedError(
                "Passing an external graph is no longer supported; mutate the DAG instance directly"
            )
