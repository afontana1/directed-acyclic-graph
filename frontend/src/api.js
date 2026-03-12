const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8003";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep the default message if the server has no JSON error body.
    }
    throw new Error(detail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  baseUrl: API_BASE_URL,
  getGraphs: () => request("/graphs"),
  createGraph: (payload) =>
    request("/graphs", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getGraph: (graphId) => request(`/graphs/${encodeURIComponent(graphId)}`),
  deleteGraph: (graphId) =>
    request(`/graphs/${encodeURIComponent(graphId)}`, {
      method: "DELETE",
    }),
  resetGraph: (graphId, payload) =>
    request(`/graphs/${encodeURIComponent(graphId)}/reset`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  addNode: (graphId, payload) =>
    request(`/graphs/${encodeURIComponent(graphId)}/nodes`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateNodeWeight: (graphId, nodeId, payload) =>
    request(`/graphs/${encodeURIComponent(graphId)}/nodes/${encodeURIComponent(nodeId)}/weight`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteNode: (graphId, nodeId) =>
    request(`/graphs/${encodeURIComponent(graphId)}/nodes/${encodeURIComponent(nodeId)}`, {
      method: "DELETE",
    }),
  addEdge: (graphId, payload) =>
    request(`/graphs/${encodeURIComponent(graphId)}/edges`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  deleteEdge: (graphId, payload) =>
    request(`/graphs/${encodeURIComponent(graphId)}/edges`, {
      method: "DELETE",
      body: JSON.stringify(payload),
    }),
  getTopologicalSort: (graphId) =>
    request(`/graphs/${encodeURIComponent(graphId)}/topology/topological-sort`),
  getTopologicalLevels: (graphId) =>
    request(`/graphs/${encodeURIComponent(graphId)}/topology/topological-levels`),
  getTransitiveReduction: (graphId) =>
    request(`/graphs/${encodeURIComponent(graphId)}/topology/transitive-reduction`),
  getTransitiveClosure: (graphId) =>
    request(`/graphs/${encodeURIComponent(graphId)}/reachability/transitive-closure`),
  getDescendants: (graphId, nodeId) =>
    request(`/graphs/${encodeURIComponent(graphId)}/reachability/descendants/${encodeURIComponent(nodeId)}`),
  getAncestors: (graphId, nodeId) =>
    request(`/graphs/${encodeURIComponent(graphId)}/reachability/ancestors/${encodeURIComponent(nodeId)}`),
  getHasPath: (graphId, source, target) =>
    request(
      `/graphs/${encodeURIComponent(graphId)}/reachability/has-path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}`,
    ),
  getShortestPath: (graphId, payload) =>
    request(`/graphs/${encodeURIComponent(graphId)}/pathfinding/shortest-path`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getDijkstraPath: (graphId, payload) =>
    request(`/graphs/${encodeURIComponent(graphId)}/pathfinding/dijkstra`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getCriticalPath: (graphId, payload) =>
    request(`/graphs/${encodeURIComponent(graphId)}/analysis/critical-path`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getStrongComponents: (graphId) =>
    request(`/graphs/${encodeURIComponent(graphId)}/connectivity/strongly-connected-components`),
  getWeakComponents: (graphId) =>
    request(`/graphs/${encodeURIComponent(graphId)}/connectivity/weakly-connected-components`),
};
