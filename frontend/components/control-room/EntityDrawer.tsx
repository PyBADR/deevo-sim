"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, MapPin, AlertCircle, Link } from "lucide-react";
import type { MapEntity } from "@/lib/control-room-types";

interface EntityDrawerProps {
  entity: MapEntity;
  relatedEntities: MapEntity[];
  onClose: () => void;
  language: "en" | "ar";
}

export default function EntityDrawer({
  entity,
  relatedEntities,
  onClose,
  language,
}: EntityDrawerProps) {
  const isRTL = language === "ar";

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 z-40"
        onClick={onClose}
      />
      <motion.div
        initial={{ [isRTL ? "right" : "x"]: -400 }}
        animate={{ [isRTL ? "right" : "x"]: 0 }}
        exit={{ [isRTL ? "right" : "x"]: -400 }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        onClick={(e) => e.stopPropagation()}
        className={`fixed top-0 ${
          isRTL ? "right-0" : "left-0"
        } h-screen w-96 ds-bg-panel border-r ds-border flex flex-col z-50`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b ds-border">
          <div className="flex-1">
            <h2 className="font-semibold text-base leading-tight">
              {language === "en" ? entity.name : entity.nameAr}
            </h2>
            <p className="text-xs ds-text-secondary mt-1 uppercase tracking-wider">
              {entity.type}
            </p>
          </div>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
            onClick={onClose}
            className="p-2 hover:ds-bg-accent/20 rounded transition-colors"
          >
            <X size={18} />
          </motion.button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Location */}
          <div>
            <div className="flex items-center gap-2 text-xs uppercase tracking-wider ds-text-secondary mb-2">
              <MapPin size={14} />
              {language === "en" ? "Location" : "الموقع"}
            </div>
            <div className="space-y-1 text-sm">
              <div className="font-mono">
                {entity.lat.toFixed(4)}, {entity.lon.toFixed(4)}
              </div>
              <div className="text-xs ds-text-secondary">
                {entity.description || entity.descriptionAr}
              </div>
            </div>
          </div>

          {/* Risk Assessment */}
          <div>
            <div className="flex items-center gap-2 text-xs uppercase tracking-wider ds-text-secondary mb-3">
              <AlertCircle size={14} />
              {language === "en" ? "Risk Assessment" : "تقييم المخاطر"}
            </div>
            <div className="space-y-2">
              {/* Overall Risk */}
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ delay: 0.1 }}
                className="space-y-1"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="ds-text-secondary">
                    {language === "en" ? "Overall Risk" : "المخاطر الكلية"}
                  </span>
                  <span className="font-semibold">
                    {(entity.riskScore.overall * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-ds-panel/50 rounded-full h-2 overflow-hidden border ds-border-secondary/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${entity.riskScore.overall * 100}%` }}
                    transition={{ delay: 0.2, duration: 0.5 }}
                    className="h-full bg-ds-accent"
                  />
                </div>
              </motion.div>

              {/* Disruption Score */}
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ delay: 0.15 }}
                className="space-y-1"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="ds-text-secondary">
                    {language === "en" ? "Disruption" : "الاضطراب"}
                  </span>
                  <span className="font-semibold">
                    {(entity.riskScore.disruption * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-ds-panel/50 rounded-full h-2 overflow-hidden border ds-border-secondary/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${entity.riskScore.disruption * 100}%` }}
                    transition={{ delay: 0.25, duration: 0.5 }}
                    style={{ backgroundColor: "#ff9900" }}
                    className="h-full"
                  />
                </div>
              </motion.div>

              {/* Probability */}
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ delay: 0.2 }}
                className="space-y-1"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="ds-text-secondary">
                    {language === "en" ? "Probability" : "الاحتمالية"}
                  </span>
                  <span className="font-semibold">
                    {(entity.riskScore.probability * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-ds-panel/50 rounded-full h-2 overflow-hidden border ds-border-secondary/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${entity.riskScore.probability * 100}%` }}
                    transition={{ delay: 0.3, duration: 0.5 }}
                    style={{ backgroundColor: "#ffff00" }}
                    className="h-full"
                  />
                </div>
              </motion.div>

              {/* Velocity */}
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ delay: 0.25 }}
                className="space-y-1"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="ds-text-secondary">
                    {language === "en" ? "Velocity" : "السرعة"}
                  </span>
                  <span className="font-semibold">
                    {(entity.riskScore.velocity * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-ds-panel/50 rounded-full h-2 overflow-hidden border ds-border-secondary/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${entity.riskScore.velocity * 100}%` }}
                    transition={{ delay: 0.35, duration: 0.5 }}
                    style={{ backgroundColor: "#ff6666" }}
                    className="h-full"
                  />
                </div>
              </motion.div>

              {/* Scale */}
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: "100%" }}
                transition={{ delay: 0.3 }}
                className="space-y-1"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="ds-text-secondary">
                    {language === "en" ? "Scale" : "الحجم"}
                  </span>
                  <span className="font-semibold">
                    {(entity.riskScore.scale * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-ds-panel/50 rounded-full h-2 overflow-hidden border ds-border-secondary/30">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${entity.riskScore.scale * 100}%` }}
                    transition={{ delay: 0.4, duration: 0.5 }}
                    style={{ backgroundColor: "#ff4488" }}
                    className="h-full"
                  />
                </div>
              </motion.div>
            </div>
          </div>

          {/* Status */}
          <div>
            <div className="text-xs uppercase tracking-wider ds-text-secondary mb-2">
              {language === "en" ? "Status" : "الحالة"}
            </div>
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className={`inline-block px-2 py-1 rounded text-xs font-semibold ${
                entity.status === "active"
                  ? "bg-green-500/20 text-green-400"
                  : entity.status === "alert"
                    ? "bg-orange-500/20 text-orange-400"
                    : entity.status === "critical"
                      ? "bg-red-500/20 text-red-400"
                      : "bg-gray-500/20 text-gray-400"
              }`}
            >
              {entity.status?.toUpperCase()}
            </motion.span>
          </div>

          {/* Related Entities */}
          {relatedEntities.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-xs uppercase tracking-wider ds-text-secondary mb-2">
                <Link size={14} />
                {language === "en"
                  ? "Connected Entities"
                  : "الكيانات المتصلة"}
              </div>
              <div className="space-y-2">
                {relatedEntities.map((related) => (
                  <motion.div
                    key={related.id}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="p-2 rounded ds-bg-panel/50 border ds-border-secondary/30 hover:border-ds-accent/50 transition-colors"
                  >
                    <div className="text-sm font-medium">
                      {language === "en" ? related.name : related.nameAr}
                    </div>
                    <div className="text-xs ds-text-secondary mt-1">
                      {related.type}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Events */}
          {entity.recentEvents && entity.recentEvents.length > 0 && (
            <div>
              <div className="text-xs uppercase tracking-wider ds-text-secondary mb-2">
                {language === "en" ? "Recent Events" : "الأحداث الأخيرة"}
              </div>
              <div className="space-y-1 text-xs">
                {entity.recentEvents.map((event, idx) => (
                  <motion.div
                    key={idx}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: idx * 0.05 }}
                    className="p-2 rounded ds-bg-panel/50 border-l-2 ds-border-accent"
                  >
                    {event}
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
