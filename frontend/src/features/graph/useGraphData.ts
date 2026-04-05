"use client";

import { useState, useEffect, useCallback } from "react";
import { graphClient } from "@/lib/graph-client";
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
  error: string | null;
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
    error: null,
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
          setState((s) => ({
            ...s,
            nodes: nodesRes.nodes,
            edges: edgesRes.edges,
            totalNodes: nodesRes.total_graph_nodes,
            totalEdges: nodesRes.total_graph_edges,
            layers: nodesRes.layers,
            loading: false,
          }));
        }
      } catch (err) {
        if (!cancelled) {
          setState((s) => ({
            ...s,
            loading: false,
            error: err instanceof Error ? err.message : "Failed to load graph",
          }));
        }
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  // Filter by layer
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
    } catch (err) {
      setState((s) => ({
        ...s,
        loading: false,
        error: err instanceof Error ? err.message : "Filter failed",
      }));
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
    } catch (err) {
      setState((s) => ({
        ...s,
        scenarioLoading: false,
        error: err instanceof Error ? err.message : "Scenario run failed",
      }));
      return null;
    }
  }, []);

  return { ...state, filterByLayer, runScenario };
}
