"""Rule spec compiler — convert validated RuleSpec into DecisionRuleORM.

The compiler is the bridge between the declarative spec format and the
existing decision engine's ORM layer. It:
  1. Maps spec fields to DecisionRuleORM columns
  2. Serializes conditions into the JSONB format expected by the engine
  3. Preserves provenance (spec_version, author) in audit fields
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from src.data_foundation.models.tables import DecisionRuleORM
from src.data_foundation.rules.spec import RuleSpec


def compile_spec(spec: RuleSpec) -> DecisionRuleORM:
    """Compile a validated RuleSpec into a DecisionRuleORM instance.

    The ORM object is not persisted — the caller decides when to
    add it to a session and flush.

    Args:
        spec: A validated RuleSpec.

    Returns:
        DecisionRuleORM ready for persistence.
    """
    # Serialize conditions to the JSONB list format used by DecisionRuleORM
    conditions_json = [
        {
            "field": cond.field,
            "operator": cond.operator,
            "threshold": cond.threshold,
            "unit": cond.unit,
            "dataset": cond.dataset,
            "indicator_code": cond.indicator_code,
            "description": cond.description,
        }
        for cond in spec.conditions
    ]

    # Parse expiry_date if present
    expiry: Optional[datetime] = None
    if spec.expiry_date:
        from datetime import date as _date
        d = _date.fromisoformat(spec.expiry_date)
        expiry = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

    return DecisionRuleORM(
        rule_id=spec.rule_id,
        rule_name=spec.rule_name,
        rule_name_ar=spec.rule_name_ar,
        description=spec.description,
        version=spec.version,
        is_active=spec.is_active,
        conditions=conditions_json,
        condition_logic=spec.condition_logic,
        action=spec.action,
        action_params=spec.action_params,
        escalation_level=spec.escalation_level,
        applicable_countries=spec.applicable_countries or None,
        applicable_sectors=spec.applicable_sectors or None,
        applicable_scenarios=spec.applicable_scenarios or None,
        requires_human_approval=spec.requires_human_approval,
        cooldown_minutes=spec.cooldown_minutes,
        expiry_date=expiry,
        source_dataset_ids=spec.source_dataset_ids or None,
        tags=spec.tags or None,
        created_by=spec.author,
        approved_by=spec.approved_by,
        audit_notes=f"Compiled from spec v{spec.spec_version}",
    )


def compile_specs(specs: List[RuleSpec]) -> List[DecisionRuleORM]:
    """Compile a list of RuleSpecs into DecisionRuleORM instances."""
    return [compile_spec(s) for s in specs]
