"""
authority.models — SQLAlchemy ORM table definitions for the Backend DAL.

Tables created in the SAME SQLite database as the signal store.
Register models on the shared Base imported from app.signals.store so that
Base.metadata.create_all() in signals.store.init_db() creates them in one pass.

Tables:
  decision_authority  — one active envelope per decision (unique on decision_id)
  authority_events    — append-only event log with SHA-256 hash chain
"""

from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

# Share the Base (and engine lifecycle) from the signal store so a single
# init_db() call creates all tables in one pass.
from app.signals.store import Base  # noqa: F401 — registers tables on shared metadata


class DecisionAuthorityRecord(Base):
    """Persisted authority envelope wrapping an OperatorDecision.

    One active row per decision_id (enforced via unique constraint).
    Resubmission increments revision_number in-place; no new row is created.
    """
    __tablename__ = "decision_authority"
    __table_args__ = (
        UniqueConstraint("decision_id", name="uq_authority_decision"),
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    authority_id      = Column(String(64),  primary_key=True)
    decision_id       = Column(String(64),  nullable=False, index=True)
    authority_status  = Column(String(32),  nullable=False, default="PROPOSED", index=True)
    revision_number   = Column(Integer,     nullable=False, default=1)
    escalation_level  = Column(Integer,     nullable=False, default=0)
    priority          = Column(Integer,     nullable=False, default=3)  # 1 (highest) – 5 (lowest)

    # ── Proposal ──────────────────────────────────────────────────────────────
    proposed_by        = Column(String(256), nullable=False)
    proposed_by_role   = Column(String(64),  nullable=False)
    proposal_rationale = Column(Text,        nullable=True)

    # ── Review ────────────────────────────────────────────────────────────────
    reviewer_id       = Column(String(256), nullable=True)
    reviewer_role     = Column(String(64),  nullable=True)
    review_started_at = Column(DateTime(timezone=True), nullable=True)

    # ── Authority decision (approve / reject / return / escalate) ─────────────
    authority_actor_id   = Column(String(256), nullable=True)
    authority_actor_role = Column(String(64),  nullable=True)
    authority_decided_at = Column(DateTime(timezone=True), nullable=True)
    authority_rationale  = Column(Text,        nullable=True)

    # ── Execution ─────────────────────────────────────────────────────────────
    executed_by      = Column(String(256), nullable=True)
    executed_by_role = Column(String(64),  nullable=True)
    executed_at      = Column(DateTime(timezone=True), nullable=True)
    execution_result = Column(Text,        nullable=True)

    # ── Linkage (by reference only — no copied payloads) ─────────────────────
    linked_outcome_id = Column(String(64), nullable=True)
    linked_value_id   = Column(String(64), nullable=True)

    # ── Source context ────────────────────────────────────────────────────────
    source_run_id           = Column(String(64), nullable=True)
    source_scenario_label   = Column(Text,       nullable=True)
    tags_json               = Column(Text,       nullable=False, default="[]")

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False)


class AuthorityEventRecord(Base):
    """Append-only authority event log with SHA-256 hash chain.

    One row per authority state transition.  Rows are never updated or deleted.
    The hash chain is per-authority_id: previous_event_hash links to the
    event_hash of the immediately preceding event for the same authority.
    """
    __tablename__ = "authority_events"

    event_id            = Column(String(64),  primary_key=True)
    authority_id        = Column(String(64),  nullable=False, index=True)
    decision_id         = Column(String(64),  nullable=False, index=True)
    action              = Column(String(64),  nullable=False)
    from_status         = Column(String(32),  nullable=True)   # null on PROPOSE
    to_status           = Column(String(32),  nullable=False)
    actor_id            = Column(String(256), nullable=False)
    actor_role          = Column(String(64),  nullable=False)
    timestamp           = Column(DateTime(timezone=True), nullable=False, index=True)
    notes               = Column(Text,        nullable=True)
    metadata_json       = Column(Text,        nullable=False, default="{}")
    event_hash          = Column(String(64),  nullable=False)
    previous_event_hash = Column(String(64),  nullable=True)   # null for first event
