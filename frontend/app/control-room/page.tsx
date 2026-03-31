"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import CesiumGlobe from "@/components/control-room/CesiumGlobe";
import DeckOverlay from "@/components/control-room/DeckOverlay";
import ScenarioPanel from "@/components/control-room/ScenarioPanel";
import EntityDrawer from "@/components/control-room/EntityDrawer";
import ExplanationPanel from "@/components/control-room/ExplanationPanel";
import LayerControls from "@/components/control-room/LayerControls";
import TimelineBar from "@/components/control-room/TimelineBar";
import StatusBar from "@/components/control-room/StatusBar";
import {
  fetchScenarios,
  fetchEntities,
  fetchSystemHealth,
  fetchGCCMetrics,
  runScenario,
  fetchExplanation,
} from "@/lib/api";
import type {
  ScenarioTemplate,
  MapEntity,
  ScenarioResult,
  PanelState,
  SystemHealth,
  LayerVisibility,
  ExplanationOutput,
} from "@/lib/control-room-types";
import { getLanguage } from "@/lib/i18n";
import { ChevronLeft, ChevronRight } from "lucide-react";

export default function ControlRoomPage() {
  // State management
  const [language, setLanguage] = useState<"en" | "ar">("en");
  const [scenarios, setScenarios] = useState<ScenarioTemplate[]>([]);
  const [entities, setEntities] = useState<MapEntity[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [panelState, setPanelState] = useState<PanelState>({
    leftOpen: true,
    rightOpen: true,
    bottomOpen: true,
    selectedEntity: null,
    selectedScenario: null,
  });
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>({
    events: true,
    airports: true,
    ports: true,
    corridors: true,
    flights: true,
    vessels: true,
    heatmap: true,
    riskZones: true,
    flowLines: true,
  });
  const [scenarioResult, setScenarioResult] = useState<ScenarioResult | null>(
    null
  );
  const [explanation, setExplanation] = useState<ExplanationOutput | null>(null);
  const [loading, setLoading] = useState(true);
  const [scenarioRunning, setScenarioRunning] = useState(false);
  const [selectedEntityData, setSelectedEntityData] = useState<MapEntity | null>(
    null
  );
  const globeRef = useRef<any>(null);

  // Initialize language
  useEffect(() => {
    const lang = getLanguage();
    setLanguage(lang as "en" | "ar");
  }, []);

  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [scenariosData, entitiesData, healthData] = await Promise.all([
          fetchScenarios(),
          fetchEntities(),
          fetchSystemHealth(),
        ]);

        setScenarios(scenariosData);
        setEntities(entitiesData);
        setSystemHealth(healthData);
      } catch (error) {
        console.error("Failed to load Control Room data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Handle scenario execution
  const handleRunScenario = useCallback(
    async (scenarioId: string, severity: number) => {
      try {
        setScenarioRunning(true);
        setPanelState((prev) => ({
          ...prev,
          selectedScenario: scenarioId,
        }));

        const result = await runScenario(scenarioId, severity);
        setScenarioResult(result);

        // Fetch explanation for the scenario result
        if (result.runId) {
          try {
            const explanationData = await fetchExplanation(result.runId);
            setExplanation(explanationData);
          } catch (error) {
            console.error("Failed to fetch explanation:", error);
          }
        }
      } catch (error) {
        console.error("Failed to run scenario:", error);
      } finally {
        setScenarioRunning(false);
      }
    },
    []
  );

  // Handle entity selection
  const handleSelectEntity = useCallback((entity: MapEntity | null) => {
    setSelectedEntityData(entity);
    setPanelState((prev) => ({
      ...prev,
      selectedEntity: entity?.id || null,
    }));
  }, []);

  // Handle layer visibility toggle
  const handleToggleLayer = useCallback(
    (layer: keyof LayerVisibility) => {
      setLayerVisibility((prev) => ({
        ...prev,
        [layer]: !prev[layer],
      }));
    },
    []
  );

  // Panel toggle handlers
  const toggleLeftPanel = useCallback(() => {
    setPanelState((prev) => ({
      ...prev,
      leftOpen: !prev.leftOpen,
    }));
  }, []);

  const toggleRightPanel = useCallback(() => {
    setPanelState((prev) => ({
      ...prev,
      rightOpen: !prev.rightOpen,
    }));
  }, []);

  const toggleBottomPanel = useCallback(() => {
    setPanelState((prev) => ({
      ...prev,
      bottomOpen: !prev.bottomOpen,
    }));
  }, []);

  const isRTL = language === "ar";

  if (loading) {
    return (
      <div className="w-full h-screen ds-bg ds-text flex items-center justify-center">
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 border-2 ds-border border-t-ds-accent rounded-full mx-auto mb-4"
          />
          <p className="text-sm ds-text-secondary">
            {language === "en"
              ? "Initializing Control Room..."
              : "جاري تهيئة غرفة التحكم..."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="w-full h-screen ds-bg flex overflow-hidden"
      dir={isRTL ? "rtl" : "ltr"}
    >
      {/* Status Bar (Top) */}
      <div className="absolute top-0 left-0 right-0 z-30">
        <StatusBar
          systemHealth={systemHealth}
          scenarioRunning={scenarioRunning}
          activeScenarioName={
            scenarios.find((s) => s.id === panelState.selectedScenario)
              ?.[language === "en" ? "name" : "nameAr"] || null
          }
          language={language}
        />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 relative flex" style={{ marginTop: "60px" }}>
        {/* Left Panel - Entity List & Layer Controls */}
        <AnimatePresence initial={false}>
          {panelState.leftOpen && (
            <motion.div
              initial={{ [isRTL ? "right" : "x"]: -400 }}
              animate={{ [isRTL ? "right" : "x"]: 0 }}
              exit={{ [isRTL ? "right" : "x"]: -400 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="w-96 ds-bg-panel border-r ds-border flex flex-col overflow-hidden"
            >
              {/* Layer Controls */}
              <div className="flex-1 overflow-y-auto">
                <LayerControls
                  visibility={layerVisibility}
                  onToggle={handleToggleLayer}
                  language={language}
                />
              </div>

              {/* Entity List */}
              <div className="flex-1 overflow-y-auto border-t ds-border">
                <div className="p-4 space-y-2">
                  <h3 className="text-xs font-semibold uppercase ds-text-secondary tracking-wider mb-3">
                    {language === "en" ? "Entities" : "الكيانات"}
                  </h3>
                  {entities.map((entity) => (
                    <motion.button
                      key={entity.id}
                      onClick={() => handleSelectEntity(entity)}
                      whileHover={{ x: isRTL ? -2 : 2 }}
                      className={`w-full text-left p-3 rounded text-sm transition-colors ${
                        selectedEntityData?.id === entity.id
                          ? "ds-bg-accent/20 ds-border border ds-border-accent"
                          : "ds-bg-panel border ds-border-secondary/30 hover:ds-border-accent/50"
                      }`}
                    >
                      <div className="font-medium">
                        {language === "en" ? entity.name : entity.nameAr}
                      </div>
                      <div className="text-xs ds-text-secondary mt-1">
                        {entity.type}
                      </div>
                    </motion.button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Center - 3D Globe with Deck.gl Overlay */}
        <div className="flex-1 relative overflow-hidden">
          <CesiumGlobe
            ref={globeRef}
            entities={entities}
            layerVisibility={layerVisibility}
            onSelectEntity={handleSelectEntity}
            selectedEntityId={selectedEntityData?.id}
          />
          <DeckOverlay
            entities={entities}
            layerVisibility={layerVisibility}
            onSelectEntity={handleSelectEntity}
            globePosition={{ lat: 0, lon: 0 }}
          />

          {/* Left Panel Toggle */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleLeftPanel}
            className={`absolute ${
              isRTL ? "right-2" : "left-2"
            } top-1/2 -translate-y-1/2 z-20 ds-bg-panel hover:ds-bg-accent/20 p-2 rounded border ds-border transition-colors`}
          >
            <ChevronRight
              size={18}
              className={isRTL ? "rotate-180" : ""}
              style={{ color: "#00ff88" }}
            />
          </motion.button>

          {/* Right Panel Toggle */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleRightPanel}
            className={`absolute ${
              isRTL ? "left-2" : "right-2"
            } top-1/2 -translate-y-1/2 z-20 ds-bg-panel hover:ds-bg-accent/20 p-2 rounded border ds-border transition-colors`}
          >
            <ChevronLeft
              size={18}
              className={isRTL ? "rotate-180" : ""}
              style={{ color: "#00ff88" }}
            />
          </motion.button>

          {/* Bottom Panel Toggle */}
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={toggleBottomPanel}
            className="absolute bottom-2 left-1/2 -translate-x-1/2 z-20 ds-bg-panel hover:ds-bg-accent/20 p-2 rounded border ds-border transition-colors"
          >
            <div className="text-xs ds-text-secondary">
              {panelState.bottomOpen ? "▼" : "▲"}
            </div>
          </motion.button>
        </div>

        {/* Right Panel - Scenario & Explanation */}
        <AnimatePresence initial={false}>
          {panelState.rightOpen && (
            <motion.div
              initial={{ [isRTL ? "left" : "x"]: 400 }}
              animate={{ [isRTL ? "left" : "x"]: 0 }}
              exit={{ [isRTL ? "left" : "x"]: 400 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="w-96 ds-bg-panel border-l ds-border flex flex-col overflow-hidden"
            >
              {/* Scenario Panel */}
              <div className="flex-1 overflow-y-auto border-b ds-border">
                <ScenarioPanel
                  scenarios={scenarios}
                  onRunScenario={handleRunScenario}
                  loading={scenarioRunning}
                  result={scenarioResult}
                  language={language}
                />
              </div>

              {/* Explanation Panel */}
              {explanation && (
                <div className="flex-1 overflow-y-auto">
                  <ExplanationPanel
                    explanation={explanation}
                    language={language}
                  />
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Panel - Timeline */}
      <AnimatePresence initial={false}>
        {panelState.bottomOpen && (
          <motion.div
            initial={{ y: 200 }}
            animate={{ y: 0 }}
            exit={{ y: 200 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="absolute bottom-0 left-0 right-0 h-48 ds-bg-panel border-t ds-border flex flex-col overflow-hidden z-20"
          >
            <TimelineBar
              entities={entities}
              scenarioResult={scenarioResult}
              language={language}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Entity Details Drawer */}
      <AnimatePresence>
        {selectedEntityData && (
          <EntityDrawer
            entity={selectedEntityData}
            relatedEntities={entities.filter((e) =>
              selectedEntityData.relatedEntities?.includes(e.id)
            )}
            onClose={() => handleSelectEntity(null)}
            language={language}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
