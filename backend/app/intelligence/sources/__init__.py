"""
Intelligence Adapter Foundation — Source Adapter Stubs

Each module in this package is a source-specific adapter.
All adapters MUST:
    1. Accept a raw external payload (dict)
    2. Return a NormalizedIntelligenceSignal
    3. Never write to Decision / Outcome / Value layers
    4. Never bypass the validator

Currently: interfaces / stubs only.
Full implementation deferred to Jet Nexus / TREK / Observatory integration phases.
"""
