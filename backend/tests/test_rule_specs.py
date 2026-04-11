"""Tests for the Rule Specification Layer.

Covers:
  1. RuleSpec schema — construction, validation, field constraints
  2. ConditionSpec — operators, threshold types, field references
  3. Loader — JSON loading, YAML loading, directory scanning, error handling
  4. Validator — structural, referential (indicator catalog), threshold range, governance, uniqueness
  5. Compiler — spec → DecisionRuleORM field mapping
  6. Built-in specs — the 4 production rule spec files load, validate, and compile
"""

from __future__ import annotations

import json
import tempfile
from datetime import date
from pathlib import Path

import pytest

from src.data_foundation.rules.spec import (
    ConditionSpec,
    RuleSpec,
    VALID_ACTIONS,
    VALID_DATASETS,
    VALID_OPERATORS,
)
from src.data_foundation.rules.loader import load_spec, load_specs_dir
from src.data_foundation.rules.validator import validate_spec, validate_all, ValidationResult
from src.data_foundation.rules.compiler import compile_spec, compile_specs


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

def _minimal_spec(**overrides) -> dict:
    """Return a minimal valid spec dict with optional overrides."""
    base = {
        "rule_id": "RULE-TEST-001",
        "rule_name": "Test Rule",
        "description": "A test rule.",
        "conditions": [
            {
                "field": "value",
                "operator": "lt",
                "threshold": 50.0,
                "dataset": "oil_energy_signals",
            }
        ],
        "action": "ALERT",
    }
    base.update(overrides)
    return base


def _minimal_condition(**overrides) -> dict:
    base = {
        "field": "value",
        "operator": "gt",
        "threshold": 100.0,
        "dataset": "banking_profiles",
    }
    base.update(overrides)
    return base


# ═════════════════════════════════════════════════════════════════════════════
# Test: ConditionSpec
# ═════════════════════════════════════════════════════════════════════════════


class TestConditionSpec:
    def test_valid_condition(self):
        c = ConditionSpec(**_minimal_condition())
        assert c.field == "value"
        assert c.operator == "gt"
        assert c.threshold == 100.0

    def test_with_indicator_code(self):
        c = ConditionSpec(
            field="value",
            operator="lt",
            threshold=55.0,
            indicator_code="BRENT_SPOT",
        )
        assert c.indicator_code == "BRENT_SPOT"
        assert c.dataset is None

    def test_with_description(self):
        c = ConditionSpec(
            field="npl_ratio_pct",
            operator="gt",
            threshold=5.0,
            dataset="banking_profiles",
            description="NPL ratio above 5%",
        )
        assert c.description == "NPL ratio above 5%"

    def test_invalid_operator_rejected(self):
        with pytest.raises(ValueError, match="Invalid operator"):
            ConditionSpec(
                field="value",
                operator="INVALID_OP",
                threshold=1.0,
                dataset="oil_energy_signals",
            )

    def test_all_operators_accepted(self):
        for op in VALID_OPERATORS:
            c = ConditionSpec(field="x", operator=op, threshold=1.0, dataset="oil_energy_signals")
            assert c.operator == op

    def test_extra_fields_rejected(self):
        with pytest.raises(ValueError):
            ConditionSpec(
                field="value",
                operator="gt",
                threshold=1.0,
                dataset="oil_energy_signals",
                unknown_field="bad",
            )


# ═════════════════════════════════════════════════════════════════════════════
# Test: RuleSpec
# ═════════════════════════════════════════════════════════════════════════════


class TestRuleSpec:
    def test_minimal_spec(self):
        s = RuleSpec(**_minimal_spec())
        assert s.rule_id == "RULE-TEST-001"
        assert s.version == 1
        assert s.condition_logic == "AND"
        assert s.escalation_level == "ELEVATED"
        assert s.is_active is False
        assert s.requires_human_approval is True

    def test_all_fields(self):
        s = RuleSpec(**_minimal_spec(
            rule_name_ar="قاعدة اختبار",
            version=2,
            condition_logic="OR",
            action_params={"notify": True},
            escalation_level="SEVERE",
            applicable_countries=["KW", "SA"],
            applicable_sectors=["energy", "banking"],
            applicable_scenarios=["saudi_oil_shock"],
            requires_human_approval=False,
            cooldown_minutes=120,
            is_active=True,
            expiry_date="2027-12-31",
            author="test-author",
            approved_by="test-approver",
            source_dataset_ids=["oil_energy_signals"],
            tags=["test", "oil"],
        ))
        assert s.rule_name_ar == "قاعدة اختبار"
        assert s.applicable_countries == ["KW", "SA"]
        assert s.expiry_date == "2027-12-31"

    def test_invalid_action_rejected(self):
        with pytest.raises(ValueError, match="Invalid action"):
            RuleSpec(**_minimal_spec(action="DESTROY"))

    def test_invalid_escalation_rejected(self):
        with pytest.raises(ValueError, match="Invalid escalation_level"):
            RuleSpec(**_minimal_spec(escalation_level="EXTREME"))

    def test_invalid_country_rejected(self):
        with pytest.raises(ValueError, match="Invalid country codes"):
            RuleSpec(**_minimal_spec(applicable_countries=["US", "KW"]))

    def test_empty_conditions_rejected(self):
        with pytest.raises(ValueError):
            RuleSpec(**_minimal_spec(conditions=[]))

    def test_extra_fields_rejected(self):
        with pytest.raises(ValueError):
            RuleSpec(**_minimal_spec(unknown_field="bad"))

    def test_all_actions_accepted(self):
        for action in VALID_ACTIONS:
            s = RuleSpec(**_minimal_spec(action=action))
            assert s.action == action


# ═════════════════════════════════════════════════════════════════════════════
# Test: Loader
# ═════════════════════════════════════════════════════════════════════════════


class TestLoader:
    def test_load_from_dict(self):
        spec = load_spec(_minimal_spec())
        assert spec.rule_id == "RULE-TEST-001"

    def test_load_from_json_file(self, tmp_path):
        p = tmp_path / "test_rule.json"
        p.write_text(json.dumps(_minimal_spec()))
        spec = load_spec(p)
        assert spec.rule_id == "RULE-TEST-001"

    def test_load_from_yaml_file(self, tmp_path):
        import yaml
        p = tmp_path / "test_rule.yaml"
        p.write_text(yaml.dump(_minimal_spec()))
        spec = load_spec(p)
        assert spec.rule_id == "RULE-TEST-001"

    def test_load_from_yml_file(self, tmp_path):
        import yaml
        p = tmp_path / "test_rule.yml"
        p.write_text(yaml.dump(_minimal_spec()))
        spec = load_spec(p)
        assert spec.rule_id == "RULE-TEST-001"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_spec("/nonexistent/path/rule.json")

    def test_unsupported_extension(self, tmp_path):
        p = tmp_path / "rule.xml"
        p.write_text("<rule/>")
        with pytest.raises(ValueError, match="Unsupported file type"):
            load_spec(p)

    def test_invalid_json_raises(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{invalid json")
        with pytest.raises(Exception):
            load_spec(p)

    def test_load_specs_dir(self, tmp_path):
        for i in range(3):
            p = tmp_path / f"rule_{i}.json"
            p.write_text(json.dumps(_minimal_spec(rule_id=f"RULE-DIR-{i:03d}")))
        specs = load_specs_dir(tmp_path)
        assert len(specs) == 3
        ids = {s.rule_id for s in specs}
        assert ids == {"RULE-DIR-000", "RULE-DIR-001", "RULE-DIR-002"}

    def test_load_specs_dir_skips_bad_files(self, tmp_path):
        (tmp_path / "good.json").write_text(json.dumps(_minimal_spec()))
        (tmp_path / "bad.json").write_text("{bad")
        (tmp_path / "readme.txt").write_text("not a spec")
        (tmp_path / ".hidden.json").write_text(json.dumps(_minimal_spec(rule_id="hidden")))
        specs = load_specs_dir(tmp_path)
        assert len(specs) == 1
        assert specs[0].rule_id == "RULE-TEST-001"

    def test_load_specs_dir_nonexistent(self, tmp_path):
        specs = load_specs_dir(tmp_path / "nope")
        assert specs == []

    def test_load_builtin_specs_dir(self):
        """The built-in specs/ directory should have 4 specs."""
        specs = load_specs_dir()
        assert len(specs) == 4


# ═════════════════════════════════════════════════════════════════════════════
# Test: Validator
# ═════════════════════════════════════════════════════════════════════════════


class TestValidator:
    def test_valid_spec_passes(self):
        spec = RuleSpec(**_minimal_spec())
        result = validate_spec(spec)
        assert result.passed
        assert result.valid == 1
        assert result.invalid == 0

    def test_invalid_dataset_in_condition(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "value", "operator": "gt", "threshold": 1.0, "dataset": "nonexistent_dataset"},
        ]))
        result = validate_spec(spec)
        assert not result.passed
        errors = result.errors()
        assert any("nonexistent_dataset" in e.message for e in errors)

    def test_indicator_code_not_in_catalog(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "value", "operator": "lt", "threshold": 50.0, "indicator_code": "FAKE_INDICATOR_XYZ"},
        ]))
        result = validate_spec(spec)
        assert any("FAKE_INDICATOR_XYZ" in i.message for i in result.issues)

    def test_indicator_code_in_catalog_passes(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "value", "operator": "lt", "threshold": 55.0, "indicator_code": "BRENT_SPOT"},
        ]))
        result = validate_spec(spec)
        assert result.passed

    def test_operator_in_requires_list_threshold(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "status", "operator": "in", "threshold": "OPERATIONAL", "dataset": "logistics_nodes"},
        ]))
        result = validate_spec(spec)
        errors = result.errors()
        assert any("list threshold" in e.message for e in errors)

    def test_operator_in_with_list_passes(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "status", "operator": "in", "threshold": ["OPERATIONAL", "DEGRADED"], "dataset": "logistics_nodes"},
        ]))
        result = validate_spec(spec)
        assert result.passed

    def test_between_requires_two_element_list(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "value", "operator": "between", "threshold": [10, 20, 30], "dataset": "oil_energy_signals"},
        ]))
        result = validate_spec(spec)
        errors = result.errors()
        assert any("[min, max]" in e.message for e in errors)

    def test_between_with_valid_list(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "value", "operator": "between", "threshold": [40.0, 120.0], "dataset": "oil_energy_signals"},
        ]))
        result = validate_spec(spec)
        assert result.passed

    def test_active_without_approval_warns(self):
        spec = RuleSpec(**_minimal_spec(is_active=True))
        result = validate_spec(spec)
        warnings = result.warnings()
        assert any("approved_by" in w.message for w in warnings)

    def test_active_with_approval_no_warning(self):
        spec = RuleSpec(**_minimal_spec(is_active=True, approved_by="admin"))
        result = validate_spec(spec)
        warnings = result.warnings()
        assert not any("approved_by" in w.message for w in warnings)

    def test_excessive_cooldown_warns(self):
        spec = RuleSpec(**_minimal_spec(cooldown_minutes=99999))
        result = validate_spec(spec)
        warnings = result.warnings()
        assert any("cooldown" in w.message.lower() for w in warnings)

    def test_invalid_expiry_date(self):
        spec = RuleSpec(**_minimal_spec(expiry_date="not-a-date"))
        result = validate_spec(spec)
        errors = result.errors()
        assert any("ISO date" in e.message for e in errors)

    def test_valid_expiry_date(self):
        spec = RuleSpec(**_minimal_spec(expiry_date="2027-12-31"))
        result = validate_spec(spec)
        assert result.passed

    def test_threshold_far_outside_range_warns(self):
        """BRENT_SPOT normal range is 40-120. Threshold of -500 should warn."""
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "value", "operator": "lt", "threshold": -500.0, "indicator_code": "BRENT_SPOT"},
        ]))
        result = validate_spec(spec)
        warnings = result.warnings()
        assert any("far below" in w.message for w in warnings)

    def test_field_without_dataset_or_indicator_or_dot(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "bare_field", "operator": "gt", "threshold": 1.0},
        ]))
        result = validate_spec(spec)
        errors = result.errors()
        assert any("dataset" in e.message.lower() or "indicator_code" in e.message.lower() for e in errors)

    def test_dot_notation_field_passes_without_dataset(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "oil_energy_signals.value", "operator": "lt", "threshold": 50.0},
        ]))
        result = validate_spec(spec)
        assert result.passed


class TestValidateAll:
    def test_duplicate_rule_ids(self):
        specs = [
            RuleSpec(**_minimal_spec(rule_id="RULE-DUP-001")),
            RuleSpec(**_minimal_spec(rule_id="RULE-DUP-001")),
        ]
        result = validate_all(specs)
        assert result.invalid >= 1
        assert any("Duplicate" in i.message for i in result.issues)

    def test_unique_ids_pass(self):
        specs = [
            RuleSpec(**_minimal_spec(rule_id="RULE-A")),
            RuleSpec(**_minimal_spec(rule_id="RULE-B")),
        ]
        result = validate_all(specs)
        assert result.valid == 2

    def test_validate_all_builtin_specs(self):
        """All 4 built-in specs should pass validation."""
        specs = load_specs_dir()
        result = validate_all(specs)
        errors = result.errors()
        assert errors == [], f"Built-in specs have errors: {[(e.rule_id, e.message) for e in errors]}"
        assert result.valid == 4


# ═════════════════════════════════════════════════════════════════════════════
# Test: Compiler
# ═════════════════════════════════════════════════════════════════════════════


class TestCompiler:
    def test_compile_minimal(self):
        spec = RuleSpec(**_minimal_spec())
        orm = compile_spec(spec)
        assert orm.rule_id == "RULE-TEST-001"
        assert orm.rule_name == "Test Rule"
        assert orm.description == "A test rule."
        assert orm.action == "ALERT"
        assert orm.condition_logic == "AND"
        assert orm.is_active is False
        assert orm.version == 1
        assert orm.escalation_level == "ELEVATED"

    def test_compile_conditions_json(self):
        spec = RuleSpec(**_minimal_spec(conditions=[
            {"field": "value", "operator": "lt", "threshold": 55.0, "indicator_code": "BRENT_SPOT", "unit": "USD_per_bbl"},
            {"field": "change_pct", "operator": "change_pct_lt", "threshold": -20.0, "dataset": "oil_energy_signals"},
        ]))
        orm = compile_spec(spec)
        assert isinstance(orm.conditions, list)
        assert len(orm.conditions) == 2
        assert orm.conditions[0]["field"] == "value"
        assert orm.conditions[0]["indicator_code"] == "BRENT_SPOT"
        assert orm.conditions[1]["operator"] == "change_pct_lt"

    def test_compile_scope(self):
        spec = RuleSpec(**_minimal_spec(
            applicable_countries=["KW", "SA"],
            applicable_sectors=["energy", "banking"],
            applicable_scenarios=["saudi_oil_shock"],
        ))
        orm = compile_spec(spec)
        assert orm.applicable_countries == ["KW", "SA"]
        assert orm.applicable_sectors == ["energy", "banking"]
        assert orm.applicable_scenarios == ["saudi_oil_shock"]

    def test_compile_governance(self):
        spec = RuleSpec(**_minimal_spec(
            requires_human_approval=False,
            cooldown_minutes=120,
            is_active=True,
            expiry_date="2027-06-30",
        ))
        orm = compile_spec(spec)
        assert orm.requires_human_approval is False
        assert orm.cooldown_minutes == 120
        assert orm.is_active is True
        assert orm.expiry_date is not None
        assert orm.expiry_date.year == 2027
        assert orm.expiry_date.month == 6

    def test_compile_audit_fields(self):
        spec = RuleSpec(**_minimal_spec(
            author="test-user",
            approved_by="admin",
        ))
        orm = compile_spec(spec)
        assert orm.created_by == "test-user"
        assert orm.approved_by == "admin"
        assert "spec v1.0.0" in orm.audit_notes

    def test_compile_empty_lists_become_none(self):
        spec = RuleSpec(**_minimal_spec(
            applicable_countries=[],
            applicable_sectors=[],
            tags=[],
        ))
        orm = compile_spec(spec)
        assert orm.applicable_countries is None
        assert orm.applicable_sectors is None
        assert orm.tags is None

    def test_compile_action_params(self):
        spec = RuleSpec(**_minimal_spec(
            action_params={"notify": True, "recipients": ["CRO"]},
        ))
        orm = compile_spec(spec)
        assert orm.action_params == {"notify": True, "recipients": ["CRO"]}

    def test_compile_specs_batch(self):
        specs = [
            RuleSpec(**_minimal_spec(rule_id="RULE-A")),
            RuleSpec(**_minimal_spec(rule_id="RULE-B")),
        ]
        orms = compile_specs(specs)
        assert len(orms) == 2
        assert orms[0].rule_id == "RULE-A"
        assert orms[1].rule_id == "RULE-B"

    def test_orm_type(self):
        from src.data_foundation.models.tables import DecisionRuleORM
        spec = RuleSpec(**_minimal_spec())
        orm = compile_spec(spec)
        assert isinstance(orm, DecisionRuleORM)


# ═════════════════════════════════════════════════════════════════════════════
# Test: Built-in spec files
# ═════════════════════════════════════════════════════════════════════════════


class TestBuiltinSpecs:
    """End-to-end: load → validate → compile each built-in spec."""

    def test_oil_shock_spec(self):
        spec = load_spec(Path(__file__).parent.parent / "src/data_foundation/rules/specs/oil_shock.json")
        assert spec.rule_id == "RULE-OIL-SHOCK-001"
        assert spec.condition_logic == "OR"
        assert len(spec.conditions) == 2
        assert spec.action == "ALERT"
        assert spec.escalation_level == "HIGH"
        assert "KW" in spec.applicable_countries
        result = validate_spec(spec)
        assert result.passed or not result.errors()
        orm = compile_spec(spec)
        assert orm.rule_id == "RULE-OIL-SHOCK-001"

    def test_rate_shift_spec(self):
        spec = load_spec(Path(__file__).parent.parent / "src/data_foundation/rules/specs/rate_shift.json")
        assert spec.rule_id == "RULE-RATE-SHIFT-001"
        assert spec.action == "MONITOR"
        assert len(spec.conditions) == 2
        assert spec.requires_human_approval is True
        result = validate_spec(spec)
        assert result.passed or not result.errors()
        orm = compile_spec(spec)
        assert orm.action == "MONITOR"

    def test_logistics_disruption_spec(self):
        spec = load_spec(Path(__file__).parent.parent / "src/data_foundation/rules/specs/logistics_disruption.json")
        assert spec.rule_id == "RULE-LOGISTICS-001"
        assert spec.action == "REBALANCE"
        assert len(spec.conditions) == 2
        result = validate_spec(spec)
        assert result.passed or not result.errors()
        orm = compile_spec(spec)
        assert orm.action == "REBALANCE"

    def test_liquidity_stress_spec(self):
        spec = load_spec(Path(__file__).parent.parent / "src/data_foundation/rules/specs/liquidity_stress.json")
        assert spec.rule_id == "RULE-LIQUIDITY-001"
        assert spec.action == "PAUSE"
        assert spec.escalation_level == "SEVERE"
        assert len(spec.conditions) == 3
        result = validate_spec(spec)
        assert result.passed or not result.errors()
        orm = compile_spec(spec)
        assert orm.escalation_level == "SEVERE"

    def test_all_specs_unique_ids(self):
        specs = load_specs_dir()
        ids = [s.rule_id for s in specs]
        assert len(ids) == len(set(ids)), f"Duplicate rule_ids: {ids}"

    def test_all_specs_have_arabic_name(self):
        specs = load_specs_dir()
        for s in specs:
            assert s.rule_name_ar, f"Spec {s.rule_id} missing Arabic name"

    def test_all_specs_have_author(self):
        specs = load_specs_dir()
        for s in specs:
            assert s.author, f"Spec {s.rule_id} missing author"

    def test_all_specs_have_tags(self):
        specs = load_specs_dir()
        for s in specs:
            assert len(s.tags) > 0, f"Spec {s.rule_id} has no tags"

    def test_all_specs_compile_to_orm(self):
        specs = load_specs_dir()
        orms = compile_specs(specs)
        assert len(orms) == 4
        for orm in orms:
            assert orm.rule_id is not None
            assert orm.conditions is not None
            assert len(orm.conditions) >= 1


# ═════════════════════════════════════════════════════════════════════════════
# Test: Package imports
# ═════════════════════════════════════════════════════════════════════════════


class TestPackageImports:
    def test_import_spec(self):
        from src.data_foundation.rules import RuleSpec, ConditionSpec
        assert RuleSpec is not None
        assert ConditionSpec is not None

    def test_import_loader(self):
        from src.data_foundation.rules import load_spec, load_specs_dir
        assert callable(load_spec)
        assert callable(load_specs_dir)

    def test_import_validator(self):
        from src.data_foundation.rules import validate_spec, validate_all
        assert callable(validate_spec)
        assert callable(validate_all)

    def test_import_compiler(self):
        from src.data_foundation.rules import compile_spec
        assert callable(compile_spec)
