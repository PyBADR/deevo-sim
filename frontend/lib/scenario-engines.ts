// ============================================================================
// TYPES AND INTERFACES
// ============================================================================

export interface Narrative {
  en: string;
  ar: string;
}

export interface EngineMetric {
  value: number;
  confidence: number;
}

export interface EngineSectorImpact {
  gdpLoss: EngineMetric;
  confidence: EngineMetric;
  narrative: Narrative;
}

export interface EngineNodeImpact {
  nodeId: string;
  layers: {
    geography?: EngineMetric;
    economy?: EngineMetric;
    finance?: EngineMetric;
    infrastructure?: EngineMetric;
    society?: EngineMetric;
  };
}

export interface ExplanationStep {
  en: string;
  ar: string;
}

export interface ScenarioEngineOutput {
  scenarioId: string;
  scenarioName: string;
  timestamp: number;
  timeframe: {
    immediate: string;
    shortTerm: string;
    mediumTerm: string;
  };
  metrics: {
    globalGdpLoss: EngineMetric;
    regionalGdpLoss: EngineMetric;
    confidence: EngineMetric;
  };
  sectorImpacts: Record<string, EngineSectorImpact>;
  nodeImpacts: EngineNodeImpact[];
  explanation: ExplanationStep[];
}

export interface ScenarioEngineInput {
  scenarioId: string;
  parameters?: Record<string, number>;
}

export interface ScenarioEngine {
  id: string;
  name: string;
  compute: (input: ScenarioEngineInput) => ScenarioEngineOutput;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function I(base: number, factor: number = 1): EngineMetric {
  return {
    value: base * factor,
    confidence: Math.min(95, Math.max(30, 75 - Math.abs(base - 50) * 0.5))
  };
}

function clamp(value: number, min: number = 0, max: number = 100): number {
  return Math.max(min, Math.min(max, value));
}

function pct(value: number): number {
  return clamp(value, 0, 100);
}

// ============================================================================
// SCENARIO ENGINE IMPLEMENTATIONS
// ============================================================================

const hormuzClosure: ScenarioEngine = {
  id: 'hormuz-closure',
  name: 'Hormuz Strait Closure',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'Hormuz Strait Closure',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Hours to days',
      shortTerm: '1-3 months',
      mediumTerm: '3-12 months'
    },
    metrics: {
      globalGdpLoss: I(4.5),
      regionalGdpLoss: I(28),
      confidence: I(82)
    },
    sectorImpacts: {
      oil_gas: {
        gdpLoss: I(45),
        confidence: I(88),
        narrative: {
          en: 'Global oil supply disrupted; prices spike 200-300%',
          ar: 'إمدادات النفط العالمية مختلة; تقفز الأسعار 200-300%'
        }
      },
      shipping: {
        gdpLoss: I(85),
        confidence: I(90),
        narrative: {
          en: 'International maritime trade halted; rerouting adds 20-30 days',
          ar: 'التجارة البحرية الدولية موقوفة; إعادة التوجيه تضيف 20-30 يوم'
        }
      },
      chemicals: {
        gdpLoss: I(52),
        confidence: I(85),
        narrative: {
          en: 'Petrochemical supply chains fractured',
          ar: 'سلاسل التوريد البتروكيماوية مقسمة'
        }
      },
      aviation: {
        gdpLoss: I(18),
        confidence: I(75),
        narrative: {
          en: 'Fuel costs rise; routes diverted around Persian Gulf',
          ar: 'ترتفع تكاليف الوقود; تحويل المسارات حول الخليج الفارسي'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          economy: I(42),
          finance: I(55),
          infrastructure: I(38)
        }
      },
      {
        nodeId: 'iran',
        layers: {
          economy: I(65),
          finance: I(72)
        }
      },
      {
        nodeId: 'asia_pacific',
        layers: {
          economy: I(22),
          infrastructure: I(18)
        }
      }
    ],
    explanation: [
      {
        en: 'The Hormuz Strait is the world\'s most critical oil chokepoint',
        ar: 'مضيق هرمز هو أهم نقطة اختناق نفط في العالم'
      },
      {
        en: 'Closure would immediately disrupt 30% of globally traded oil',
        ar: 'الإغلاق سيعطل فوراً 30% من النفط المتداول عالمياً'
      },
      {
        en: 'Energy prices would spike, triggering global inflation',
        ar: 'ستقفز أسعار الطاقة، مما يؤدي إلى التضخم العالمي'
      }
    ]
  })
};

const usIranEscalation: ScenarioEngine = {
  id: 'us-iran-escalation',
  name: 'US-Iran Military Escalation',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'US-Iran Military Escalation',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Days',
      shortTerm: '1-6 months',
      mediumTerm: '6-24 months'
    },
    metrics: {
      globalGdpLoss: I(3.2),
      regionalGdpLoss: I(35),
      confidence: I(68)
    },
    sectorImpacts: {
      defense: {
        gdpLoss: I(8),
        confidence: I(90),
        narrative: {
          en: 'Defense spending surges; military buildup accelerates',
          ar: 'نفقات الدفاع تقفز؛ التعزيز العسكري يتسارع'
        }
      },
      energy: {
        gdpLoss: I(35),
        confidence: I(80),
        narrative: {
          en: 'Iranian oil exports face restrictions; price volatility increases',
          ar: 'الصادرات النفطية الإيرانية تواجه قيوداً; تقلبات الأسعار تزداد'
        }
      },
      tourism: {
        gdpLoss: I(42),
        confidence: I(85),
        narrative: {
          en: 'Travel warnings issued; tourism collapses in Middle East',
          ar: 'إصدار تنبيهات السفر؛ انهيار السياحة في الشرق الأوسط'
        }
      },
      insurance: {
        gdpLoss: I(28),
        confidence: I(82),
        narrative: {
          en: 'War risk premiums surge for regional shipping',
          ar: 'علاوات مخاطر الحرب تقفز للشحن الإقليمي'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          economy: I(38),
          finance: I(45),
          infrastructure: I(22),
          society: I(35)
        }
      },
      {
        nodeId: 'iran',
        layers: {
          economy: I(58),
          finance: I(68),
          society: I(72)
        }
      },
      {
        nodeId: 'us',
        layers: {
          economy: I(8),
          finance: I(12)
        }
      }
    ],
    explanation: [
      {
        en: 'Military escalation would trigger immediate risk repricing',
        ar: 'سيؤدي التصعيد العسكري إلى إعادة تسعير الأخطار الفوري'
      },
      {
        en: 'Regional stability would deteriorate; investment flows reverse',
        ar: 'الاستقرار الإقليمي سيتدهور؛ تنعكس تدفقات الاستثمار'
      }
    ]
  })
};

const gccAirspaceRestriction: ScenarioEngine = {
  id: 'gcc-airspace-restriction',
  name: 'GCC Airspace Restrictions',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'GCC Airspace Restrictions',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Hours',
      shortTerm: '1-3 weeks',
      mediumTerm: '1-3 months'
    },
    metrics: {
      globalGdpLoss: I(1.8),
      regionalGdpLoss: I(18),
      confidence: I(75)
    },
    sectorImpacts: {
      aviation: {
        gdpLoss: I(65),
        confidence: I(92),
        narrative: {
          en: 'Flight routes rerouted; fuel costs and journey times increase',
          ar: 'إعادة توجيه مسارات الرحلات؛ تزداد تكاليف الوقود وأوقات الرحلة'
        }
      },
      tourism: {
        gdpLoss: I(48),
        confidence: I(80),
        narrative: {
          en: 'Hub connectivity disrupted; tourism affected',
          ar: 'اتصال المركز معطل؛ السياحة متأثرة'
        }
      },
      shipping: {
        gdpLoss: I(12),
        confidence: I(70),
        narrative: {
          en: 'Minimal impact on maritime trade but air cargo affected',
          ar: 'تأثير ضئيل على التجارة البحرية لكن الشحن الجوي متأثر'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          economy: I(22),
          infrastructure: I(32),
          society: I(12)
        }
      },
      {
        nodeId: 'asia_pacific',
        layers: {
          economy: I(8)
        }
      }
    ],
    explanation: [
      {
        en: 'GCC airspace is critical for global aviation routes',
        ar: 'أجواء دول مجلس التعاون الخليجي حرجة لمسارات الطيران العالمية'
      },
      {
        en: 'Restrictions would reroute 40% of Asia-Europe flights',
        ar: 'ستعيد القيود توجيه 40% من الرحلات آسيا-أوروبا'
      }
    ]
  })
};

const hajjDisruption: ScenarioEngine = {
  id: 'hajj-disruption',
  name: 'Hajj Disruption',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'Hajj Disruption',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Days to weeks',
      shortTerm: '1-3 months',
      mediumTerm: '1 year'
    },
    metrics: {
      globalGdpLoss: I(0.6),
      regionalGdpLoss: I(8),
      confidence: I(72)
    },
    sectorImpacts: {
      tourism: {
        gdpLoss: I(72),
        confidence: I(88),
        narrative: {
          en: '2 million+ pilgrims unable to attend; hotel, transport sectors collapse',
          ar: 'أكثر من مليونين حاج غير قادر على الحضور؛ انهيار قطاعات الفنادق والنقل'
        }
      },
      retail: {
        gdpLoss: I(28),
        confidence: I(80),
        narrative: {
          en: 'Retail spending in KSA drops significantly',
          ar: 'ينخفض الإنفاق في التجزئة في المملكة العربية السعودية بشكل كبير'
        }
      },
      logistics: {
        gdpLoss: I(18),
        confidence: I(75),
        narrative: {
          en: 'Logistics and ground handling severely impacted',
          ar: 'الخدمات اللوجستية والمعالجة الأرضية متأثرة بشدة'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          economy: I(12),
          finance: I(8),
          society: I(35)
        }
      }
    ],
    explanation: [
      {
        en: 'Hajj is the world\'s largest annual religious gathering',
        ar: 'الحج هو أكبر تجمع ديني سنوي في العالم'
      },
      {
        en: 'Disruption would cost KSA billions in revenue',
        ar: 'سيكلف الاضطراب المملكة العربية السعودية مليارات الإيرادات'
      }
    ]
  })
};

const jebelAliDisruption: ScenarioEngine = {
  id: 'jebel-ali-disruption',
  name: 'Jebel Ali Port Disruption',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'Jebel Ali Port Disruption',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Days',
      shortTerm: '2-8 weeks',
      mediumTerm: '2-6 months'
    },
    metrics: {
      globalGdpLoss: I(2.1),
      regionalGdpLoss: I(15),
      confidence: I(80)
    },
    sectorImpacts: {
      shipping: {
        gdpLoss: I(78),
        confidence: I(90),
        narrative: {
          en: 'World\'s 10th largest container port offline; cargo backlogs severe',
          ar: 'ميناء الحاويات العاشر في العالم غير متصل بالإنترنت; تأخيرات الشحنات حادة'
        }
      },
      retail: {
        gdpLoss: I(32),
        confidence: I(82),
        narrative: {
          en: 'Consumer goods supply delayed; retail shortages emerge',
          ar: 'تأخر توريد السلع الاستهلاكية؛ ظهور النقص في البيع بالتجزئة'
        }
      },
      manufacturing: {
        gdpLoss: I(25),
        confidence: I(78),
        narrative: {
          en: 'Supply chain disruption impacts electronics, automotive',
          ar: 'اضطراب سلسلة التوريد يؤثر على الإلكترونيات والسيارات'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          economy: I(18),
          finance: I(22),
          infrastructure: I(65)
        }
      },
      {
        nodeId: 'asia_pacific',
        layers: {
          economy: I(12),
          infrastructure: I(15)
        }
      }
    ],
    explanation: [
      {
        en: 'Jebel Ali is a critical Middle East logistics hub',
        ar: 'جبل علي هو مركز لوجستي حرج في الشرق الأوسط'
      },
      {
        en: 'Disruption would affect global supply chains for weeks',
        ar: 'سيؤثر الاضطراب على سلاسل التوريد العالمية لأسابيع'
      }
    ]
  })
};

const foodSecurityShock: ScenarioEngine = {
  id: 'food-security-shock',
  name: 'Food Security Shock',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'Food Security Shock',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Weeks',
      shortTerm: '1-3 months',
      mediumTerm: '6-24 months'
    },
    metrics: {
      globalGdpLoss: I(1.9),
      regionalGdpLoss: I(22),
      confidence: I(78)
    },
    sectorImpacts: {
      agriculture: {
        gdpLoss: I(58),
        confidence: I(85),
        narrative: {
          en: 'Food prices spike 40-60%; supply chain disrupted',
          ar: 'أسعار المواد الغذائية تقفز 40-60%; سلسلة التوريد معطلة'
        }
      },
      retail_food: {
        gdpLoss: I(35),
        confidence: I(82),
        narrative: {
          en: 'Grocery stores face shortages; consumer panic buying',
          ar: 'محلات البقالة تواجه نقصاً; الشراء الذعر من المستهلكين'
        }
      },
      hospitality: {
        gdpLoss: I(28),
        confidence: I(75),
        narrative: {
          en: 'Restaurants and hotels face input cost inflation',
          ar: 'تواجه المطاعم والفنادق التضخم في تكاليف المدخلات'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          economy: I(22),
          society: I(45),
          finance: I(18)
        }
      },
      {
        nodeId: 'global',
        layers: {
          economy: I(12),
          society: I(28)
        }
      }
    ],
    explanation: [
      {
        en: 'Middle East imports 80% of food needs',
        ar: 'يستورد الشرق الأوسط 80% من احتياجاته الغذائية'
      },
      {
        en: 'Supply disruption would cause immediate food inflation',
        ar: 'سيؤدي اضطراب الإمدادات إلى التضخم الفوري للغذاء'
      }
    ]
  })
};

const gccLiquidityStress: ScenarioEngine = {
  id: 'gcc-liquidity-stress',
  name: 'GCC Liquidity Stress',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'GCC Liquidity Stress',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Hours to days',
      shortTerm: '1-4 weeks',
      mediumTerm: '1-6 months'
    },
    metrics: {
      globalGdpLoss: I(1.2),
      regionalGdpLoss: I(32),
      confidence: I(75)
    },
    sectorImpacts: {
      banking: {
        gdpLoss: I(68),
        confidence: I(88),
        narrative: {
          en: 'Credit markets seize; lending freezes; FX volatility spikes',
          ar: 'أسواق الائتمان تتوقف؛ تجميد الإقراض؛ تقلبات الصرف الأجنبي تقفز'
        }
      },
      real_estate: {
        gdpLoss: I(45),
        confidence: I(80),
        narrative: {
          en: 'Property values decline; construction projects halted',
          ar: 'تنخفض قيم الممتلكات؛ توقف المشاريع الإنشائية'
        }
      },
      capital_markets: {
        gdpLoss: I(52),
        confidence: I(85),
        narrative: {
          en: 'Stock markets decline; investor confidence collapses',
          ar: 'تراجع أسواق الأسهم؛ انهيار ثقة المستثمرين'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          finance: I(72),
          economy: I(42),
          infrastructure: I(28)
        }
      }
    ],
    explanation: [
      {
        en: 'GCC banking system is highly interconnected regionally',
        ar: 'نظام البنوك في دول مجلس التعاون الخليجي مترابط بشكل كبير إقليمياً'
      },
      {
        en: 'Liquidity stress would cascade through financial system',
        ar: 'سيؤدي الضغط على السيولة إلى التأثير على النظام المالي'
      }
    ]
  })
};

const fxGoldCryptoShock: ScenarioEngine = {
  id: 'fx-gold-crypto-shock',
  name: 'FX, Gold, Crypto Shock',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'FX, Gold, Crypto Shock',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Hours',
      shortTerm: '1-2 weeks',
      mediumTerm: '1-3 months'
    },
    metrics: {
      globalGdpLoss: I(0.8),
      regionalGdpLoss: I(12),
      confidence: I(70)
    },
    sectorImpacts: {
      forex: {
        gdpLoss: I(75),
        confidence: I(88),
        narrative: {
          en: 'Major currency pairs experience 10-15% swings',
          ar: 'تشهد أزواج العملات الرئيسية تذبذبات بنسبة 10-15%'
        }
      },
      commodities: {
        gdpLoss: I(42),
        confidence: I(82),
        narrative: {
          en: 'Gold spikes as safe haven; oil and metals volatile',
          ar: 'القفزات الذهبية كملاذ آمن؛ النفط والمعادن متقلبة'
        }
      },
      digital_assets: {
        gdpLoss: I(58),
        confidence: I(75),
        narrative: {
          en: 'Crypto crashes 30-50%; confidence in digital assets erodes',
          ar: 'انهيار العملات المشفرة 30-50%; تآكل الثقة في الأصول الرقمية'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          finance: I(58),
          economy: I(18)
        }
      },
      {
        nodeId: 'global',
        layers: {
          finance: I(32)
        }
      }
    ],
    explanation: [
      {
        en: 'Market volatility triggers flight to safety',
        ar: 'تقلبات السوق تؤدي إلى الهروب للأمان'
      },
      {
        en: 'Currency weakness impacts import costs for GCC nations',
        ar: 'ضعف العملة يؤثر على تكاليف الاستيراد لدول مجلس التعاون الخليجي'
      }
    ]
  })
};

const insuranceRepricing: ScenarioEngine = {
  id: 'insurance-repricing',
  name: 'Insurance Repricing Crisis',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'Insurance Repricing Crisis',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Days',
      shortTerm: '1-3 months',
      mediumTerm: '3-12 months'
    },
    metrics: {
      globalGdpLoss: I(0.5),
      regionalGdpLoss: I(18),
      confidence: I(72)
    },
    sectorImpacts: {
      insurance: {
        gdpLoss: I(65),
        confidence: I(85),
        narrative: {
          en: 'Insurance premiums surge 100-300% for high-risk sectors',
          ar: 'ترتفع أقساط التأمين 100-300% للقطاعات عالية المخاطر'
        }
      },
      shipping: {
        gdpLoss: I(48),
        confidence: I(82),
        narrative: {
          en: 'War risk premiums spike; maritime insurance becomes expensive',
          ar: 'تقفز علاوات مخاطر الحرب؛ تصبح تأمين البحار مكلفاً'
        }
      },
      energy: {
        gdpLoss: I(32),
        confidence: I(78),
        narrative: {
          en: 'Oil and gas facility insurance costs increase dramatically',
          ar: 'تزداد تكاليف تأمين منشآت النفط والغاز بشكل كبير'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          finance: I(48),
          economy: I(22),
          infrastructure: I(18)
        }
      }
    ],
    explanation: [
      {
        en: 'Insurance markets reprice risk in response to geopolitical events',
        ar: 'تعيد أسواق التأمين تسعير المخاطر استجابة للأحداث الجيوسياسية'
      },
      {
        en: 'Higher premiums increase business operating costs',
        ar: 'تزيد الأقساط الأعلى من تكاليف التشغيل للأعمال'
      }
    ]
  })
};

const gccGridFailure: ScenarioEngine = {
  id: 'gcc-grid-failure',
  name: 'GCC Power Grid Failure',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'GCC Power Grid Failure',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Seconds to hours',
      shortTerm: '24-72 hours',
      mediumTerm: '1-4 weeks'
    },
    metrics: {
      globalGdpLoss: I(1.4),
      regionalGdpLoss: I(28),
      confidence: I(78)
    },
    sectorImpacts: {
      energy: {
        gdpLoss: I(82),
        confidence: I(90),
        narrative: {
          en: 'Power outages cascade across GCC; generation capacity offline',
          ar: 'انقطاع التيار الكهربائي ينتشر في جميع دول مجلس التعاون؛ السعة المولدة معطلة'
        }
      },
      manufacturing: {
        gdpLoss: I(58),
        confidence: I(85),
        narrative: {
          en: 'Industrial production halts; supply chains disrupted',
          ar: 'الإنتاج الصناعي يتوقف؛ سلاسل التوريد معطلة'
        }
      },
      desalination: {
        gdpLoss: I(72),
        confidence: I(88),
        narrative: {
          en: 'Water desalination offline; water shortage emergency',
          ar: 'تحلية المياه معطلة؛ حالة طوارئ نقص المياه'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          infrastructure: I(88),
          economy: I(58),
          society: I(62)
        }
      }
    ],
    explanation: [
      {
        en: 'GCC grids are tightly integrated and interdependent',
        ar: 'شبكات دول مجلس التعاون الخليجي متكاملة ومترابطة بإحكام'
      },
      {
        en: 'Failure would cascade across region; recovery takes weeks',
        ar: 'سيؤدي الفشل إلى انتشار الأزمة في المنطقة؛ الاستعادة تستغرق أسابيع'
      }
    ]
  })
};

const electricityWaterDisruption: ScenarioEngine = {
  id: 'electricity-water-disruption',
  name: 'Electricity-Water Disruption',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'Electricity-Water Disruption',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Hours to days',
      shortTerm: '1-4 weeks',
      mediumTerm: '1-3 months'
    },
    metrics: {
      globalGdpLoss: I(0.9),
      regionalGdpLoss: I(24),
      confidence: I(76)
    },
    sectorImpacts: {
      utilities: {
        gdpLoss: I(78),
        confidence: I(88),
        narrative: {
          en: 'Water and power supplies disrupted; dual infrastructure failure',
          ar: 'اضطراب الماء والكهرباء؛ فشل البنية التحتية المزدوجة'
        }
      },
      agriculture: {
        gdpLoss: I(35),
        confidence: I(80),
        narrative: {
          en: 'Irrigation systems fail; crop watering suspended',
          ar: 'فشل أنظمة الري؛ توقف ري المحاصيل'
        }
      },
      health: {
        gdpLoss: I(42),
        confidence: I(82),
        narrative: {
          en: 'Hospital operations impaired; water shortage emergency',
          ar: 'تضعف عمليات المستشفيات؛ حالة طوارئ نقص المياه'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          infrastructure: I(78),
          society: I(58),
          economy: I(35)
        }
      }
    ],
    explanation: [
      {
        en: 'GCC depends on electricity-powered desalination for water',
        ar: 'تعتمد دول مجلس التعاون الخليجي على تحلية المياه التي تعمل بالكهرباء'
        
      },
      {
        en: 'Disruption cascades; water shortage within 24 hours',
        ar: 'الاضطراب ينتشر؛ نقص المياه خلال 24 ساعة'
      }
    ]
  })
};

const vision2030Stress: ScenarioEngine = {
  id: 'vision-2030-stress',
  name: 'Vision 2030 Program Stress',
  compute: (input: ScenarioEngineInput) => ({
    scenarioId: input.scenarioId,
    scenarioName: 'Vision 2030 Program Stress',
    timestamp: Date.now(),
    timeframe: {
      immediate: 'Weeks',
      shortTerm: '3-6 months',
      mediumTerm: '6-18 months'
    },
    metrics: {
      globalGdpLoss: I(0.7),
      regionalGdpLoss: I(16),
      confidence: I(68)
    },
    sectorImpacts: {
      construction: {
        gdpLoss: I(48),
        confidence: I(82),
        narrative: {
          en: 'Major projects delayed or suspended; funding pressures',
          ar: 'تأخير أو إيقاف المشاريع الكبرى؛ ضغوط التمويل'
        }
      },
      tourism: {
        gdpLoss: I(38),
        confidence: I(78),
        narrative: {
          en: 'Tourism sector growth plans halted',
          ar: 'توقف خطط نمو القطاع السياحي'
        }
      },
      investments: {
        gdpLoss: I(52),
        confidence: I(80),
        narrative: {
          en: 'Sovereign wealth fund returns pressured; capital projects frozen',
          ar: 'ضغط على عوائد صناديق الثروة السيادية؛ المشاريع الرأسمالية مجمدة'
        }
      }
    },
    nodeImpacts: [
      {
        nodeId: 'gcc',
        layers: {
          economy: I(22),
          finance: I(28),
          society: I(18)
        }
      }
    ],
    explanation: [
      {
        en: 'Vision 2030 depends on oil revenue and investment inflows',
        ar: 'تعتمد الرؤية 2030 على إيرادات النفط وتدفقات الاستثمار'
      },
      {
        en: 'Economic stress would force program reductions',
        ar: 'سيفرض الضغط الاقتصادي تقليص البرنامج'
      }
    ]
  })
};

// ============================================================================
// SCENARIO ENGINE REGISTRY
// ============================================================================

export const scenarioEngines: Record<string, ScenarioEngine> = {
  // ── Primary engines (12 mandatory) ──
  hormuz_closure: hormuzClosure,
  us_iran_escalation: usIranEscalation,
  airspace_restriction: gccAirspaceRestriction,
  hajj_disruption: hajjDisruption,
  jebel_ali_disruption: jebelAliDisruption,
  food_security_shock: foodSecurityShock,
  gcc_liquidity_stress: gccLiquidityStress,
  fx_gold_crypto_shock: fxGoldCryptoShock,
  insurance_repricing: insuranceRepricing,
  gcc_grid_failure: gccGridFailure,
  water_electricity_disruption: electricityWaterDisruption,
  vision2030_stress: vision2030Stress,
  // ── Aliases (scenarios sharing engines) ──
  military_repositioning: hormuzClosure,
  flight_rerouting: gccAirspaceRestriction,
  gcc_port_congestion: jebelAliDisruption,
  summer_utility_stress: gccGridFailure,
  mega_projects_pressure: vision2030Stress,
};

// ============================================================================
// HELPER FUNCTION
// ============================================================================

export function computeScenarioEngine(
  scenarioId: string,
  parameters?: Record<string, number>,
): ScenarioEngineOutput | null {
  // Try exact match first, then try engineId field from scenario
  const engine = scenarioEngines[scenarioId];
  if (!engine) {
    return null;
  }
  return engine.compute({ scenarioId, parameters });
}
