'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, SkipBack, SkipForward, Clock } from 'lucide-react';

interface TimelineEvent {
  id: string;
  timestamp: number;
  label: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
}

interface TimelineBarProps {
  events: TimelineEvent[];
  onEventSelect: (event: TimelineEvent) => void;
  language: 'en' | 'ar';
  isOpen?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export const TimelineBar: React.FC<TimelineBarProps> = ({
  events,
  onEventSelect,
  language,
  isOpen = true,
  onOpenChange,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [progress, setProgress] = useState(0);
  const playbackIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const timelineRef = useRef<HTMLDivElement>(null);
  const isRTL = language === 'ar';

  const sortedEvents = React.useMemo(
    () => [...events].sort((a, b) => a.timestamp - b.timestamp),
    [events]
  );

  // Auto-playback simulation
  useEffect(() => {
    if (!isPlaying || sortedEvents.length === 0) {
      if (playbackIntervalRef.current) {
        clearInterval(playbackIntervalRef.current);
        playbackIntervalRef.current = null;
      }
      return;
    }

    playbackIntervalRef.current = setInterval(() => {
      setCurrentIndex((prev) => {
        if (prev >= sortedEvents.length - 1) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 2000);

    return () => {
      if (playbackIntervalRef.current) {
        clearInterval(playbackIntervalRef.current);
      }
    };
  }, [isPlaying, sortedEvents.length]);

  // Update progress based on current index
  useEffect(() => {
    if (sortedEvents.length > 0) {
      setProgress((currentIndex / (sortedEvents.length - 1)) * 100);
      onEventSelect(sortedEvents[currentIndex]);
    }
  }, [currentIndex, sortedEvents, onEventSelect]);

  const handlePlayPause = useCallback(() => {
    setIsPlaying((prev) => !prev);
  }, []);

  const handlePrevious = useCallback(() => {
    setCurrentIndex((prev) => Math.max(0, prev - 1));
    setIsPlaying(false);
  }, []);

  const handleNext = useCallback(() => {
    setCurrentIndex((prev) => Math.min(sortedEvents.length - 1, prev + 1));
    setIsPlaying(false);
  }, [sortedEvents.length]);

  const handleTimelineClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!timelineRef.current) return;

    const rect = timelineRef.current.getBoundingClientRect();
    const clickX = isRTL ? rect.right - e.clientX : e.clientX - rect.left;
    const percentage = (clickX / rect.width) * 100;
    const newIndex = Math.round((percentage / 100) * (sortedEvents.length - 1));

    setCurrentIndex(Math.max(0, Math.min(newIndex, sortedEvents.length - 1)));
    setIsPlaying(false);
  }, [sortedEvents.length, isRTL]);

  if (!isOpen || sortedEvents.length === 0) {
    return null;
  }

  const currentEvent = sortedEvents[currentIndex];

  const severityColors = {
    critical: 'text-red-500 bg-red-500/20',
    high: 'text-orange-400 bg-orange-400/20',
    medium: 'text-yellow-400 bg-yellow-400/20',
    low: 'text-green-400 bg-green-400/20',
  };

  const severityBadgeColors = {
    critical: 'bg-red-500',
    high: 'bg-orange-400',
    medium: 'bg-yellow-400',
    low: 'bg-green-400',
  };

  return (
    <motion.div
      initial={{ y: 100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 100, opacity: 0 }}
      transition={{ type: 'spring', damping: 20, stiffness: 300 }}
      className={`fixed bottom-8 left-1/2 transform -translate-x-1/2 w-11/12 max-w-6xl bg-ds-panel border border-ds-accent/20 rounded-lg shadow-2xl overflow-hidden ${
        isRTL ? 'rtl' : 'ltr'
      }`}
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      <div className="bg-gradient-to-r from-ds-accent/10 to-transparent px-6 py-4">
        <div className="flex items-center gap-3 mb-4">
          <Clock size={18} className="text-ds-accent" />
          <h3 className="text-sm font-semibold text-ds-accent">
            {language === 'ar' ? 'خط الزمن' : 'Timeline'}
          </h3>
          <span className="text-xs text-gray-400">
            {currentIndex + 1} / {sortedEvents.length}
          </span>
        </div>

        {/* Event Info */}
        {currentEvent && (
          <div className="mb-4 p-3 bg-ds-background/50 rounded-lg border border-ds-accent/10">
            <div className="flex items-start justify-between mb-2">
              <div>
                <h4 className="font-semibold text-white">{currentEvent.label}</h4>
                <p className="text-xs text-gray-400 mt-1">{currentEvent.description}</p>
              </div>
              <span
                className={`px-2 py-1 rounded text-xs font-semibold ${
                  severityColors[currentEvent.severity]
                }`}
              >
                {language === 'ar'
                  ? currentEvent.severity === 'critical'
                    ? 'حرج'
                    : currentEvent.severity === 'high'
                      ? 'عالي'
                      : currentEvent.severity === 'medium'
                        ? 'متوسط'
                        : 'منخفض'
                  : currentEvent.severity.charAt(0).toUpperCase() +
                    currentEvent.severity.slice(1)}
              </span>
            </div>
            <p className="text-xs text-gray-500">
              T+{(currentEvent.timestamp / 60).toFixed(1)}m
            </p>
          </div>
        )}

        {/* Timeline Visual */}
        <div className="mb-4 space-y-3">
          {/* Progress Bar */}
          <div
            ref={timelineRef}
            onClick={handleTimelineClick}
            className="relative h-8 bg-ds-background/30 rounded-lg cursor-pointer group border border-ds-accent/10 overflow-hidden"
          >
            {/* Background progress */}
            <motion.div
              animate={{ width: `${progress}%` }}
              transition={{ type: 'spring', damping: 20, stiffness: 300 }}
              className="absolute inset-y-0 left-0 bg-gradient-to-r from-ds-accent/30 to-ds-accent/10"
            />

            {/* Event markers */}
            {sortedEvents.map((event, index) => {
              const eventProgress = (index / (sortedEvents.length - 1)) * 100;
              return (
                <motion.button
                  key={event.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    setCurrentIndex(index);
                    setIsPlaying(false);
                  }}
                  whileHover={{ scale: 1.5 }}
                  whileTap={{ scale: 1.3 }}
                  className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full transition-all ${
                    index === currentIndex
                      ? 'ring-2 ring-ds-accent scale-125'
                      : 'hover:scale-110'
                  }`}
                  style={{
                    [isRTL ? 'right' : 'left']: `${eventProgress}%`,
                    transform: 'translateY(-50%)',
                  }}
                >
                  <div
                    className={`w-full h-full rounded-full ${severityBadgeColors[event.severity]}`}
                  />

                  {/* Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-ds-background border border-ds-accent/30 rounded text-xs text-gray-300 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                    {event.label}
                  </div>
                </motion.button>
              );
            })}

            {/* Current indicator */}
            <motion.div
              animate={{ [isRTL ? 'right' : 'left']: `${progress}%` }}
              transition={{ type: 'spring', damping: 20, stiffness: 300 }}
              className="absolute top-0 bottom-0 w-1 bg-ds-accent shadow-lg shadow-ds-accent/50 pointer-events-none"
            />
          </div>

          {/* Playback Controls */}
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={handlePrevious}
              disabled={currentIndex === 0}
              className="p-2 rounded-lg hover:bg-ds-accent/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-gray-400 hover:text-ds-accent"
            >
              <SkipBack size={18} />
            </button>

            <button
              onClick={handlePlayPause}
              className="p-3 rounded-lg bg-ds-accent/20 hover:bg-ds-accent/30 transition-colors text-ds-accent"
            >
              {isPlaying ? <Pause size={20} /> : <Play size={20} />}
            </button>

            <button
              onClick={handleNext}
              disabled={currentIndex === sortedEvents.length - 1}
              className="p-2 rounded-lg hover:bg-ds-accent/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-gray-400 hover:text-ds-accent"
            >
              <SkipForward size={18} />
            </button>

            {/* Playback speed indicator */}
            <div className="flex-1 text-right text-xs text-gray-500">
              {isPlaying && '⚡ 2s per event'}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
