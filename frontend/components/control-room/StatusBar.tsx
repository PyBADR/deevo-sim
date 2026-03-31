'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  AlertCircle,
  Zap,
  Database,
  Clock,
  TrendingUp,
  Radio,
} from 'lucide-react';

interface SystemHealth {
  status: 'healthy' | 'warning' | 'critical';
  uptime: number;
  latency: number;
  activeConnections: number;
}

interface StatusBarProps {
  systemHealth?: SystemHealth;
  gccRiskLevel?: number;
  activeScenarioName?: string;
  dataSourcesCount?: number;
  lastRefreshTime?: Date;
  language: 'en' | 'ar';
}

export const StatusBar: React.FC<StatusBarProps> = ({
  systemHealth = {
    status: 'healthy',
    uptime: 99.8,
    latency: 45,
    activeConnections: 127,
  },
  gccRiskLevel = 45,
  activeScenarioName = undefined,
  dataSourcesCount = 8,
  lastRefreshTime = new Date(),
  language,
}) => {
  const [displayedRiskLevel, setDisplayedRiskLevel] = useState(gccRiskLevel);
  const isRTL = language === 'ar';

  // Animate risk level changes
  useEffect(() => {
    const interval = setInterval(() => {
      setDisplayedRiskLevel((prev) => {
        const diff = gccRiskLevel - prev;
        if (Math.abs(diff) < 1) return gccRiskLevel;
        return prev + diff * 0.1;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [gccRiskLevel]);

  const healthColors = {
    healthy: 'text-green-400 bg-green-400/20',
    warning: 'text-yellow-400 bg-yellow-400/20',
    critical: 'text-red-500 bg-red-500/20',
  };

  const getRiskColor = (risk: number) => {
    if (risk < 30) return 'text-green-400';
    if (risk < 60) return 'text-yellow-400';
    if (risk < 80) return 'text-orange-400';
    return 'text-red-500';
  };

  const getRiskBgColor = (risk: number) => {
    if (risk < 30) return 'bg-green-400/20';
    if (risk < 60) return 'bg-yellow-400/20';
    if (risk < 80) return 'bg-orange-400/20';
    return 'bg-red-500/20';
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);

    if (diffSecs < 60) return language === 'ar' ? 'الآن' : 'Now';
    if (diffSecs < 3600)
      return `${Math.floor(diffSecs / 60)}${language === 'ar' ? 'د' : 'm'} ago`;
    if (diffSecs < 86400)
      return `${Math.floor(diffSecs / 3600)}${language === 'ar' ? 'س' : 'h'} ago`;
    return `${Math.floor(diffSecs / 86400)}${language === 'ar' ? 'ي' : 'd'} ago`;
  };

  return (
    <motion.div
      initial={{ y: -80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', damping: 20, stiffness: 300 }}
      className={`fixed top-0 left-0 right-0 h-20 bg-gradient-to-r from-ds-background via-ds-background to-ds-accent/5 border-b border-ds-accent/20 z-30 ${
        isRTL ? 'rtl' : 'ltr'
      }`}
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      <div className="h-full px-6 py-4 flex items-center justify-between gap-8">
        {/* Left Section: System Health */}
        <div className="flex items-center gap-6 min-w-0 flex-1">
          {/* Health Status */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className={`px-3 py-2 rounded-lg flex items-center gap-2 whitespace-nowrap ${
              healthColors[systemHealth.status]
            }`}
          >
            <motion.div animate={{ scale: [1, 1.1, 1] }} transition={{ duration: 2, repeat: Infinity }}>
              <Activity size={16} />
            </motion.div>
            <span className="text-sm font-semibold">
              {language === 'ar'
                ? systemHealth.status === 'healthy'
                  ? 'سليم'
                  : systemHealth.status === 'warning'
                    ? 'تحذير'
                    : 'حرج'
                : systemHealth.status.charAt(0).toUpperCase() +
                  systemHealth.status.slice(1)}
            </span>
          </motion.div>

          {/* Latency */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="px-3 py-2 rounded-lg bg-ds-accent/10 border border-ds-accent/20 flex items-center gap-2 text-xs whitespace-nowrap"
          >
            <Radio size={14} className="text-ds-accent" />
            <span className="text-gray-300">
              {language === 'ar' ? 'الكمون:' : 'Latency:'}{' '}
              <span className="text-ds-accent font-semibold">{systemHealth.latency}ms</span>
            </span>
          </motion.div>

          {/* Active Connections */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="px-3 py-2 rounded-lg bg-ds-accent/10 border border-ds-accent/20 flex items-center gap-2 text-xs whitespace-nowrap"
          >
            <Database size={14} className="text-cyan-400" />
            <span className="text-gray-300">
              {language === 'ar' ? 'الاتصالات:' : 'Connections:'}{' '}
              <span className="text-cyan-400 font-semibold">
                {systemHealth.activeConnections}
              </span>
            </span>
          </motion.div>

          {/* Data Sources */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="px-3 py-2 rounded-lg bg-ds-accent/10 border border-ds-accent/20 flex items-center gap-2 text-xs whitespace-nowrap"
          >
            <Database size={14} className="text-purple-400" />
            <span className="text-gray-300">
              {language === 'ar' ? 'المصادر:' : 'Sources:'}{' '}
              <span className="text-purple-400 font-semibold">{dataSourcesCount}</span>
            </span>
          </motion.div>
        </div>

        {/* Center Section: GCC Risk Level & Active Scenario */}
        <div className="flex items-center gap-4 flex-1 justify-center">
          {/* GCC Risk Level */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className={`px-4 py-2 rounded-lg flex items-center gap-3 ${getRiskBgColor(
              displayedRiskLevel
            )}`}
          >
            <Zap size={16} className={getRiskColor(displayedRiskLevel)} />
            <div className="flex flex-col">
              <span className="text-xs text-gray-400">
                {language === 'ar' ? 'مخاطر GCC' : 'GCC Risk'}
              </span>
              <span className={`text-lg font-bold ${getRiskColor(displayedRiskLevel)}`}>
                {Math.round(displayedRiskLevel)}%
              </span>
            </div>

            {/* Risk Indicator */}
            <div className="w-24 h-1.5 bg-ds-background/50 rounded-full overflow-hidden">
              <motion.div
                animate={{ width: `${displayedRiskLevel}%` }}
                transition={{ type: 'spring', damping: 20, stiffness: 300 }}
                className={`h-full rounded-full ${getRiskColor(displayedRiskLevel).replace(
                  'text',
                  'bg'
                )}`}
              />
            </div>
          </motion.div>

          {/* Active Scenario */}
          {activeScenarioName && (
            <motion.div
              whileHover={{ scale: 1.05 }}
              className="px-4 py-2 rounded-lg bg-ds-accent/10 border border-ds-accent/20 flex items-center gap-2 whitespace-nowrap"
            >
              <TrendingUp size={14} className="text-ds-accent" />
              <div className="flex flex-col">
                <span className="text-xs text-gray-400">
                  {language === 'ar' ? 'السيناريو النشط' : 'Active Scenario'}
                </span>
                <span className="text-sm font-semibold text-ds-accent">
                  {activeScenarioName}
                </span>
              </div>
            </motion.div>
          )}
        </div>

        {/* Right Section: Last Refresh & Uptime */}
        <div className="flex items-center gap-4 min-w-0 flex-1 justify-end">
          {/* Uptime */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="px-3 py-2 rounded-lg bg-ds-accent/10 border border-ds-accent/20 flex items-center gap-2 text-xs whitespace-nowrap"
          >
            <Activity size={14} className="text-green-400" />
            <span className="text-gray-300">
              {language === 'ar' ? 'التشغيل:' : 'Uptime:'}{' '}
              <span className="text-green-400 font-semibold">
                {systemHealth.uptime.toFixed(1)}%
              </span>
            </span>
          </motion.div>

          {/* Last Refresh */}
          <motion.div
            whileHover={{ scale: 1.05 }}
            className="px-3 py-2 rounded-lg bg-ds-accent/10 border border-ds-accent/20 flex items-center gap-2 text-xs whitespace-nowrap"
          >
            <Clock size={14} className="text-blue-400" />
            <span className="text-gray-300">
              {language === 'ar' ? 'آخر تحديث:' : 'Last Update:'}{' '}
              <span className="text-blue-400 font-semibold">
                {formatTime(lastRefreshTime)}
              </span>
            </span>
          </motion.div>

          {/* Status Indicator Pulse */}
          <motion.div
            animate={{ opacity: [1, 0.5, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-2 h-2 rounded-full bg-ds-accent"
          />
        </div>
      </div>
    </motion.div>
  );
};
