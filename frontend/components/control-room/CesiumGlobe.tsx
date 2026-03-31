"use client";

import React, { useEffect, useRef, forwardRef, useImperativeHandle } from "react";
import * as Cesium from "cesium";
import type { MapEntity, LayerVisibility } from "@/lib/control-room-types";

interface CesiumGlobeProps {
  entities: MapEntity[];
  layerVisibility: LayerVisibility;
  onSelectEntity?: (entity: MapEntity) => void;
  selectedEntityId?: string | null;
}

const CesiumGlobe = forwardRef<any, CesiumGlobeProps>(
  (
    { entities, layerVisibility, onSelectEntity, selectedEntityId },
    ref
  ) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const viewerRef = useRef<Cesium.Viewer | null>(null);
    const entityLayersRef = useRef<Map<string, Cesium.Entity>>(new Map());

    // Initialize Cesium viewer
    useEffect(() => {
      if (!containerRef.current) return;

      // Initialize Cesium Ion access token if needed
      if (!Cesium.Ion.defaultAccessToken) {
        Cesium.Ion.defaultAccessToken =
          process.env.NEXT_PUBLIC_CESIUM_TOKEN || "";
      }

      const viewer = new Cesium.Viewer(containerRef.current, {
        terrain: Cesium.Terrain.fromWorldTerrain(),
        baseLayerPicker: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        sceneModePicker: false,
        selectionIndicator: true,
        timeline: false,
        animation: false,
        fullscreenButton: false,
        vrButton: false,
        navigationHelpButton: false,
        navigationInstructionsInitiallyVisible: false,
        imageryProvider: Cesium.ImageryLayer.fromProviderAsync(
          Cesium.TileMapServiceImageryProvider.fromUrl(
            Cesium.ArcGisMapServerImageryProvider.fromUrl(
              "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer"
            )
          )
        ),
      });

      // Set initial camera position
      viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(0, 20, 15000000),
      });

      // Enable OSM buildings
      try {
        Cesium.Cesium3DTileset.fromUrl(
          "https://tile.openstreetmap.org/data/buildings/tileset.json",
          {
            skipLevelOfDetail: true,
          }
        )
          .then((tileset) => {
            viewer.scene.primitives.add(tileset);
          })
          .catch(() => {
            // Silently fail if OSM buildings unavailable
          });
      } catch {
        // Continue without buildings if unavailable
      }

      // Enable atmosphere and shadows
      viewer.scene.globe.enableLighting = true;
      viewer.scene.postProcessStages.fxaa.enabled = true;

      // Click handler for entity selection
      const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
      handler.setInputAction((click) => {
        const pickedObject = viewer.scene.pick(click.position);
        if (Cesium.defined(pickedObject)) {
          const cesiumEntity = pickedObject.id;
          if (cesiumEntity && cesiumEntity.entityData) {
            onSelectEntity?.(cesiumEntity.entityData);
          }
        }
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

      viewerRef.current = viewer;

      return () => {
        viewer.destroy();
        viewerRef.current = null;
      };
    }, [onSelectEntity]);

    // Update entity visualizations
    useEffect(() => {
      const viewer = viewerRef.current;
      if (!viewer) return;

      // Clear existing entities
      entityLayersRef.current.forEach((_, id) => {
        const entity = viewer.entities.getById(id);
        if (entity) {
          viewer.entities.removeById(id);
        }
      });
      entityLayersRef.current.clear();

      // Add entities based on visibility settings
      entities.forEach((entity) => {
        let shouldDisplay = false;

        switch (entity.type) {
          case "event":
            shouldDisplay = layerVisibility.events;
            break;
          case "airport":
            shouldDisplay = layerVisibility.airports;
            break;
          case "port":
            shouldDisplay = layerVisibility.ports;
            break;
          case "corridor":
            shouldDisplay = layerVisibility.corridors;
            break;
          case "flight":
            shouldDisplay = layerVisibility.flights;
            break;
          case "vessel":
            shouldDisplay = layerVisibility.vessels;
            break;
          case "conflict_zone":
            shouldDisplay = layerVisibility.riskZones;
            break;
        }

        if (!shouldDisplay) return;

        // Determine icon and color based on type and risk
        let iconUrl = "/icons/marker.png";
        let color = Cesium.Color.GREEN;

        if (entity.severity === "critical") {
          color = Cesium.Color.RED;
          iconUrl = "/icons/marker-critical.png";
        } else if (entity.severity === "high") {
          color = Cesium.Color.ORANGE;
          iconUrl = "/icons/marker-high.png";
        } else if (entity.severity === "medium") {
          color = Cesium.Color.YELLOW;
          iconUrl = "/icons/marker-medium.png";
        }

        // Create Cesium entity
        const cesiumEntity = viewer.entities.add({
          id: entity.id,
          position: Cesium.Cartesian3.fromDegrees(entity.lon, entity.lat),
          point: {
            pixelSize: 10,
            color: color,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2,
          },
          label: {
            text: entity.name,
            font: "12px sans-serif",
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            showBackground: true,
            backgroundColor: Cesium.Color.BLACK.withAlpha(0.7),
            pixelOffset: new Cesium.Cartesian2(0, -20),
          },
          entityData: entity,
          properties: {
            riskScore: entity.riskScore,
            type: entity.type,
            status: entity.status,
          },
        });

        entityLayersRef.current.set(entity.id, cesiumEntity);
      });
    }, [entities, layerVisibility]);

    // Highlight selected entity
    useEffect(() => {
      const viewer = viewerRef.current;
      if (!viewer) return;

      entityLayersRef.current.forEach((cesiumEntity, id) => {
        if (id === selectedEntityId) {
          cesiumEntity.point.pixelSize = 15;
          cesiumEntity.point.outlineWidth = 3;
        } else {
          cesiumEntity.point.pixelSize = 10;
          cesiumEntity.point.outlineWidth = 2;
        }
      });
    }, [selectedEntityId]);

    // Expose viewer for external use
    useImperativeHandle(ref, () => ({
      viewer: viewerRef.current,
      getCamera: () => viewerRef.current?.camera,
      flyTo: (lon: number, lat: number, height: number = 1000000) => {
        if (viewerRef.current) {
          viewerRef.current.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(lon, lat, height),
            duration: 3,
          });
        }
      },
    }));

    return (
      <div
        ref={containerRef}
        className="w-full h-full relative"
        style={{
          background: "#0a0a0f",
        }}
      />
    );
  }
);

CesiumGlobe.displayName = "CesiumGlobe";

export default CesiumGlobe;
