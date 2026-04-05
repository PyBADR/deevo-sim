"""
Impact Observatory | مرصد الأثر — Intelligence Adapter API routes

POST /api/v1/intelligence/normalize
    Accept a raw external intelligence payload, run it through the adapter
    foundation, and return a typed NormalizedIntelligenceSignal summary.
    DOES NOT enter the signal pipeline — preview / normalization only.
    Requires: INGEST_INTELLIGENCE permission (OPERATOR+)

POST /api/v1/intelligence/validate
    Validate a raw payload against the adapter contract without normalizing.
    Returns a validation report: field-level errors + warnings.
    Requires: READ_INTELLIGENCE permission (ANALYST+)

POST /api/v1/intelligence/bridge-preview
    Normalize a payload AND attempt bridge conversion (NIS → LiveSignal).
    Returns preview of what LiveSignal would be produced.
    Does NOT submit to HITL — preview only.
    Requires: INGEST_INTELLIGENCE permission (OPERATOR+)

Error responses:
    400  — malformed JSON body
    401  — missing / invalid Authorization header
    403  — insufficient role for the requested action
    422  — payload failed adapter validation (violations list included)
    501  — source family adapter not yet implemented (stub)
"""

import logging
from typing import Any

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.rbac import Permission, has_permission
from app.core.security import authenticate
from app.intelligence.adapter import (
    normalize_for_preview,
    normalize_intelligence_payload,
    normalize_with_trek,
    normalize_with_simulation,
)
from app.intelligence.models import SourceFamily
from app.intelligence.trace import AdapterError
from app.intelligence.validators import validate_raw_payload, REQUIRED_RAW_FIELDS
from app.intelligence.trace import TraceBuilder
from app.intelligence.models import ADAPTER_VERSION

logger = logging.getLogger("observatory.intelligence.api")

router = APIRouter(prefix="/intelligence")


# ── Request / Response models ──────────────────────────────────────────────────

class IntelligencePayloadBody(BaseModel):
    """Raw intelligence payload submitted by an external system or operator.

    source (optional):
        When provided, identifies the source adapter to use and tells the
        endpoint that 'payload' is in the source's native format.
        Supported values: "jet_nexus"
        When omitted: 'payload' must be a full adapter-format dict that includes
        'source_family' and all standard adapter fields.

    payload:
        The raw payload dict. Schema depends on 'source':
          - source="jet_nexus" → native JN format (event_id, event_type, etc.)
          - source omitted     → adapter format (source_family, signal_type, etc.)

    enable_trek (optional, default False):
        When True, apply TREK enrichment after source normalization.
        TREK is the reasoning/enrichment layer that adds:
            - inferred_reasoning  — risk-type analysis items (LIQUIDITY_STRESS, etc.)
            - reasoning_summary   — narrative summary of TREK's conclusions
            - causal_chain        — ordered causal steps (observed → inferred)
            - adjusted scores     — severity/confidence updated by TREK
        TREK does NOT overwrite observed_evidence from the source.
        Supported for source="jet_nexus" and generic adapter-format payloads.

    Validation happens inside the adapter — not here. This keeps error messages
    adapter-specific and traceable.
    """
    source: str | None = Field(
        None,
        description="Source adapter hint: 'jet_nexus' | None (use adapter-format payload)",
    )
    payload: dict[str, Any] = Field(
        ...,
        description="Raw external intelligence payload.",
    )
    enable_trek: bool = Field(
        False,
        description=(
            "Apply TREK enrichment after normalization. "
            "Adds inferred_reasoning, reasoning_summary, causal_chain, adjusted scores. "
            "Observed evidence from the source adapter is never modified."
        ),
    )
    enable_simulation: bool = Field(
        False,
        description=(
            "Apply Impact Observatory simulation enrichment. "
            "Adds simulation_context with: scenario_label, impact_score, "
            "propagation_paths, exposure_estimates, time_horizon_hours. "
            "Simulation runs AFTER TREK when enable_trek=True (recommended). "
            "Simulation is ADVISORY — never overwrites observed or inferred data. "
            "All simulation output is clearly labeled SIMULATED."
        ),
    )


class ValidationReport(BaseModel):
    """Result of POST /api/v1/intelligence/validate."""
    valid:              bool
    source_family:      str | None
    violations:         list[dict[str, Any]]
    warnings:           list[dict[str, Any]]
    missing_fields:     list[str]
    adapter_version:    str


class NormalizeResponse(BaseModel):
    """Result of POST /api/v1/intelligence/normalize (success path)."""
    success:              bool
    normalized_signal_id: str
    normalization_status: str
    source_family:        str
    source_systems:       list[str]
    signal_type:          str
    title:                str
    severity_score:       float
    confidence_score:     float
    detected_at:          str
    time_horizon_hours:   int
    affected_domains:     list[str]
    semantic_summary:     dict[str, int]
    trace_payload:        dict[str, Any]


class BridgePreviewResponse(BaseModel):
    """Result of POST /api/v1/intelligence/bridge-preview."""
    success:              bool
    normalized_signal_id: str
    live_signal_id:       str
    source:               str
    sector:               str
    event_type:           str
    severity_raw:         float
    confidence_raw:       float
    entity_ids:           list[str]
    description:          str
    payload_keys:         list[str]   # keys present in live_signal.payload (not full payload for brevity)
    bridge_meta:          dict[str, Any]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _nis_to_response(signal) -> dict[str, Any]:
    """Convert a NormalizedIntelligenceSignal to a NormalizeResponse dict."""
    return {
        "success":              True,
        "normalized_signal_id": signal.normalized_signal_id,
        "normalization_status": signal.normalization_status,
        "source_family":        signal.source_family,
        "source_systems":       signal.source_systems,
        "signal_type":          signal.signal_type,
        "title":                signal.title,
        "severity_score":       signal.severity_score,
        "confidence_score":     signal.confidence_score,
        "detected_at":          signal.detected_at.isoformat(),
        "time_horizon_hours":   signal.time_horizon_hours,
        "affected_domains":     signal.affected_domains,
        "semantic_summary":     signal.semantic_summary(),
        "trace_payload":        signal.trace_payload,
    }


SUPPORTED_SOURCES: frozenset[str] = frozenset({"jet_nexus"})


def _route_to_source_adapter(source: str, payload: dict[str, Any]):
    """Dispatch to the named source adapter.  Returns NormalizedIntelligenceSignal.

    Raises AdapterError, NotImplementedError, or ValueError on failure.
    Raises ValueError for an unrecognised source name.
    """
    if source == "jet_nexus":
        from app.intelligence.sources.jet_nexus import adapt_jet_nexus_payload
        return adapt_jet_nexus_payload(payload)
    raise ValueError(
        f"Unsupported source '{source}'. Supported: {sorted(SUPPORTED_SOURCES)}"
    )


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post(
    "/normalize",
    response_model=NormalizeResponse,
    status_code=200,
    summary="Normalize an external intelligence payload",
    description=(
        "Run a raw external intelligence payload through the adapter foundation. "
        "Returns a normalized signal summary. Does NOT enter the signal pipeline. "
        "Use /bridge-preview to preview full HITL pipeline entry."
    ),
)
async def normalize_intelligence(
    body: IntelligencePayloadBody,
    authorization: str = Header(..., description="Bearer <token>"),
) -> dict[str, Any]:
    actor = authenticate(authorization)
    if not has_permission(actor.role, Permission.INGEST_INTELLIGENCE):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Role '{actor.role}' does not have INGEST_INTELLIGENCE permission. "
                "Required: OPERATOR or higher."
            ),
        )

    source            = body.source
    enable_trek       = body.enable_trek
    enable_simulation = body.enable_simulation
    logger.info(
        "intelligence.normalize actor=%s source=%s enable_trek=%s enable_simulation=%s",
        actor.user_id,
        source or body.payload.get("source_family", "?"),
        enable_trek,
        enable_simulation,
    )

    # ── Source-specific path (native format) ──────────────────────────────────
    if source is not None:
        if source not in SUPPORTED_SOURCES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported source '{source}'. Supported: {sorted(SUPPORTED_SOURCES)}",
            )
        try:
            signal = _route_to_source_adapter(source, body.payload)
            if enable_trek:
                from app.intelligence.sources.trek import enrich_with_trek
                signal = enrich_with_trek(signal)
            if enable_simulation:
                from app.intelligence.sources.impact_observatory import enrich_with_simulation
                signal = enrich_with_simulation(signal)
            return _nis_to_response(signal)
        except AdapterError as exc:
            raise HTTPException(
                status_code=422,
                detail={
                    "message":    str(exc),
                    "violations": [v.__dict__ for v in exc.violations],
                },
            )
        except Exception as exc:
            logger.exception("intelligence.normalize source=%s failed", source)
            raise HTTPException(status_code=500, detail=str(exc))

    # ── Generic path (adapter-format payload with source_family field) ────────
    result = normalize_for_preview(
        body.payload,
        enable_trek=enable_trek,
        enable_simulation=enable_simulation,
    )

    if not result.get("success"):
        error_code = result.get("error", "UNKNOWN")
        detail     = result.get("detail", "Normalization failed")
        violations = result.get("violations", [])

        if error_code == "NOT_IMPLEMENTED":
            raise HTTPException(status_code=501, detail=detail)
        elif error_code == "ADAPTER_ERROR":
            raise HTTPException(
                status_code=422,
                detail={
                    "message":    detail,
                    "violations": violations,
                },
            )
        else:
            logger.error("intelligence.normalize unexpected error: %s", detail)
            raise HTTPException(status_code=500, detail=detail)

    return result


@router.post(
    "/validate",
    response_model=ValidationReport,
    status_code=200,
    summary="Validate a raw intelligence payload without normalizing",
    description=(
        "Check a raw payload against the adapter contract. "
        "Returns field-level violations and warnings. "
        "Does not produce a NormalizedIntelligenceSignal."
    ),
)
async def validate_intelligence(
    body: IntelligencePayloadBody,
    authorization: str = Header(..., description="Bearer <token>"),
) -> ValidationReport:
    actor = authenticate(authorization)
    if not has_permission(actor.role, Permission.READ_INTELLIGENCE):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Role '{actor.role}' does not have READ_INTELLIGENCE permission. "
                "Required: ANALYST or higher."
            ),
        )

    source = body.source
    raw    = body.payload

    # ── Source-specific validation (native format) ────────────────────────────
    if source == "jet_nexus":
        from app.intelligence.sources.jet_nexus import (
            validate_jet_nexus_payload,
            JET_NEXUS_REQUIRED_FIELDS as JN_REQUIRED,
        )
        tb = TraceBuilder(
            source_family   = "jet_nexus",
            source_systems  = ["jet_nexus"],
            adapter_version = ADAPTER_VERSION,
        )
        validate_jet_nexus_payload(raw, tb)

        violations = [
            {
                "field":   v.field_name,
                "message": v.message,
                "value":   str(v.received_value)[:200],
                "rule":    v.rule,
            }
            for v in tb.get_violations()
        ]
        warnings = [
            {
                "field":    w.field_name,
                "message":  w.message,
                "severity": w.severity,
            }
            for w in tb.get_warnings()
        ]
        missing_fields = [
            f for f in JN_REQUIRED if f not in raw or raw[f] is None
        ]
        valid = len(violations) == 0

        logger.info(
            "intelligence.validate actor=%s source=jet_nexus valid=%s violations=%d",
            actor.user_id, valid, len(violations),
        )
        return ValidationReport(
            valid           = valid,
            source_family   = "jet_nexus",
            violations      = violations,
            warnings        = warnings,
            missing_fields  = missing_fields,
            adapter_version = ADAPTER_VERSION,
        )

    # ── Generic validation (adapter-format payload) ───────────────────────────
    source_family = raw.get("source_family")

    # Check source_family enum membership separately (gives cleaner error)
    sf_error: str | None = None
    if source_family not in [f.value for f in SourceFamily]:
        sf_error = (
            f"Unknown source_family '{source_family}'. "
            f"Accepted: {[f.value for f in SourceFamily]}"
        )

    # Run validation via TraceBuilder (same path as the adapter)
    tb = TraceBuilder(
        source_family    = str(source_family) if source_family else "",
        source_systems   = raw.get("source_systems", []),
        adapter_version  = ADAPTER_VERSION,
    )

    if not sf_error:
        validate_raw_payload(raw, tb)

    violations = [
        {
            "field":   v.field_name,
            "message": v.message,
            "value":   str(v.received_value)[:200],
            "rule":    v.rule,
        }
        for v in tb.get_violations()
    ]

    if sf_error:
        violations.insert(0, {
            "field":   "source_family",
            "message": sf_error,
            "value":   str(source_family)[:200],
            "rule":    "ENUM_MEMBERSHIP",
        })

    warnings = [
        {
            "field":    w.field_name,
            "message":  w.message,
            "severity": w.severity,
        }
        for w in tb.get_warnings()
    ]

    missing_fields = [
        f for f in REQUIRED_RAW_FIELDS if f not in raw or raw[f] is None
    ]

    valid = (len(violations) == 0)

    logger.info(
        "intelligence.validate actor=%s source_family=%s valid=%s violations=%d warnings=%d",
        actor.user_id,
        source_family,
        valid,
        len(violations),
        len(warnings),
    )

    return ValidationReport(
        valid            = valid,
        source_family    = str(source_family) if source_family else None,
        violations       = violations,
        warnings         = warnings,
        missing_fields   = missing_fields,
        adapter_version  = ADAPTER_VERSION,
    )


@router.post(
    "/bridge-preview",
    response_model=BridgePreviewResponse,
    status_code=200,
    summary="Preview bridge conversion: raw payload → LiveSignal (no HITL submission)",
    description=(
        "Normalize a payload AND convert it to a LiveSignal via the bridge. "
        "Returns a preview of the LiveSignal that would be submitted to HITL. "
        "Does NOT submit to the HITL queue — preview only."
    ),
)
async def bridge_preview(
    body: IntelligencePayloadBody,
    authorization: str = Header(..., description="Bearer <token>"),
) -> BridgePreviewResponse:
    actor = authenticate(authorization)
    if not has_permission(actor.role, Permission.INGEST_INTELLIGENCE):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Role '{actor.role}' does not have INGEST_INTELLIGENCE permission. "
                "Required: OPERATOR or higher."
            ),
        )

    source            = body.source
    enable_trek       = body.enable_trek
    enable_simulation = body.enable_simulation
    logger.info(
        "intelligence.bridge-preview actor=%s source=%s enable_trek=%s enable_simulation=%s",
        actor.user_id,
        source or body.payload.get("source_family", "?"),
        enable_trek,
        enable_simulation,
    )

    # Step 1: normalize (source-specific or generic path)
    try:
        if source is not None:
            if source not in SUPPORTED_SOURCES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported source '{source}'. Supported: {sorted(SUPPORTED_SOURCES)}",
                )
            signal = _route_to_source_adapter(source, body.payload)
        else:
            signal = normalize_intelligence_payload(body.payload)
        # Step 1b: optional TREK enrichment
        if enable_trek:
            from app.intelligence.sources.trek import enrich_with_trek
            signal = enrich_with_trek(signal)
        # Step 1c: optional simulation enrichment
        if enable_simulation:
            from app.intelligence.sources.impact_observatory import enrich_with_simulation
            signal = enrich_with_simulation(signal)
    except AdapterError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message":    str(exc),
                "violations": [v.__dict__ for v in exc.violations],
            },
        )
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    except Exception as exc:
        logger.exception("bridge-preview normalization failed")
        raise HTTPException(status_code=500, detail=str(exc))

    # Step 2: bridge → LiveSignal (preview only, no HITL submission)
    try:
        from app.intelligence.bridge import SignalBridge, SignalBridgeError
        live = SignalBridge.to_live_signal(signal)
    except (AdapterError, Exception) as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"Bridge conversion failed: {exc}",
                "stage":   "bridge",
            },
        )

    bridge_meta = live.payload.get("bridge_meta", {})

    return BridgePreviewResponse(
        success              = True,
        normalized_signal_id = signal.normalized_signal_id,
        live_signal_id       = live.signal_id,
        source               = live.source.value,
        sector               = live.sector.value,
        event_type           = live.event_type,
        severity_raw         = live.severity_raw,
        confidence_raw       = live.confidence_raw,
        entity_ids           = list(live.entity_ids),
        description          = live.description,
        payload_keys         = sorted(live.payload.keys()),
        bridge_meta          = bridge_meta,
    )
