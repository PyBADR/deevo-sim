import type {
  Scenario,
  Entity,
  GraphNode,
  GraphEdge,
  SimulationStep,
  SimulationReport,
  ChatMessage,
  Agent,
} from './types'

export const mockScenarios: Scenario[] = [
  {
    id: 'scenario_001',
    title: 'Fuel Price Increase in Saudi Arabia',
    scenario: 'ارتفاع أسعار الوقود في السعودية بنسبة 10% وتأثير ذلك على تفاعل المستخدمين والرأي العام',
    raw_text: 'ارتفاع أسعار الوقود في السعودية بنسبة 10% وتأثير ذلك على تفاعل المستخدمين والرأي العام',
    language: 'ar',
    country: 'Saudi Arabia',
    category: 'economy',
  },
  {
    id: 'scenario_002',
    title: 'Kuwait Hashtag Trend',
    scenario: 'انتشار وسم في الكويت بسبب قرار اقتصادي جديد وتفاعل الإعلام والمؤثرين معه',
    raw_text: 'انتشار وسم في الكويت بسبب قرار اقتصادي جديد وتفاعل الإعلام والمؤثرين معه',
    language: 'ar',
    country: 'Kuwait',
    category: 'public sentiment',
  },
  {
    id: 'scenario_003',
    title: 'Telecom Price Increase',
    scenario: 'إعلان شركة اتصالات عن رفع أسعار بعض الباقات في الخليج وما قد يسببه من ردود فعل',
    raw_text: 'إعلان شركة اتصالات عن رفع أسعار بعض الباقات في الخليج وما قد يسببه من ردود فعل',
    language: 'ar',
    country: 'GCC',
    category: 'business reaction',
  },
]

export const mockEntities: Entity[] = [
  { id: 'ent_001', name: 'Fuel Prices', type: 'Topic', weight: 0.95 },
  { id: 'ent_002', name: 'Saudi Arabia', type: 'Region', weight: 0.9 },
  { id: 'ent_003', name: 'Ministry of Energy', type: 'Organization', weight: 0.85 },
  { id: 'ent_004', name: 'Saudi Citizens', type: 'Person', weight: 0.8 },
  { id: 'ent_005', name: 'Social Media', type: 'Platform', weight: 0.75 },
  { id: 'ent_006', name: 'Economic Impact', type: 'Topic', weight: 0.7 },
  { id: 'ent_007', name: 'Public Opinion', type: 'Topic', weight: 0.65 },
  { id: 'ent_008', name: 'Transportation', type: 'Organization', weight: 0.6 },
]

export const mockGraphNodes: GraphNode[] = [
  { id: 'node_001', position: { x: 400, y: 50 }, data: { label: 'Fuel Prices', type: 'Topic', weight: 0.95 }, type: 'custom' },
  { id: 'node_002', position: { x: 150, y: 200 }, data: { label: 'Saudi Arabia', type: 'Region', weight: 0.9 }, type: 'custom' },
  { id: 'node_003', position: { x: 650, y: 200 }, data: { label: 'Ministry of Energy', type: 'Organization', weight: 0.85 }, type: 'custom' },
  { id: 'node_004', position: { x: 100, y: 380 }, data: { label: 'Saudi Citizens', type: 'Person', weight: 0.8 }, type: 'custom' },
  { id: 'node_005', position: { x: 400, y: 300 }, data: { label: 'Social Media', type: 'Platform', weight: 0.75 }, type: 'custom' },
  { id: 'node_006', position: { x: 700, y: 380 }, data: { label: 'Economic Impact', type: 'Topic', weight: 0.7 }, type: 'custom' },
  { id: 'node_007', position: { x: 250, y: 450 }, data: { label: 'Public Opinion', type: 'Topic', weight: 0.65 }, type: 'custom' },
  { id: 'node_008', position: { x: 550, y: 450 }, data: { label: 'Transportation', type: 'Organization', weight: 0.6 }, type: 'custom' },
]

export const mockGraphEdges: GraphEdge[] = [
  { id: 'edge_001', source: 'node_001', target: 'node_002', label: 'affects', animated: true },
  { id: 'edge_002', source: 'node_001', target: 'node_003', label: 'regulated by' },
  { id: 'edge_003', source: 'node_002', target: 'node_004', label: 'impacts' },
  { id: 'edge_004', source: 'node_004', target: 'node_005', label: 'reacts via', animated: true },
  { id: 'edge_005', source: 'node_005', target: 'node_007', label: 'amplifies', animated: true },
  { id: 'edge_006', source: 'node_001', target: 'node_006', label: 'causes' },
  { id: 'edge_007', source: 'node_006', target: 'node_008', label: 'disrupts' },
  { id: 'edge_008', source: 'node_003', target: 'node_001', label: 'regulates' },
  { id: 'edge_009', source: 'node_007', target: 'node_003', label: 'pressures' },
  { id: 'edge_010', source: 'node_004', target: 'node_007', label: 'shapes' },
]

export const mockSimulationSteps: SimulationStep[] = [
  {
    step: 1, label: 't1 — Initial Reaction',
    summary: 'News breaks on social media. Citizens begin sharing concerns about fuel costs. Early reactions are negative but contained.',
    sentiment_score: 0.35, visibility_score: 0.4,
    events: ['News published on local outlets', 'First wave of tweets', 'WhatsApp forwards begin'],
  },
  {
    step: 2, label: 't2 — Amplification',
    summary: 'Influencers engage. Hashtags trend nationally. Media outlets pick up the story. Sentiment turns sharply negative.',
    sentiment_score: 0.25, visibility_score: 0.7,
    events: ['Influencer amplification', 'Hashtag trending #أسعار_الوقود', 'Media coverage expands'],
  },
  {
    step: 3, label: 't3 — Peak Intensity',
    summary: 'Maximum public attention. Competing narratives emerge. Government response anticipated. Visibility at peak.',
    sentiment_score: 0.2, visibility_score: 0.92,
    events: ['Peak social engagement', 'Competing narratives', 'Calls for official response'],
  },
  {
    step: 4, label: 't4 — Stabilization',
    summary: 'Government issues clarification. Official response reduces intensity. Sentiment begins gradual recovery.',
    sentiment_score: 0.45, visibility_score: 0.6,
    events: ['Official statement released', 'Sentiment shifts positive', 'Engagement declining'],
  },
]

export const mockReport: SimulationReport = {
  prediction: 'High initial public backlash with gradual stabilization following government intervention. Expected 48-72 hour intensity cycle.',
  main_driver: 'Social media amplification by high-influence accounts combined with economic anxiety among citizens.',
  top_influencers: ['@gcc_analyst', '@saudi_voice', '@energy_watch', 'Ministry of Energy'],
  spread_level: 'high',
  confidence: 0.82,
  timeline_summary: [
    'Hour 0-6: Initial news break and organic sharing',
    'Hour 6-18: Influencer amplification and hashtag trending',
    'Hour 18-36: Peak intensity with media coverage',
    'Hour 36-72: Government response and gradual de-escalation',
  ],
  graph_observations: [
    'Fuel Prices node has highest centrality in the network',
    'Social Media acts as key amplification bridge',
    'Government response node shows strongest de-escalation potential',
    'Public Opinion influenced by 4 direct pathways',
  ],
}

export const mockChatMessages: ChatMessage[] = [
  {
    id: 'msg_001',
    role: 'assistant',
    content: 'Simulation complete. The scenario shows a high-spread pattern typical of GCC economic events. Ask me anything about the results.',
  },
]

export const mockAgents: Agent[] = [
  { id: 'agent_001', name: 'Ahmed Al-Saudi', archetype: 'Saudi Citizen', influence: 0.4, platform: 'Twitter', behavior: 'Reactive', sentiment: 'Negative' },
  { id: 'agent_002', name: 'Fatima Al-Kuwaiti', archetype: 'Kuwaiti Citizen', influence: 0.35, platform: 'Twitter', behavior: 'Analytical', sentiment: 'Neutral' },
  { id: 'agent_003', name: 'Khaled Digital', archetype: 'Influencer', influence: 0.85, platform: 'Twitter', behavior: 'Reactive', sentiment: 'Negative' },
  { id: 'agent_004', name: 'GCC Media Hub', archetype: 'Media Account', influence: 0.75, platform: 'News', behavior: 'Analytical', sentiment: 'Neutral' },
  { id: 'agent_005', name: 'Official Comms', archetype: 'Government Voice', influence: 0.9, platform: 'News', behavior: 'Neutral', sentiment: 'Positive' },
  { id: 'agent_006', name: 'Nora Youth', archetype: 'Youth User', influence: 0.3, platform: 'WhatsApp', behavior: 'Reactive', sentiment: 'Negative' },
]
