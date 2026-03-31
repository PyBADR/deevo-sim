"use client";

import React, { useEffect, useRef, useMemo } from "react";
import DeckGL from "@deck.gl/react";
import {
  HeatmapLayer,
  ArcLayer,
  PathLayer,
  ScatterplotLayer,
  IconLayer,
  ScreenGridLayer,
} from "@deck.gl/layers";
import type { MapEntity, LayerVisibility } from "@/lib/control-room-types";

interface DeckOverlayProps {
  entities: MapEntity[];
  layerVisibility: LayerVisibility;
  onSelectEntity?: (entity: MapEntity) => void;
  globePosition: { lat: number; lon: number };
}

export default function DeckOverlay({
  entities,
  layerVisibility,
  onSelectEntity,
  globePosition,
}: DeckOverlayProps) {
  const deckRef = useRef<any>(null);

  // Initial view state
  const initialViewState = {
    longitude: globePosition.lon,
    latitude: globePosition.lat,
    zoom: 2,
    pitch: 45,
    bearing: 0,
  };

  // Prepare heatmap data
  const heatmapData = useMemo(() => {
    if (!layerVisibility.heatmap) return [];
    return entities
      .filter((e) => e.riskScore && e.riskScore.overall > 0)
      .map((e) => ({
        position: [e.lon, e.lat],
        weight: e.riskScore.overall,
      }));
  }, [entities, layerVisibility.heatmap]);

  // Prepare arc data for flow lines between related entities
  const arcData = useMemo(() => {
    if (!layerVisibility.flowLines) return [];
    const arcs: any[] = [];

    entities.forEach((entity) => {
      if (entity.relatedEntities && entity.relatedEntities.length > 0) {
        entity.relatedEntities.forEach((relatedId) => {
          const relatedEntity = entities.find((e) => e.id === relatedId);
          if (relatedEntity) {
            arcs.push({
              sourcePosition: [entity.lon, entity.lat],
              targetPosition: [relatedEntity.lon, relatedEntity.lat],
              sourceId: entity.id,
              targetId: relatedEntity.id,
              impact: entity.riskScore?.overall || 0,
            });
          }
        });
      }
    });

    return arcs;
  }, [entities, layerVisibility.flowLines]);

  // Prepare scatterplot data for entity positions
  const scatterplotData = useMemo(() => {
    return entities.map((entity) => ({
      position: [entity.lon, entity.lat],
      color:
        entity.severity === "critical"
          ? [255, 68, 68]
          : entity.severity === "high"
            ? [255, 153, 0]
            : entity.severity === "medium"
              ? [255, 255, 0]
              : [0, 255, 136],
      size: Math.max(50, (entity.riskScore?.overall || 0) * 100),
      entity: entity,
    }));
  }, [entities]);

  // Icon data for specific entity types
  const iconData = useMemo(() => {
    const icons: any[] = [];

    entities.forEach((entity) => {
      let icon = "marker";
      if (entity.type === "airport") icon = "airport";
      else if (entity.type === "port") icon = "port";
      else if (entity.type === "flight") icon = "flight";
      else if (entity.type === "vessel") icon = "ship";
      else if (entity.type === "conflict_zone") icon = "danger";

      if (
        (entity.type === "airport" && layerVisibility.airports) ||
        (entity.type === "port" && layerVisibility.ports) ||
        (entity.type === "flight" && layerVisibility.flights) ||
        (entity.type === "vessel" && layerVisibility.vessels) ||
        (entity.type === "conflict_zone" && layerVisibility.riskZones)
      ) {
        icons.push({
          position: [entity.lon, entity.lat],
          icon: icon,
          size: 40,
          entity: entity,
        });
      }
    });

    return icons;
  }, [entities, layerVisibility]);

  // Create layers
  const layers = useMemo(
    () => [
      // Heatmap layer for overall risk distribution
      layerVisibility.heatmap &&
        new HeatmapLayer({
          id: "heatmap",
          data: heatmapData,
          getPosition: (d: any) => d.position,
          getWeight: (d: any) => d.weight,
          radiusPixels: 50,
          colorRange: [
            [0, 255, 136],
            [255, 200, 0],
            [255, 100, 0],
            [255, 50, 50],
          ],
          intensity: 1,
          threshold: 0.05,
          opacity: 0.6,
        }),

      // Arc layer for flow lines between entities
      layerVisibility.flowLines &&
        new ArcLayer({
          id: "arcs",
          data: arcData,
          getSourcePosition: (d: any) => d.sourcePosition,
          getTargetPosition: (d: any) => d.targetPosition,
          getSourceColor: (d: any) => [0, 255, 136],
          getTargetColor: (d: any) => [255, 68, 68],
          getWidth: (d: any) => Math.max(1, d.impact * 3),
          getHeight: (d: any) => 0.5,
          opacity: 0.4,
          pickable: true,
          onClick: (info) => {
            if (info.object?.sourceId) {
              const source = entities.find((e) => e.id === info.object.sourceId);
              if (source) onSelectEntity?.(source);
            }
          },
        }),

      // Scatterplot layer for entity positions and risk
      new ScatterplotLayer({
        id: "scatterplot",
        data: scatterplotData,
        getPosition: (d: any) => d.position,
        getRadius: (d: any) => d.size,
        getColor: (d: any) => d.color,
        opacity: 0.7,
        pickable: true,
        onClick: (info) => {
          if (info.object?.entity) {
            onSelectEntity?.(info.object.entity);
          }
        },
      }),

      // Icon layer for specific entity types
      new IconLayer({
        id: "icons",
        data: iconData,
        getPosition: (d: any) => d.position,
        getIcon: (d: any) => d.icon,
        getSize: (d: any) => d.size,
        sizeUnits: "pixels",
        sizeScale: 1,
        pickable: true,
        onClick: (info) => {
          if (info.object?.entity) {
            onSelectEntity?.(info.object.entity);
          }
        },
        iconAtlas:
          "https://raw.githubusercontent.com/visgl/deck.gl-data/master/website/icon-atlas.png",
        iconMapping: {
          marker: { x: 0, y: 0, width: 128, height: 128 },
          airport: { x: 128, y: 0, width: 128, height: 128 },
          port: { x: 256, y: 0, width: 128, height: 128 },
          flight: { x: 384, y: 0, width: 128, height: 128 },
          ship: { x: 512, y: 0, width: 128, height: 128 },
          danger: { x: 640, y: 0, width: 128, height: 128 },
        },
      }),

      // Screen grid layer for density visualization
      layerVisibility.heatmap &&
        new ScreenGridLayer({
          id: "screen-grid",
          data: scatterplotData,
          getPosition: (d: any) => d.position,
          cellSizePixels: 50,
          colorRange: [
            [0, 255, 136, 0],
            [0, 255, 136, 50],
            [255, 255, 0, 100],
            [255, 100, 0, 150],
            [255, 50, 50, 200],
          ],
          getWeight: (d: any) => d.size / 100,
          pickable: false,
          opacity: 0.3,
        }),
    ].filter(Boolean),
    [heatmapData, arcData, scatterplotData, iconData, layerVisibility]
  );

  return (
    <div className="absolute inset-0 pointer-events-none">
      <DeckGL
        ref={deckRef}
        initialViewState={initialViewState}
        controller={false}
        layers={layers}
        getTooltip={({ object }: any) => {
          if (object?.entity) {
            return {
              html: `<div class="text-xs bg-gray-900 text-white p-2 rounded">${object.entity.name}</div>`,
              style: {
                backgroundColor: "rgba(10, 10, 15, 0.9)",
                borderRadius: "4px",
                padding: "8px",
                border: "1px solid #00ff88",
              },
            };
          }
          return null;
        }}
      />
    </div>
  );
}
