# Backend API

This folder contains a backend service that exposes the installed `dag` package through an HTTP API.

The backend is designed for frontend graph visualization tools that need to:
- create and manage graphs
- mutate nodes and edges
- inspect graph structure
- run DAG and directed-graph algorithms

## Stack

- FastAPI for the HTTP API
- Pydantic for request and response contracts
- an in-memory graph registry for runtime state

## Run

Install backend dependencies in your virtual environment, then run:

```bash
uvicorn backend.app.main:app --reload --port 8003
```

## Environment Variables

- `DAG_API_TITLE`: API title
- `DAG_API_VERSION`: API version
- `DAG_API_CORS_ORIGINS`: comma-separated list of allowed origins
- `DAG_API_CREATE_DEFAULT_GRAPH`: `true` or `false`
- `DAG_API_DEFAULT_GRAPH_ID`: default graph identifier

## API Overview

- `GET /health`
- `GET /graphs`
- `POST /graphs`
- `GET /graphs/{graph_id}`
- `DELETE /graphs/{graph_id}`
- `POST /graphs/{graph_id}/reset`
- `POST /graphs/{graph_id}/nodes`
- `DELETE /graphs/{graph_id}/nodes/{node_id}`
- `POST /graphs/{graph_id}/edges`
- `DELETE /graphs/{graph_id}/edges`
- `GET /graphs/{graph_id}/summary`
- `GET /graphs/{graph_id}/topology/topological-sort`
- `GET /graphs/{graph_id}/topology/topological-levels`
- `GET /graphs/{graph_id}/topology/transitive-reduction`
- `GET /graphs/{graph_id}/reachability/transitive-closure`
- `GET /graphs/{graph_id}/reachability/descendants/{node_id}`
- `GET /graphs/{graph_id}/reachability/ancestors/{node_id}`
- `GET /graphs/{graph_id}/reachability/has-path`
- `POST /graphs/{graph_id}/pathfinding/shortest-path`
- `POST /graphs/{graph_id}/pathfinding/dijkstra`
- `POST /graphs/{graph_id}/analysis/critical-path`
- `GET /graphs/{graph_id}/connectivity/strongly-connected-components`
- `GET /graphs/{graph_id}/connectivity/weakly-connected-components`

## Notes

- The backend currently stores graphs in memory.
- A restart clears all graph state.
- Node IDs are modeled as strings at the API boundary for JSON compatibility.
