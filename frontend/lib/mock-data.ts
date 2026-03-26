/* =================================================
    Deevo Sim — Mock Data
    Decision Intelligence Platform
   ================================================= */

import type {
  Scenario, Entity, GraphNode, GraphEdge,
  SimulationStep, SimulationReport, ChatMessage, Agent,
  DecisionOutput
} from './types'

/* -------------------------------------------------
   Scenarios
   ------------------------------------------------- */
export const mockScenarios: Scenario[] = [
  {
    id: 'sc-001',
    title: 'Fuel Price Increase in Saudi Arabia',
    titleAr: 'ارتفاع أسعار الوقود في السعودية',
    scenario: 'ارتفاع أسعار الوقود في السعودية بنسبة 10% وتأثير ذلك على تفاعل المستخدمين والرأي العام',
    raw_text: 'ارتفاع أسعار الوقود في السعودية بنسبة 10% وتأثير ذلك على تفاعل المستخدمين والرأي العام',
    language: 'ar',
    country: 'Saudi Arabia',
    category: 'Economy',
  },
  {
    id: 'sc-002',
    title: 'Kuwait Hashtag Trend',
    titleAr: 'هاشتاق فيرال في الكويت',
    scenario: 'انتشار هاشتاق فيرال حول سياسة اقتصادية جديدة في الكويت',
    raw_text: 'انتشار هاشتاق فيرال حول سياسة اقتصادية جديدة في الكويت',
    language: 'ar',
    country: 'Kuwait',
    category: 'Social',
  },
  {
    id: 'sc-003',
    title: 'Telecom Price Increase',
    titleAr: 'ارتفاع أسعار الاتصالات',
    scenario: 'ارتفاع أسعار خدمات الاتصالات في دول الخليج',
    raw_text: 'ارتفاع أسعار خدمات الاتصالات في دول الخليج',
    language: 'ar',
    country: 'GCC',
    category: 'Telecom',
  },
]

/* -------------------------------------------------
   Entities
   ------------------------------------------------- */
export const mockEntities: Entity[] = [
  { id: 'e-1', name: 'Ministry of Energy', nameAr: 'وزارة الطاقة', type: 'organization', weight: 0.9 },
  { id: 'e-2', name: 'Saudi Aramco', nameAr: 'أرامكو', type: 'organization', weight: 0.85 },
  { id: 'e-3', name: 'Citizens', nameAr: 'المواطنون', type: 'person', weight: 0.7 },
  { id: 'e-4', name: 'Twitter/X', type: 'platform', weight: 0.8 },
  { id: 'e-5', name: 'WhatsApp', type: 'platform', weight: 0.6 },
  { id: 'e-6', name: 'Al Arabiya', nameAr: 'العربية', type: 'media', weight: 0.75 },
  { id: 'e-7', name: 'Fuel Prices', nameAr: 'أسعار الوقود', type: 'topic', weight: 0.95 },
  { id: 'e-8', name: 'Saudi Arabia', nameAr: 'السعودية', type: 'region', weight: 0.65 },
]

/* -------------------------------------------------
   Graph
   ------------------------------------------------- */
export const mockGraphNodes: GraphNode[] = [
  { id: 'n-1', label: 'Ministry of Energy', type: 'organization', weight: 0.9 },
  { id: 'n-2', label: 'Saudi Aramco', type: 'organization', weight: 0.85 },
  { id: 'n-3', label: 'Citizens', type: 'person', weight: 0.7 },
  { id: 'n-4', label: 'Twitter/X', type: 'platform', weight: 0.8 },
  { id: 'n-5', label: 'WhatsApp', type: 'platform', weight: 0.6 },
  { id: 'n-6', label: 'Al Arabiya', type: 'media', weight: 0.75 },
  { id: 'n-7', label: 'Fuel Prices', type: 'topic', weight: 0.95 },
  { id: 'n-8', label: 'Saudi Arabia', type: 'region', weight: 0.65 },
]

export const mockGraphEdges: GraphEdge[] = [
  { id: 'ed-1', source: 'n-1', target: 'n-7', label: 'regulates', weight: 0.9 },
  { id: 'ed-2', source: 'n-2', target: 'n-7', label: 'supplies', weight: 0.85 },
  { id: 'ed-3', source: 'n-7', target: 'n-3', label: 'affects', weight: 0.8 },
  { id: 'ed-4', source: 'n-3', target: 'n-4', label: 'posts on', weight: 0.75 },
  { id: 'ed-5', source: 'n-3', target: 'n-5', label: 'shares via', weight: 0.6 },
  { id: 'ed-6', source: 'n-6', target: 'n-7', label: 'covers', weight: 0.7 },
  { id: 'ed-7', source: 'n-4', target: 'n-6', label: 'amplifies to', weight: 0.65 },
  { id: 'ed-8', source: 'n-1', target: 'n-8', label: 'governs', weight: 0.5 },
  { id: 'ed-9', source: 'n-7', target: 'n-8', label: 'impacts', weight: 0.7 },
  { id: 'ed-10', source: 'n-6', target: 'n-3', label: 'informs', weight: 0.55 },
]

/* -------------------------------------------------
   Simulation Steps
   ------------------------------------------------- */
export const mockSimulationSteps: SimulationStep[] = [
  {
    id: 1,
    title: 'Initial Trigger',
    titleAr: 'المحفز الأولي',
    description: 'News of the 10% fuel price hike breaks across local media channels and government portals.',
    descriptionAr: 'خبر ارتفاع أسعار الوقود بنسبة 10% ينتشر عبر وسائل الإعلام',
    timestamp: 'T+0h',
    sentiment: -0.3,
    visibility: 0.25,
    events: ['News breaks', 'Official announcement published', 'First social posts appear'],
  },
  {
    id: 2,
    title: 'Influencer Amplification',
    titleAr: 'تضخيم المؤثرين',
    description: 'Key influencers pick up the story. Hashtags trend. Engagement spikes across Twitter and WhatsApp.',
    descriptionAr: 'المؤثرون يلتقطون الخبر. الهاشتاقات تتصدر',
    timestamp: 'T+2h',
    sentiment: -0.6,
    visibility: 0.55,
    events: ['Influencer retweets', 'Hashtag trending', 'WhatsApp forwards surge'],
  },
  {
    id: 3,
    title: 'Media Cascade',
    titleAr: 'التصعيد الإعلامي',
    description: 'Al Arabiya and regional outlets run analysis segments. Narrative shifts from news to citizen impact.',
    descriptionAr: 'العربية والمنافذ الإقليمية تبث تحليلات',
    timestamp: 'T+6h',
    sentiment: -0.75,
    visibility: 0.8,
    events: ['TV coverage begins', 'Expert opinions aired', 'Sentiment peaks negative'],
  },
  {
    id: 4,
    title: 'Stabilization Phase',
    titleAr: 'مرحلة الاستقرار',
    description: 'Government issues clarification. Official accounts engage. Sentiment begins gradual recovery.',
    descriptionAr: 'الحكومة تصدر توضيحاً. المشاعر تبدأ بالتعافي',
    timestamp: 'T+12h',
    sentiment: -0.4,
    visibility: 0.65,
    events: ['Official response released', 'Influencer tone shifts', 'Engagement declines'],
  },
]

/* -------------------------------------------------
   Decision Output (Phase 1-3)
   ------------------------------------------------- */
export const mockDecisionOutput: DecisionOutput = {
  riskLevel: 'HIGH',
  expectedSpread: 72,
  sentiment: 'negative',
  primaryDriver: 'Influencer amplification combined with media coverage',
  primaryDriverAr: 'تضخيم المؤثرين مع تغطية إعلامية',
  criticalTimeWindow: 'First 2 hours are critical — immediate response required',
  criticalTimeWindowAr: 'أول ساعتين حرجة — يتطلب استجابة فورية',
  explanation: [
    {
      factor: 'Negative public sentiment',
      factorAr: 'مشاعر عامة سلبية',
      direction: 'amplifying',
      weight: 0.85,
      description: 'Negative events spread 2.3x faster than neutral ones in GCC social media ecosystems',
      descriptionAr: 'الأحداث السلبية تنتشر أسرع ب 2.3 مرة',
    },
    {
      factor: 'High influencer amplification',
      factorAr: 'تضخيم المؤثرين',
      direction: 'amplifying',
      weight: 0.78,
      description: 'Influencers with >70% reach accelerate information spread across platform boundaries',
      descriptionAr: 'المؤثرون يسرعون انتشار المعلومات عبر المنصات',
    },
    {
      factor: 'Absence of official response',
      factorAr: 'غياب الرد الرسمي',
      direction: 'amplifying',
      weight: 0.72,
      description: 'Delayed government response increases speculation and rumor propagation by up to 40%',
      descriptionAr: 'تأخر الرد الحكومي يزيد التكهنات بنسبة 40%',
    },
    {
      factor: 'Media coverage within first wave',
      factorAr: 'تغطية إعلامية في الموجة الأولى',
      direction: 'amplifying',
      weight: 0.65,
      description: 'Media pickup in the first cycle legitimizes the narrative and expands audience reach 3x',
      descriptionAr: 'التغطية الإعلامية توسع نطاق الجمهور 3 مرات',
    },
  ],
  recommendedActions: [
    {
      id: 'act-1',
      priority: 'immediate',
      action: 'Issue official statement within 2 hours',
      actionAr: 'إصدار بيان رسمي خلال ساعتين',
      rationale: 'Early official response reduces misinformation spread by 40% and stabilizes public sentiment',
      rationaleAr: 'الرد الرسمي المبكر يقلل انتشار المعلومات المضللة بنسبة 40%',
      timeframe: '0–2 hours',
      impact: 'high',
    },
    {
      id: 'act-2',
      priority: 'immediate',
      action: 'Engage top influencers with verified information',
      actionAr: 'إشراك أهم المؤثرين بمعلومات موثقة',
      rationale: 'Redirecting influencer narrative shifts public perception within 1 simulation cycle',
      rationaleAr: 'إعادة توجيه خطاب المؤثرين يغير التصور العام',
      timeframe: '0–4 hours',
      impact: 'high',
    },
    {
      id: 'act-3',
      priority: 'short-term',
      action: 'Activate crisis communication protocol',
      actionAr: 'تفعيل بروتوكول اتصال الأزمات',
      rationale: 'High-risk scenarios require coordinated multi-channel response with unified messaging',
      rationaleAr: 'السيناريوهات عالية المخاطر تتطلب استجابة منسقة',
      timeframe: '2–6 hours',
      impact: 'high',
    },
    {
      id: 'act-4',
      priority: 'monitoring',
      action: 'Deploy real-time sentiment monitoring across Twitter and WhatsApp',
      actionAr: 'نشر مراقبة المشاعر عبر تويتر وواتساب',
      rationale: 'Continuous monitoring enables early detection of narrative shifts and emerging risks',
      rationaleAr: 'المراقبة المستمرة تمكن من الكشف المبكر',
      timeframe: 'Ongoing',
      impact: 'medium',
    },
  ],
  narrative: {
    title: 'Fuel Price Increase in Saudi Arabia — Risk Simulation',
    titleAr: 'ارتفاع أسعار الوقود في السعودية — محاكاة المخاطر',
    subtitle: 'Decision Intelligence Analysis',
    subtitleAr: 'تحليل ذكاء القرار',
    summary: 'This simulation models public reaction dynamics across GCC social channels following a 10% fuel price adjustment. The scenario triggers a high-risk propagation pattern driven primarily by influencer amplification combined with media coverage.',
    summaryAr: 'تحاكي هذه المحاكاة ديناميكيات ردود الفعل العامة عبر قنوات التواصل الخليجية بعد تعديل أسعار الوقود بنسبة 10%.',
    riskDescription: 'This scenario presents significant reputational and operational risk requiring immediate executive attention and coordinated multi-channel response.',
    riskDescriptionAr: 'يمثل هذا السيناريو مخاطر كبيرة تتطلب اهتماماً تنفيذياً فورياً.',
  },
}

/* -------------------------------------------------
   Simulation Report (Phase 4 — 6-Section Brief)
   ------------------------------------------------- */
export const mockReport: SimulationReport = {
  prediction: 'Public backlash expected within 6 hours with high social media amplification. Sentiment recovery begins after official response but full stabilization requires 24–48 hours.',
  predictionAr: 'من المتوقع ردة فعل عامة خلال 6 ساعات مع تضخيم عالٍ عبر وسائل التواصل الاجتماعي.',
  mainDriver: 'Influencer amplification combined with media coverage',
  mainDriverAr: 'تضخيم المؤثرين مع تغطية إعلامية',
  spreadLevel: 'high',
  confidence: 0.82,
  topInfluencers: ['@energy_analyst', '@saudi_voice', '@gcc_economy', 'Al Arabiya News'],
  keyObservations: [
    'Negative sentiment amplified 2.3x by influencer network effect',
    'WhatsApp forwards created parallel narrative outside trackable platforms',
    'Government delay of 4+ hours significantly increased speculation volume',
    'Media coverage legitimized citizen frustration and expanded reach',
    'Youth demographic showed highest engagement velocity on Twitter',
  ],
  keyObservationsAr: [
    'المشاعر السلبية تضخمت 2.3 مرة بفعل شبكة المؤثرين',
    'رسائل الواتساب أنشأت رواية موازية خارج المنصات القابلة للتتبع',
    'تأخر الحكومة أكثر من 4 ساعات زاد حجم التكهنات',
  ],
  decision: mockDecisionOutput,
}

/* -------------------------------------------------
   Chat Messages
   ------------------------------------------------- */
export const mockChatMessages: ChatMessage[] = [
  {
    id: 'msg-1',
    role: 'analyst',
    content: 'Simulation initialized. Fuel Price scenario loaded with 8 entities and 6 agent personas. Decision intelligence engine is active.',
    timestamp: new Date().toISOString(),
  },
]

export const mockChatResponses: Record<string, string> = {
  why: 'This prediction is driven by three converging factors: (1) High influencer amplification — accounts with >70% reach picked up the story within the first cycle, (2) Absence of an early official response — which increased speculation volume by an estimated 40%, and (3) Media coverage by Al Arabiya and regional outlets legitimized the narrative. The combination triggers a HIGH-risk propagation pattern.',
  who: 'The top influencers driving spread are @energy_analyst (influence: 0.88), @saudi_voice (influence: 0.82), and @gcc_economy (influence: 0.75). Al Arabiya acts as the media amplifier. The Youth demographic shows the highest engagement velocity on Twitter, while Citizens drive WhatsApp forwards.',
  'what if': 'If the government issues an official response within 2 hours: risk drops from HIGH to MEDIUM, expected spread reduces from 72% to approximately 45%, and sentiment recovery begins 4 hours earlier. Engaging top influencers simultaneously could further reduce spread by 15–20%. Without intervention, the scenario reaches peak negative sentiment at T+6h.',
  action: 'Recommended immediate actions: (1) Issue official statement within 2 hours addressing the policy rationale, (2) Brief top 3 influencers with verified data and economic context, (3) Activate crisis communication protocol for coordinated multi-channel response. Monitoring: Deploy real-time sentiment tracking across Twitter and WhatsApp with 30-minute reporting intervals.',
  risk: 'Current risk assessment: HIGH. Risk score is driven by negative sentiment (weight: 0.85), influencer amplification (0.78), government response gap (0.72), and media cascade (0.65). Critical time window is the first 2 hours. Without intervention, probability of narrative becoming entrenched exceeds 80% by T+8h.',
}

/* -------------------------------------------------
   GCC Agent Personas
   ------------------------------------------------- */
export const mockAgents: Agent[] = [
  {
    id: 'agent-1',
    name: 'Saudi Citizen',
    nameAr: 'مواطن سعودي',
    archetype: 'reactive',
    platform: 'twitter',
    influence: 0.45,
    region: 'Saudi Arabia',
    description: 'Average citizen concerned about cost of living',
    descriptionAr: 'مواطن عادي مهتم بتكلفة المعيشة',
  },
  {
    id: 'agent-2',
    name: 'Kuwaiti Citizen',
    nameAr: 'مواطن كويتي',
    archetype: 'analytical',
    platform: 'twitter',
    influence: 0.40,
    region: 'Kuwait',
    description: 'Analytical observer comparing regional policies',
    descriptionAr: 'مراقب تحليلي يقارن السياسات الإقليمية',
  },
  {
    id: 'agent-3',
    name: 'Digital Influencer',
    nameAr: 'مؤثر رقمي',
    archetype: 'reactive',
    platform: 'twitter',
    influence: 0.88,
    region: 'GCC',
    description: 'High-reach content creator with rapid amplification capability',
    descriptionAr: 'صانع محتوى عالي الوصول',
  },
  {
    id: 'agent-4',
    name: 'Media Account',
    nameAr: 'حساب إعلامي',
    archetype: 'neutral',
    platform: 'news',
    influence: 0.75,
    region: 'GCC',
    description: 'News outlet covering breaking stories and analysis',
    descriptionAr: 'منفذ إخباري يغطي الأخبار العاجلة',
  },
  {
    id: 'agent-5',
    name: 'Government Voice',
    nameAr: 'صوت حكومي',
    archetype: 'analytical',
    platform: 'news',
    influence: 0.82,
    region: 'Saudi Arabia',
    description: 'Official government communications channel',
    descriptionAr: 'قناة الاتصالات الحكومية الرسمية',
  },
  {
    id: 'agent-6',
    name: 'Youth User',
    nameAr: 'شاب / شابة',
    archetype: 'reactive',
    platform: 'whatsapp',
    influence: 0.35,
    region: 'GCC',
    description: 'Young demographic with high engagement velocity',
    descriptionAr: 'فئة شبابية بسرعة تفاعل عالية',
  },
]
