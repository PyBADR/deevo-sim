"""
Impact Observatory | مرصد الأثر
Macro Context Engine — derives macro-economic context signals from scenario
simulation results.

NOT a signal intake pipeline (that lives in src/macro/).
This engine DERIVES what macro conditions a scenario implies, so the UI
can show "Triggered by: Oil +12%, Maritime disruption +60%" alongside
the scenario results.

Every signal is deterministically derived from real simulation outputs:
  - Scenario type → which macro domain is affected
  - Severity → magnitude of change
  - Sector stress → domain-specific impact levels
  - Financial impact → system risk index

All values are marked status="simulated" — no real market feeds.
"""
from __future__ import annotations

import logging
from typing import Any

from src.utils import clamp, format_loss_usd

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# Bilingual macro signal catalog — maps scenario domains to macro indicators
# ═══════════════════════════════════════════════════════════════════════════════

_MACRO_SIGNAL_DEFS: list[dict[str, Any]] = [
    {
        "id": "oil_price",
        "name_en": "Oil Price Shock",
        "name_ar": "صدمة أسعار النفط",
        "unit": "%",
        "sectors": {"energy", "maritime"},
        "base_multiplier": 18.0,   # severity 1.0 → +18%
        "direction": "up",
    },
    {
        "id": "interest_rate",
        "name_en": "Interest Rate Pressure",
        "name_ar": "ضغط أسعار الفائدة",
        "unit": "bps",
        "sectors": {"banking", "government", "fintech"},
        "base_multiplier": 125.0,  # severity 1.0 → +125bps
        "direction": "up",
    },
    {
        "id": "liquidity_stress",
        "name_en": "Liquidity Stress Index",
        "name_ar": "مؤشر ضغط السيولة",
        "unit": "",
        "sectors": {"banking", "fintech", "government"},
        "base_multiplier": 1.0,    # severity 1.0 → index 1.0
        "direction": "up",
    },
    {
        "id": "trade_disruption",
        "name_en": "Trade Disruption Score",
        "name_ar": "مؤشر تعطل التجارة",
        "unit": "%",
        "sectors": {"maritime", "logistics", "energy"},
        "base_multiplier": 65.0,   # severity 1.0 → +65%
        "direction": "up",
    },
    {
        "id": "insurance_claims_surge",
        "name_en": "Insurance Claims Surge",
        "name_ar": "ارتفاع المطالبات التأمينية",
        "unit": "x",
        "sectors": {"insurance"},
        "base_multiplier": 4.2,    # severity 1.0 → 4.2x surge
        "direction": "up",
    },
    {
        "id": "cyber_disruption",
        "name_en": "Cyber Disruption Index",
        "name_ar": "مؤشر التعطل السيبراني",
        "unit": "",
        "sectors": {"fintech", "infrastructure"},
        "base_multiplier": 1.0,    # severity 1.0 → index 1.0
        "direction": "up",
    },
    {
        "id": "fx_pressure",
        "name_en": "FX / Peg Pressure",
        "name_ar": "ضغط سعر الصرف",
        "unit": "bps",
        "sectors": {"banking", "government", "energy"},
        "base_multiplier": 80.0,   # severity 1.0 → +80bps spread
        "direction": "up",
    },
    {
        "id": "sovereign_spread",
        "name_en": "Sovereign CDS Spread",
        "name_ar": "فارق أسعار CDS السيادي",
        "unit": "bps",
        "sectors": {"government", "banking"},
        "base_multiplier": 200.0,  # severity 1.0 → +200bps
        "direction": "up",
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# Impact level classification
# ═══════════════════════════════════════════════════════════════════════════════

def _impact_level(magnitude: float, base_multiplier: float) -> str:
    """Classify macro signal impact: HIGH / MEDIUM / LOW."""
    ratio = abs(magnitude) / max(base_multiplier, 0.01)
    if ratio >= 0.60:
        return "high"
    if ratio >= 0.30:
        return "medium"
    return "low"


def _format_value(magnitude: float, unit: str, direction: str) -> str:
    """Format macro signal value for display."""
    sign = "+" if direction == "up" and magnitude >= 0 else ""
    if unit == "bps":
        return f"{sign}{round(magnitude)}bps"
    if unit == "%":
        return f"{sign}{magnitude:.0f}%"
    if unit == "x":
        return f"{magnitude:.1f}x"
    # Dimensionless index
    return f"{magnitude:.2f}"


# ═══════════════════════════════════════════════════════════════════════════════
# Core derivation
# ═══════════════════════════════════════════════════════════════════════════════

def derive_macro_context(result: dict) -> dict:
    """
    Derive macro-economic context signals from a simulation result.

    Uses real simulation data:
      - severity → magnitude scaling
      - sectors_affected → which macro signals are relevant
      - sector_analysis stresses → signal intensity
      - financial_impact → system risk index
      - banking_stress / insurance_stress → domain-specific amplifiers

    Returns:
      {
        "macro_signals": [...],
        "system_risk_index": float,
        "trigger_summary_en": str,
        "trigger_summary_ar": str,
        "status": "simulated",
      }
    """
    severity = clamp(result.get("severity", 0.5), 0.01, 1.0)
    scenario_id = result.get("scenario_id", "unknown")

    # Gather affected sectors from scenario catalog metadata
    sectors_affected: set[str] = set()
    sector_analysis = result.get("sector_analysis", [])
    for sa in sector_analysis:
        s = sa.get("sector", "")
        if s:
            sectors_affected.add(s.lower())

    # Sector stress lookup
    stress_by_sector: dict[str, float] = {}
    for sa in sector_analysis:
        s = sa.get("sector", "")
        if s:
            stress_by_sector[s.lower()] = sa.get("stress", 0.0)

    # Domain-specific amplifiers from detailed stress blocks
    banking_agg = result.get("banking_stress", {}).get("aggregate_stress", 0.0)
    insurance_agg = result.get("insurance_stress", {}).get("aggregate_stress", 0.0)
    fintech_agg = result.get("fintech_stress", {}).get("aggregate_stress", 0.0)

    # ── Derive each macro signal ──
    signals: list[dict] = []

    for sig_def in _MACRO_SIGNAL_DEFS:
        # Signal fires only if scenario affects relevant sectors
        overlap = sig_def["sectors"] & sectors_affected
        if not overlap:
            continue

        # Compute magnitude from severity × base_multiplier × sector stress
        # Use the highest stress among overlapping sectors as amplifier
        max_sector_stress = max(
            (stress_by_sector.get(s, 0.0) for s in overlap),
            default=0.0,
        )
        # Blend: 60% from severity, 40% from sector stress
        blend = severity * 0.60 + max_sector_stress * 0.40
        magnitude = blend * sig_def["base_multiplier"]

        # Domain-specific amplification
        if sig_def["id"] == "liquidity_stress" and banking_agg > 0:
            magnitude = clamp(banking_agg, 0.0, 1.0)
        elif sig_def["id"] == "insurance_claims_surge" and insurance_agg > 0:
            magnitude = max(1.0, 1.0 + insurance_agg * 3.2)
        elif sig_def["id"] == "cyber_disruption" and fintech_agg > 0:
            magnitude = clamp(fintech_agg, 0.0, 1.0)

        impact = _impact_level(magnitude, sig_def["base_multiplier"])

        signals.append({
            "id": sig_def["id"],
            "name_en": sig_def["name_en"],
            "name_ar": sig_def["name_ar"],
            "value": _format_value(magnitude, sig_def["unit"], sig_def["direction"]),
            "raw_value": round(magnitude, 4),
            "unit": sig_def["unit"],
            "impact": impact,
            "status": "simulated",
            "sectors": sorted(overlap),
        })

    # Sort by impact severity (high first)
    impact_order = {"high": 0, "medium": 1, "low": 2}
    signals.sort(key=lambda s: (impact_order.get(s["impact"], 9), -s["raw_value"]))

    # ── System Risk Index ──
    # Composite of URS + top sector stresses + severity
    urs = result.get("unified_risk_score", 0.0)
    if isinstance(urs, dict):
        urs = urs.get("score", 0.0)
    avg_stress = sum(stress_by_sector.values()) / max(len(stress_by_sector), 1)
    system_risk_index = clamp(
        round(urs * 0.50 + avg_stress * 0.30 + severity * 0.20, 4),
        0.0, 1.0,
    )

    # ── Bilingual trigger summary ──
    top3 = signals[:3]
    if top3:
        parts_en = [f"{s['name_en']} {s['value']}" for s in top3]
        parts_ar = [f"{s['name_ar']} {s['value']}" for s in top3]
        trigger_summary_en = "Triggered by: " + " · ".join(parts_en)
        trigger_summary_ar = "ناتج عن: " + " · ".join(parts_ar)
    else:
        trigger_summary_en = "No macro signals derived for this scenario."
        trigger_summary_ar = "لم يتم استخلاص إشارات اقتصاد كلي لهذا السيناريو."

    logger.info(
        "Derived %d macro signals for scenario '%s' (SRI=%.2f)",
        len(signals), scenario_id, system_risk_index,
    )

    return {
        "macro_signals": signals,
        "system_risk_index": system_risk_index,
        "trigger_summary_en": trigger_summary_en,
        "trigger_summary_ar": trigger_summary_ar,
        "status": "simulated",
    }
