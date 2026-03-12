# Frontend

This folder contains a React frontend for interacting with the DAG backend API.

## Features

- graph list and graph creation
- custom SVG graph visualization
- click-to-select nodes and edges
- drag nodes to rearrange the view
- click one node, then another to create an edge directly from the graph
- add and delete nodes
- add and delete edges
- graph summary and validation status
- execution of topology, reachability, pathfinding, connectivity, and critical-path algorithms

## Configuration

Set the backend base URL with:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

If not set, the app defaults to `http://localhost:8000`.

## Run

Install dependencies, then start the app:

```bash
npm install
npm run dev
```

If PowerShell blocks `npm`, use `npm.cmd` or run the commands in another shell.
