'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronRight,
  Eye,
  EyeOff,
  Zap,
  MapPin,
  Plane,
  Ship,
  RadioWaves,
  AlertTriangle,
  Wind,
  Grid3x3,
} from 'lucide-react';

interface LayerControlsProps {
  layerVisibility: {
    events: boolean;
    airports: boolean;
    ports: boolean;
    corridors: boolean;
    flights: boolean;
    vessels: boolean;
    heatmap: boolean;
    riskZones: boolean;
    flowLines: boolean;
  };
  onLayerToggle: (layer: keyof typeof LayerControlsProps.prototype.layerVisibility) => void;
  isCollapsed?: boolean;
  onCollapsedChange?: (collapsed: boolean) => void;
  language: 'en' | 'ar';
}

interface LayerItem {
  key: keyof typeof LayerControlsProps.prototype.layerVisibility;
  label: { en: string; ar: string };
  icon: React.ReactNode;
  color: string;
  category: 'entities' | 'overlays';
}

export const LayerControls: React.FC<LayerControlsProps> = ({
  layerVisibility,
  onLayerToggle,
  isCollapsed = false,
  onCollapsedChange,
  language,
}) => {
  const isRTL = language === 'ar';

  const layers: LayerItem[] = [
    {
      key: 'events',
      label: { en: 'Events', ar: 'الأحداث' },
      icon: <AlertTriangle size={16} />,
      color: 'text-yellow-400',
      category: 'entities',
    },
    {
      key: 'airports',
      label: { en: 'Airports', ar: 'المطارات' },
      icon: <Plane size={16} />,
      color: 'text-blue-400',
      category: 'entities',
    },
    {
      key: 'ports',
      label: { en: 'Ports', ar: 'الموانئ' },
      icon: <Ship size={16} />,
      color: 'text-cyan-400',
      category: 'entities',
    },
    {
      key: 'corridors',
      label: { en: 'Corridors', ar: 'الممرات' },
      icon: <MapPin size={16} />,
      color: 'text-green-400',
      category: 'entities',
    },
    {
      key: 'flights',
      label: { en: 'Flights', ar: 'الرحلات' },
      icon: <RadioWaves size={16} />,
      color: 'text-orange-400',
      category: 'overlays',
    },
    {
      key: 'vessels',
      label: { en: 'Vessels', ar: 'السفن' },
      icon: <Ship size={16} />,
      color: 'text-purple-400',
      category: 'overlays',
    },
    {
      key: 'heatmap',
      label: { en: 'Heatmap', ar: 'خريطة الحرارة' },
      icon: <Zap size={16} />,
      color: 'text-red-400',
      category: 'overlays',
    },
    {
      key: 'riskZones',
      label: { en: 'Risk Zones', ar: 'مناطق الخطر' },
      icon: <AlertTriangle size={16} />,
      color: 'text-red-500',
      category: 'overlays',
    },
    {
      key: 'flowLines',
      label: { en: 'Flow Lines', ar: 'خطوط التدفق' },
      icon: <Wind size={16} />,
      color: 'text-ds-accent',
      category: 'overlays',
    },
  ];

  const entityLayers = layers.filter((l) => l.category === 'entities');
  const overlayLayers = layers.filter((l) => l.category === 'overlays');

  return (
    <motion.div
      initial={{ x: isRTL ? 400 : -400, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: 'spring', damping: 20, stiffness: 300 }}
      className={`fixed top-24 bottom-24 w-80 bg-ds-panel border border-ds-accent/20 rounded-lg shadow-2xl flex flex-col overflow-hidden ${
        isRTL ? 'right-8' : 'left-8'
      }`}
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-ds-accent/20 flex items-center justify-between bg-gradient-to-r from-ds-accent/10 to-transparent">
        <div className="flex items-center gap-2">
          <Grid3x3 size={18} className="text-ds-accent" />
          <h2 className="text-lg font-bold text-ds-accent">
            {language === 'ar' ? 'الطبقات' : 'Layers'}
          </h2>
        </div>
        <button
          onClick={() => onCollapsedChange?.(!isCollapsed)}
          className="p-2 hover:bg-ds-accent/20 rounded-lg transition-colors"
        >
          <motion.div animate={{ rotate: isCollapsed ? 180 : 0 }}>
            <ChevronRight size={18} className="text-ds-accent" />
          </motion.div>
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {/* Entity Layers Section */}
        <LayerSection
          title={language === 'ar' ? 'الكيانات' : 'Entities'}
          layers={entityLayers}
          layerVisibility={layerVisibility}
          onLayerToggle={onLayerToggle}
          isRTL={isRTL}
        />

        {/* Visualization Overlays Section */}
        <LayerSection
          title={language === 'ar' ? 'التصورات البصرية' : 'Visualizations'}
          layers={overlayLayers}
          layerVisibility={layerVisibility}
          onLayerToggle={onLayerToggle}
          isRTL={isRTL}
        />

        {/* Legend */}
        <div className="pt-4 border-t border-ds-accent/15">
          <h3 className="text-xs font-semibold text-gray-400 mb-3">
            {language === 'ar' ? 'الرموز' : 'Legend'}
          </h3>
          <div className="space-y-2 text-xs text-gray-400">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-400" />
              <span>{language === 'ar' ? 'منخفض الخطر' : 'Low Risk'}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-yellow-400" />
              <span>{language === 'ar' ? 'متوسط الخطر' : 'Medium Risk'}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-orange-400" />
              <span>{language === 'ar' ? 'مخاطر عالية' : 'High Risk'}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500" />
              <span>{language === 'ar' ? 'حرج' : 'Critical'}</span>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

interface LayerSectionProps {
  title: string;
  layers: LayerItem[];
  layerVisibility: LayerControlsProps['layerVisibility'];
  onLayerToggle: (layer: keyof typeof LayerControlsProps.prototype.layerVisibility) => void;
  isRTL: boolean;
}

const LayerSection: React.FC<LayerSectionProps> = ({
  title,
  layers,
  layerVisibility,
  onLayerToggle,
  isRTL,
}) => (
  <div>
    <h3 className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">
      {title}
    </h3>
    <div className="space-y-2">
      {layers.map((layer) => {
        const isVisible = layerVisibility[layer.key];
        return (
          <motion.button
            key={layer.key}
            onClick={() => onLayerToggle(layer.key)}
            whileHover={{ x: isRTL ? -4 : 4 }}
            whileTap={{ scale: 0.98 }}
            className="w-full px-4 py-3 rounded-lg bg-ds-background/50 border border-ds-accent/15 hover:border-ds-accent/40 hover:bg-ds-accent/5 transition-all flex items-center justify-between group"
          >
            <div className="flex items-center gap-3">
              <motion.div
                animate={{ scale: isVisible ? 1 : 0.8, opacity: isVisible ? 1 : 0.5 }}
                className={isVisible ? layer.color : 'text-gray-600'}
              >
                {layer.icon}
              </motion.div>
              <span
                className={`text-sm font-medium ${
                  isVisible ? 'text-white' : 'text-gray-500'
                }`}
              >
                {layer.label[language === 'ar' ? 'ar' : 'en']}
              </span>
            </div>
            <motion.div
              animate={{ scale: isVisible ? 1 : 0.9, rotate: isVisible ? 0 : -90 }}
              className={isVisible ? 'text-ds-accent' : 'text-gray-600'}
            >
              {isVisible ? <Eye size={18} /> : <EyeOff size={18} />}
            </motion.div>
          </motion.button>
        );
      })}
    </div>
  </div>
);
