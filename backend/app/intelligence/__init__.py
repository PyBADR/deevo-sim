"""
Impact Observatory | مرصد الأثر — Intelligence Adapter Foundation

Unified entry point for all external intelligence systems.

Layer contract:
    External payload (any source)
        → IntelligenceAdapter.normalize()
        → NormalizedIntelligenceSignal
        → (after HITL gate) SignalBridge.to_live_signal()
        → existing Signal Layer (LiveSignal → ScoredSignal → ScenarioSeed)

No external system may write directly to Decision / Outcome / Value layers.
All external intelligence MUST pass through this adapter layer.

Sub-modules:
    models      — NormalizedIntelligenceSignal + semantic separation types
    trace       — TracePayload, NormalizationWarning
    validators  — payload validation (ranges, timestamps, trace completeness)
    adapter     — orchestration + source-specific stubs
    bridge      — typed bridge contract: NormalizedIntelligenceSignal → LiveSignal

Source stubs (interfaces only — not yet integrated):
    sources/jet_nexus.py
    sources/trek.py
    sources/impact_observatory.py
"""
