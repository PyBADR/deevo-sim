"""
Impact Observatory | مرصد الأثر — Data Trust Layer

Every external data source must pass through this layer before reaching
the intelligence engine. No raw data bypasses the trust pipeline.

Pipeline: fetch → normalize → validate → score → pass OR quarantine

Modules
-------
contracts/   — Pydantic event contract (TrustedEventContract)
adapters/    — Source adapters (BaseAdapter, GovernmentAdapter, RealEstateAdapter)
validation/  — Deterministic schema + range + completeness validation
scoring/     — Source trust scoring (5-dimension deterministic formula)
quarantine/  — SQLite-backed quarantine store for rejected records
pipeline/    — Orchestrator + bridge to existing intelligence engine
"""

__version__ = "1.0.0"
