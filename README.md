# Directed Acyclic Graph

This project provides a directed acyclic graph (`DAG`) implementation with a small set of graph algorithms built around a clean public API.

The code is organized so that:
- `dag/` exposes the installable Python package
- storage, validation, reachability, ordering, connectivity, and pathfinding are split into focused modules

## Installation

Install the package from the project root:

```bash
pip install .
```

After installation:

```python
from dag import DAG, DAGValidationError
```

## Features

- add, delete, and rename nodes
- add and delete directed edges
- cycle prevention on edge insertion
- topological sorting
- layered topological levels
- reachability queries
- ancestor and descendant queries
- transitive closure
- transitive reduction
- critical path analysis
- shortest path on unweighted graphs
- Dijkstra shortest path on weighted graphs
- strongly connected components
- weakly connected components

## File Layout

- `dag/__init__.py`: package exports
- `dag/core.py`: public DAG API
- `dag/graph_storage.py`: adjacency and predecessor indexes
- `dag/graph_validation.py`: cycle prevention
- `dag/graph_reachability.py`: reachability and ancestry algorithms
- `dag/graph_ordering.py`: topological and DAG-specific algorithms
- `dag/graph_connectivity.py`: connectivity algorithms
- `dag/graph_pathfinding.py`: shortest-path algorithms
- `pyproject.toml`: package metadata for `pip install`

## Basic Usage

```python
from dag import DAG

graph = DAG()

graph.add_node("build")
graph.add_node("test")
graph.add_node("deploy")

graph.add_edge("build", "test")
graph.add_edge("test", "deploy")

print(graph.topological_sort())
# ['build', 'test', 'deploy']
```

## Building From a Dictionary

Use `from_dict` when you already have an adjacency mapping.

```python
from dag import DAG

graph = DAG()
graph.from_dict(
    {
        "build": ["test"],
        "test": ["deploy"],
        "deploy": [],
    }
)

print(graph.graph)
```

Each key is a node. Each value is an iterable of outbound edges.

## Core Mutations

### Add a node

```python
graph.add_node("package")
```

### Add a node if missing

```python
graph.add_node_if_not_exists("package")
```

### Delete a node

```python
graph.delete_node("package")
```

### Add an edge

```python
graph.add_edge("build", "test")
```

If the edge would create a cycle, the code raises `DAGValidationError`.

```python
from dag import DAG, DAGValidationError

graph = DAG()
graph.from_dict({"a": ["b"], "b": []})

try:
    graph.add_edge("b", "a")
except DAGValidationError:
    print("cycle rejected")
```

### Delete an edge

```python
graph.delete_edge("build", "test")
```

### Rename a node

```python
graph.rename_edges("deploy", "release")
```

This updates the node itself and all connected inbound and outbound references.

## Querying the Graph

### Direct relationships

```python
graph.predecessors("deploy")
graph.downstream("build")
graph.all_leaves()
graph.ind_nodes()
graph.size()
```

### Reachability

```python
graph.descendants("build")
graph.ancestors("deploy")
graph.has_path("build", "deploy")
graph.transitive_closure()
```

`transitive_closure()` returns a dictionary where each node maps to the set of all reachable nodes.

## DAG Algorithms

### Topological sort

```python
graph.topological_sort()
```

This uses Kahn's algorithm.

### Topological levels

```python
graph.topological_levels()
```

This groups nodes into execution stages. Nodes in the same level can run in parallel if your application allows it.

Example result:

```python
[
    ["build"],
    ["test", "lint"],
    ["deploy"],
]
```

### Transitive reduction

```python
reduced = graph.transitive_reduction()
```

This removes redundant edges while preserving reachability.

For example, if `a -> b`, `b -> c`, and `a -> c`, the edge `a -> c` is redundant and can be removed in the reduced graph.

### Critical path

```python
result = graph.critical_path(
    {
        "build": 2,
        "test": 4,
        "deploy": 1,
    }
)

print(result["path"])
print(result["duration"])
```

If no durations are provided, each node defaults to duration `1.0`.

The return value contains:
- `path`: the longest path through the DAG
- `duration`: total duration of that path
- `distances`: longest accumulated duration to each node

## Pathfinding

### Shortest path in an unweighted directed graph

```python
graph.shortest_path("build", "deploy")
```

This uses breadth-first search and returns the path as a list of nodes.

### Dijkstra shortest path in a weighted directed graph

```python
weights = {
    ("build", "test"): 2,
    ("build", "lint"): 1,
    ("lint", "deploy"): 5,
    ("test", "deploy"): 2,
}

result = graph.dijkstra_shortest_path(
    "build",
    "deploy",
    lambda source, target: weights[(source, target)],
)

print(result["path"])
print(result["distance"])
```

The weight function must return a non-negative number for each edge.

## Connectivity Algorithms

These are general directed-graph algorithms and are included for analysis, even though a valid DAG will normally have only singleton strongly connected components.

### Strongly connected components

```python
graph.strongly_connected_components()
```

This uses Tarjan's algorithm.

### Weakly connected components

```python
graph.weakly_connected_components()
```

This ignores edge direction and groups nodes by undirected connectivity.

## Validation

```python
graph.validate()
```

Returns a tuple:

```python
(True, "valid")
```

Validation relies on topological sorting. If a graph cannot be fully topologically sorted, it contains a cycle.

## Notes

- This implementation is designed for in-memory use.
- The `graph` property returns a snapshot of the adjacency structure.
- Passing a separate `graph=` object into methods is not supported in the refactored design.
- Node values must be hashable.

## Example

```python
from dag import DAG

graph = DAG()
graph.from_dict(
    {
        "a": ["b", "c"],
        "b": ["d", "e"],
        "c": ["d"],
        "d": ["f"],
        "e": [],
        "f": [],
    }
)

print("topological sort:", graph.topological_sort())
print("levels:", graph.topological_levels())
print("descendants of a:", graph.descendants("a"))
print("ancestors of f:", graph.ancestors("f"))
print("has path a -> f:", graph.has_path("a", "f"))
print("transitive reduction:", graph.transitive_reduction())
print("critical path:", graph.critical_path())
print("shortest path a -> f:", graph.shortest_path("a", "f"))
print("weakly connected components:", graph.weakly_connected_components())
```
