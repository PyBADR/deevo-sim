'use client';

import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, AlertTriangle, TrendingUp, Zap, Target } from 'lucide-react';

interface ExplanationPanelProps {
  isOpen: boolean;
  onClose: () => void;
  explanation?: string;
  scenarioName?: string;
  language: 'en' | 'ar';
}

export const ExplanationPanel: React.FC<ExplanationPanelProps> = ({
  isOpen,
  onClose,
  explanation,
  scenarioName,
  language,
}) => {
  const [expandedSections, setExpandedSections] = useState({
    whatHappened: true,
    whatImpacted: true,
    riskQuantified: true,
    recommendations: false,
  });

  const isRTL = language === 'ar';

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  // Parse explanation into sections (format: "## Section Title\nContent")
  const parsedExplanation = React.useMemo(() => {
    if (!explanation) {
      return {
        whatHappened: language === 'ar' ? 'لم يتم توفير شرح' : 'No explanation provided',
        whatImpacted: language === 'ar' ? 'لا توجد بيانات تأثير' : 'No impact data available',
        riskQuantified: language === 'ar' ? 'لا توجد بيانات المخاطر' : 'No risk data available',
        recommendations: language === 'ar' ? 'لا توجد توصيات متاحة' : 'No recommendations available',
      };
    }

    const sections = {
      whatHappened: '',
      whatImpacted: '',
      riskQuantified: '',
      recommendations: '',
    };

    const lines = explanation.split('\n');
    let currentSection = '';

    for (const line of lines) {
      if (line.includes('What Happened') || line.includes('ما الذي حدث')) {
        currentSection = 'whatHappened';
      } else if (line.includes('What Impacted') || line.includes('ما الذي تأثر')) {
        currentSection = 'whatImpacted';
      } else if (line.includes('Risk Quantified') || line.includes('تحديد المخاطر الكمي')) {
        currentSection = 'riskQuantified';
      } else if (line.includes('Recommendations') || line.includes('التوصيات')) {
        currentSection = 'recommendations';
      } else if (currentSection && line.trim()) {
        sections[currentSection as keyof typeof sections] += line + '\n';
      }
    }

    return Object.fromEntries(
      Object.entries(sections).map(([key, value]) => [
        key,
        value.trim() || (language === 'ar' ? 'لا توجد بيانات' : 'No data'),
      ])
    );
  }, [explanation, language]);

  const translations = {
    whatHappened: language === 'ar' ? 'ما الذي حدث' : 'What Happened',
    whatImpacted: language === 'ar' ? 'ما الذي تأثر' : 'What Impacted',
    riskQuantified: language === 'ar' ? 'تحديد المخاطر الكمي' : 'Risk Quantified',
    recommendations: language === 'ar' ? 'التوصيات' : 'Recommendations',
    scenario: language === 'ar' ? 'السيناريو' : 'Scenario',
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
          />
          <motion.div
            initial={{ x: isRTL ? -400 : 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: isRTL ? -400 : 400, opacity: 0 }}
            transition={{ type: 'spring', damping: 20, stiffness: 300 }}
            className={`fixed top-24 bottom-24 w-96 z-50 bg-ds-panel border border-ds-accent/20 rounded-lg shadow-2xl flex flex-col overflow-hidden ${
              isRTL ? 'left-8' : 'right-8'
            }`}
            dir={isRTL ? 'rtl' : 'ltr'}
          >
            {/* Header */}
            <div className="px-6 py-4 border-b border-ds-accent/20 flex items-center justify-between bg-gradient-to-r from-ds-accent/10 to-transparent">
              <div>
                <h2 className="text-lg font-bold text-ds-accent">
                  {language === 'ar' ? 'تحليل السيناريو' : 'Scenario Analysis'}
                </h2>
                {scenarioName && (
                  <p className="text-sm text-gray-400 mt-1">{scenarioName}</p>
                )}
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-ds-accent/20 rounded-lg transition-colors"
              >
                <ChevronDown
                  size={20}
                  className={`text-ds-accent transform ${isRTL ? 'rotate-90' : '-rotate-90'}`}
                />
              </button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
              {/* What Happened Section */}
              <ExplanationSection
                title={translations.whatHappened}
                content={parsedExplanation.whatHappened}
                isOpen={expandedSections.whatHappened}
                onToggle={() => toggleSection('whatHappened')}
                icon={<AlertTriangle size={18} />}
                isRTL={isRTL}
              />

              {/* What Impacted Section */}
              <ExplanationSection
                title={translations.whatImpacted}
                content={parsedExplanation.whatImpacted}
                isOpen={expandedSections.whatImpacted}
                onToggle={() => toggleSection('whatImpacted')}
                icon={<TrendingUp size={18} />}
                isRTL={isRTL}
              />

              {/* Risk Quantified Section */}
              <ExplanationSection
                title={translations.riskQuantified}
                content={parsedExplanation.riskQuantified}
                isOpen={expandedSections.riskQuantified}
                onToggle={() => toggleSection('riskQuantified')}
                icon={<Zap size={18} />}
                isRTL={isRTL}
                accentColor="text-orange-400"
              />

              {/* Recommendations Section */}
              <ExplanationSection
                title={translations.recommendations}
                content={parsedExplanation.recommendations}
                isOpen={expandedSections.recommendations}
                onToggle={() => toggleSection('recommendations')}
                icon={<Target size={18} />}
                isRTL={isRTL}
                accentColor="text-cyan-400"
              />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

interface ExplanationSectionProps {
  title: string;
  content: string;
  isOpen: boolean;
  onToggle: () => void;
  icon: React.ReactNode;
  isRTL: boolean;
  accentColor?: string;
}

const ExplanationSection: React.FC<ExplanationSectionProps> = ({
  title,
  content,
  isOpen,
  onToggle,
  icon,
  isRTL,
  accentColor = 'text-ds-accent',
}) => (
  <div className="border border-ds-accent/15 rounded-lg overflow-hidden bg-ds-background/50">
    <button
      onClick={onToggle}
      className="w-full px-4 py-3 flex items-center justify-between hover:bg-ds-accent/10 transition-colors"
    >
      <div className="flex items-center gap-2">
        <span className={`${accentColor}`}>{icon}</span>
        <span className="font-semibold text-white">{title}</span>
      </div>
      <motion.div
        animate={{ rotate: isOpen ? 180 : 0 }}
        transition={{ duration: 0.2 }}
      >
        <ChevronDown size={16} className="text-ds-accent" />
      </motion.div>
    </button>

    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="overflow-hidden"
        >
          <div className="px-4 py-3 border-t border-ds-accent/15 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
            {content}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  </div>
);
