"""
Impact Observatory | مرصد الأثر — Event Deduplication (Stage 4)

Detects and merges duplicate or conflicting events.
Uses content hash for exact dedup and severity comparison for conflicts.

Rules:
- Exact duplicate (same template + severity): merge, keep latest
- Near-duplicate (same template, different severity): take higher, warn
- Conflicting sources: take higher trust, reduce confidence by 0.1
"""

import hashlib
from app.domain.models.raw_event import NormalizedEvent


# In-memory dedup cache (per-run; resets between pipeline executions)
_dedup_cache: dict[str, NormalizedEvent] = {}


def _content_hash(event: NormalizedEvent) -> str:
    """Compute content hash for dedup comparison."""
    content = f"{event.canonical_type}:{event.severity:.2f}:{','.join(sorted(event.geographic_scope))}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def clear_dedup_cache():
    """Clear the dedup cache. Call at start of each pipeline run."""
    _dedup_cache.clear()


def deduplicate_event(event: NormalizedEvent) -> NormalizedEvent:
    """Check for duplicates and merge if necessary.

    Returns the event (possibly with adjusted confidence and warnings).
    """
    content_key = _content_hash(event)

    if content_key in _dedup_cache:
        existing = _dedup_cache[content_key]

        if abs(existing.severity - event.severity) < 0.01:
            # Exact duplicate — keep the new one with reduced confidence
            new_confidence = max(existing.confidence, event.confidence) - 0.05
            updated = NormalizedEvent(
                event_id=event.event_id,
                canonical_type=event.canonical_type,
                severity=event.severity,
                shock_vector=event.shock_vector,
                geographic_scope=event.geographic_scope,
                confidence=max(0.1, new_confidence),
                provenance_chain=event.provenance_chain + ["deduplicate:exact_merge"],
            )
            _dedup_cache[content_key] = updated
            return updated
        else:
            # Near-duplicate — take higher severity, warn
            merged_severity = max(existing.severity, event.severity)
            merged_confidence = max(existing.confidence, event.confidence) - 0.1
            # Use shock vector from higher-severity event
            shock_vector = event.shock_vector if event.severity >= existing.severity else existing.shock_vector
            updated = NormalizedEvent(
                event_id=event.event_id,
                canonical_type=event.canonical_type,
                severity=merged_severity,
                shock_vector=shock_vector,
                geographic_scope=list(set(existing.geographic_scope + event.geographic_scope)),
                confidence=max(0.1, merged_confidence),
                provenance_chain=event.provenance_chain + ["deduplicate:conflict_merge"],
            )
            _dedup_cache[content_key] = updated
            return updated

    # No duplicate found — cache and pass through
    _dedup_cache[content_key] = event
    provenance = event.provenance_chain.copy()
    if "deduplicate" not in provenance[-1:]:
        provenance.append("deduplicate:pass")
    return NormalizedEvent(
        event_id=event.event_id,
        canonical_type=event.canonical_type,
        severity=event.severity,
        shock_vector=event.shock_vector,
        geographic_scope=event.geographic_scope,
        confidence=event.confidence,
        provenance_chain=provenance,
    )
