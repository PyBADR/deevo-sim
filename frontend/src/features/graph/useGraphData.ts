"use client";

import { useState, useEffect, useCallback } from "react";
import { graphClient } from "@/lib/graph-client";
import { deriveGraphCapabilityFromLoad } from "@/lib/capabilities";
import type {
  KnowledgeGraphNode,
  KnowledgeGraphEdge,
  GraphLayer,
  ScenarioImpactResult,
} from "@/types/observatory";

export interface GraphDataState {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
  loading: boolean;
  /**
   * Explicit capability flag — null while loading, true/false after.
   * False when edges = 0 (disconnected graph has no propagation paths)
   * or when the graph endpoint is unreachable.
   * Pages MUST check this before attempting to render GraphCanvas.
   */
  graphSupported: boolean | null;
  totalNodes: number;
  totalEdges: number;
  layers: string[];
  activeLayer: GraphLayer | null;
  scenarioResult: ScenarioImpactResult | null;
  scenarioLoading: boolean;
}

export function useGraphData() {
  const [state, setState] = useState<GraphDataState>({
    nodes: [],
    edges: [],
    loading: true,
    graphSupported: null,
    totalNodes: 0,
    totalEdges: 0,
    layers: [],
    activeLayer: null,
    scenarioResult: null,
    scenarioLoading: false,
  });

  // Load full graph on mount
  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [nodesRes, edgesRes] = await Promise.all([
          graphClient.nodes(),
          graphClient.edges(),
        ]);
        if (!cancelled) {
          const supported = deriveGraphCapabilityFromLoad(
            nodesRes.nodes.length,
            edgesRes.edges.length
          );
          setState((s) => ({
            ...s,
            nodes: nodesRes.nodes,
            edges: edgesRes.edges,
            totalNodes: nodesRes.total_graph_nodes,
            totalEdges: nodesRes.total_graph_edges,
            layers: nodesRes.layers,
            loading: false,
            // Capability gating: false when edges absent (no propagation paths)
            graphSupported: supported,
          }));
        }
      } catch {
        // Load failed — capability not supported, not a generic error
        if (!cancelled) {
          setState((s) => ({
            ...s,
            loading: false,
            graphSupported: false,
          }));
        }
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  // Filter by layer — only callable when graphSupported = true
  const filterByLayer = useCallback(async (layer: GraphLayer | null) => {
    setState((s) => ({ ...s, loading: true, activeLayer: layer }));
    try {
      const [nodesRes, edgesRes] = await Promise.all([
        layer ? graphClient.nodes(layer) : graphClient.nodes(),
        layer ? graphClient.edges(layer) : graphClient.edges(),
      ]);
      setState((s) => ({
        ...s,
        nodes: nodesRes.nodes,
        edges: edgesRes.edges,
        loading: false,
      }));
    } catch {
      // Filter failed — don't change graphSupported, just stop loading
      setState((s) => ({ ...s, loading: false }));
    }
  }, []);

  // Run scenario impact
  const runScenario = useCallback(async (scenarioId: string, severity = 0.7) => {
    setState((s) => ({ ...s, scenarioLoading: true }));
    try {
      const result = await graphClient.scenarioImpacts(scenarioId, severity);
      setState((s) => ({
        ...s,
        scenarioResult: result,
        scenarioLoading: false,
      }));
      return result;
    } catch {
      setState((s) => ({ ...s, scenarioLoading: false }));
      return null;
    }
  }, []);

  return { ...state, filterByLayer, runScenario };
}
