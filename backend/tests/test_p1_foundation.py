"""P1 Data Foundation — Comprehensive Test Suite.

Tests all models, seed data, ingestion pipeline, and validation layer.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure p1_foundation is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# ─── Models ──────────────────────────────────────────────────────────────────

from p1_foundation.models.enums import (
    Confidence,
    Country,
    Currency,
    DataQuality,
    DecisionAction,
    DecisionStatus,
    FrequencyType,
    Sector,
    Severity,
    SignalDirection,
    SourceType,
)
from p1_foundation.models.base import (
    P1BaseModel,
    ProvenanceMixin,
    GeoMixin,
    ConfidenceMixin,
    SectorMixin,
)
from p1_foundation.models.dataset_registry import DatasetRegistryEntry
from p1_foundation.models.source_registry import SourceRegistryEntry
from p1_foundation.models.entity_registry import EntityRegistryEntry
from p1_foundation.models.macro_indicators import MacroIndicatorRecord
from p1_foundation.models.signals import (
    InterestRateSignalRecord,
    OilEnergySignalRecord,
    FXSignalRecord,
    KuwaitCBKIndicatorRecord,
)
from p1_foundation.models.events import EventSignalRecord
from p1_foundation.models.sector_profiles import BankingSectorProfile, InsuranceSectorProfile
from p1_foundation.models.logistics import LogisticsNodeProfile
from p1_foundation.models.decision_rules import DecisionRuleRecord, RuleCondition
from p1_foundation.models.decision_logs import DecisionLogRecord

# ─── Ingestion ───────────────────────────────────────────────────────────────

from p1_foundation.ingestion.contracts import IngestionContract, FieldMapping, QualityGate
from p1_foundation.ingestion.loaders.base_loader import BaseLoader, IngestionResult
from p1_foundation.ingestion.loaders.api_loader import APILoader
from p1_foundation.ingestion.loaders.csv_loader import CSVLoader
from p1_foundation.ingestion.loaders.manual_loader import ManualLoader

# ─── Validation ──────────────────────────────────────────────────────────────

from p1_foundation.validation.validator import (
    validate_record,
    validate_batch,
    validate_referential_integrity,
    validate_all_datasets,
    ValidationReport,
)

# ─── Data Loader ─────────────────────────────────────────────────────────────

from p1_foundation.data.loader import (
    load_seed,
    load_and_validate,
    load_all_seeds,
    SEED_FILE_MAP,
)


# =============================================================================
# 1. ENUM TESTS
# =============================================================================

class TestEnums:
    def test_source_type_values(self):
        assert SourceType.API.value == "api"
        assert SourceType.CSV.value == "csv"
        assert SourceType.MANUAL.value == "manual"
        assert SourceType.DERIVED.value == "derived"

    def test_country_gcc_members(self):
        gcc = {Country.KW, Country.SA, Country.AE, Country.QA, Country.BH, Country.OM, Country.GCC}
        assert len(gcc) == 7

    def test_sector_values(self):
        assert Sector.BANKING.value == "banking"
        assert Sector.INSURANCE.value == "insurance"
        assert Sector.ENERGY.value == "energy"

    def test_currency_gcc(self):
        gcc_currencies = {Currency.KWD, Currency.SAR, Currency.AED, Currency.QAR, Currency.BHD, Currency.OMR}
        assert len(gcc_currencies) == 6

    def test_decision_action_values(self):
        assert DecisionAction.ALERT.value == "alert"
        assert DecisionAction.HEDGE.value == "hedge"
        assert DecisionAction.EXECUTE.value == "execute"

    def test_severity_ordering(self):
        levels = [s.value for s in Severity]
        assert "critical" in levels
        assert "info" in levels


# =============================================================================
# 2. BASE MODEL TESTS
# =============================================================================

class TestBaseModel:
    def test_base_model_creates_id(self):
        m = P1BaseModel(source_name="test", source_type=SourceType.MANUAL)
        assert m.id is not None
        assert len(m.id) == 36  # UUID

    def test_base_model_timestamps(self):
        m = P1BaseModel(source_name="test", source_type=SourceType.API)
        assert m.created_at is not None
        assert m.updated_at is not None

    def test_provenance_hash_deterministic(self):
        m = P1BaseModel(id="fixed-id", source_name="test", source_type=SourceType.API)
        h1 = m.provenance_hash()
        h2 = m.provenance_hash()
        assert h1 == h2
        assert len(h1) == 64  # SHA-256

    def test_touch_updates_timestamp(self):
        m = P1BaseModel(source_name="test", source_type=SourceType.API)
        old = m.updated_at
        m.touch()
        assert m.updated_at >= old

    def test_geo_mixin_validation(self):
        geo = GeoMixin(country=Country.KW, lat=29.3759, lng=47.9774)
        assert geo.country == Country.KW

    def test_geo_mixin_lat_bounds(self):
        with pytest.raises(Exception):
            GeoMixin(country=Country.KW, lat=91.0, lng=0.0)

    def test_confidence_mixin_defaults(self):
        conf = ConfidenceMixin()
        assert conf.confidence == Confidence.MEDIUM
        assert conf.confidence_score == 0.5

    def test_confidence_score_bounds(self):
        with pytest.raises(Exception):
            ConfidenceMixin(confidence_score=1.5)


# =============================================================================
# 3. REGISTRY MODEL TESTS
# =============================================================================

class TestRegistryModels:
    def test_dataset_registry(self):
        ds = DatasetRegistryEntry(
            dataset_name="test_dataset",
            display_name="Test Dataset",
            description="A test",
            owner="test_team",
            update_frequency=FrequencyType.DAILY,
            schema_ref="p1_foundation.models.base.P1BaseModel",
            source_name="internal",
            source_type=SourceType.DERIVED,
        )
        assert ds.dataset_name == "test_dataset"
        assert ds.is_active is True

    def test_source_registry(self):
        src = SourceRegistryEntry(
            source_id="test_src",
            display_name="Test Source",
            description="A test source",
            provider="Test Corp",
            update_frequency=FrequencyType.DAILY,
            source_name="test",
            source_type=SourceType.API,
        )
        assert src.source_id == "test_src"
        assert src.requires_auth is False

    def test_entity_registry(self):
        ent = EntityRegistryEntry(
            entity_id="TEST_BANK",
            display_name="Test Bank",
            entity_type="bank",
            country=Country.KW,
            sector=Sector.BANKING,
            source_name="manual",
            source_type=SourceType.MANUAL,
        )
        assert ent.entity_id == "TEST_BANK"
        assert ent.is_active is True


# =============================================================================
# 4. DOMAIN MODEL TESTS
# =============================================================================

class TestDomainModels:
    def test_macro_indicator(self):
        m = MacroIndicatorRecord(
            indicator_name="gdp_growth",
            display_name="GDP Growth",
            value=2.5,
            unit="%",
            period="2024-Q3",
            frequency=FrequencyType.QUARTERLY,
            country=Country.KW,
            source_name="cbk",
            source_type=SourceType.API,
        )
        assert m.value == 2.5
        assert m.direction == SignalDirection.STABLE

    def test_interest_rate_signal(self):
        ir = InterestRateSignalRecord(
            rate_name="cbk_discount",
            display_name="CBK Discount Rate",
            rate_value_pct=4.25,
            effective_date="2024-07-15",
            central_bank="CBK",
            currency=Currency.KWD,
            country=Country.KW,
            source_name="cbk",
            source_type=SourceType.API,
        )
        assert ir.rate_value_pct == 4.25

    def test_oil_energy_signal(self):
        oil = OilEnergySignalRecord(
            signal_name="brent_spot",
            display_name="Brent Spot",
            price_usd=82.0,
            observation_date="2024-10-15",
            source_name="opec",
            source_type=SourceType.API,
        )
        assert oil.price_usd == 82.0
        assert oil.benchmark == "Brent"

    def test_fx_signal(self):
        fx = FXSignalRecord(
            pair="KWD/USD",
            base_currency=Currency.KWD,
            quote_currency=Currency.USD,
            rate=3.259,
            observation_date="2024-10-15",
            source_name="bloomberg",
            source_type=SourceType.API,
        )
        assert fx.rate == 3.259
        assert fx.is_peg is False

    def test_cbk_indicator(self):
        cbk = KuwaitCBKIndicatorRecord(
            indicator_code="CBK-001",
            indicator_name="M2 Money Supply",
            value=42300.0,
            unit="KWD mn",
            period="2024-Q3",
            category="monetary",
            source_name="cbk",
            source_type=SourceType.API,
        )
        assert cbk.country == "KW"

    def test_event_signal(self):
        evt = EventSignalRecord(
            event_type="geopolitical",
            headline="Test event",
            description="Test description",
            severity=Severity.HIGH,
            event_date="2024-01-15",
            country=Country.GCC,
            source_name="acled",
            source_type=SourceType.API,
        )
        assert evt.is_active is True

    def test_banking_profile(self):
        bp = BankingSectorProfile(
            entity_id="ent-002",
            entity_name="NBK",
            total_assets_usd_bn=115.2,
            tier1_capital_ratio_pct=17.8,
            npl_ratio_pct=1.4,
            roa_pct=1.5,
            roe_pct=15.2,
            period="2024-Q3",
            country=Country.KW,
            source_name="annual",
            source_type=SourceType.MANUAL,
        )
        assert bp.stress_score == 0.0

    def test_insurance_profile(self):
        ip = InsuranceSectorProfile(
            entity_id="ent-006",
            entity_name="GIG",
            gross_written_premium_usd_mn=850.0,
            net_written_premium_usd_mn=620.0,
            combined_ratio_pct=92.5,
            solvency_ratio_pct=195.0,
            investment_yield_pct=4.2,
            period="2024-Q3",
            country=Country.KW,
            source_name="annual",
            source_type=SourceType.MANUAL,
        )
        assert ip.solvency_ratio_pct == 195.0

    def test_logistics_node(self):
        ln = LogisticsNodeProfile(
            entity_id="ent-009",
            node_name="Shuwaikh Port",
            node_type="port",
            period="2024-Q3",
            country=Country.KW,
            source_name="port_auth",
            source_type=SourceType.CSV,
        )
        assert ln.is_operational is True


# =============================================================================
# 5. DECISION MODEL TESTS
# =============================================================================

class TestDecisionModels:
    def test_rule_condition(self):
        cond = RuleCondition(
            field="price_usd",
            operator="lt",
            value=60.0,
            dataset="oil_energy_signals",
            source_name="internal",
            source_type=SourceType.DERIVED,
        )
        assert cond.operator == "lt"

    def test_decision_rule(self):
        rule = DecisionRuleRecord(
            rule_id="RULE-TEST-001",
            rule_name="Test Rule",
            description="A test rule",
            conditions=[
                RuleCondition(
                    field="price_usd",
                    operator="lt",
                    value=60.0,
                    dataset="oil_energy_signals",
                    source_name="internal",
                    source_type=SourceType.DERIVED,
                )
            ],
            action=DecisionAction.ALERT,
            severity=Severity.CRITICAL,
            source_name="internal",
            source_type=SourceType.MANUAL,
        )
        assert rule.is_active is True
        assert rule.priority == 5

    def test_decision_rule_requires_conditions(self):
        with pytest.raises(Exception):
            DecisionRuleRecord(
                rule_id="RULE-EMPTY",
                rule_name="Empty",
                description="No conditions",
                conditions=[],
                action=DecisionAction.ALERT,
                severity=Severity.LOW,
                source_name="internal",
                source_type=SourceType.MANUAL,
            )

    def test_decision_log(self):
        log = DecisionLogRecord(
            log_id="LOG-001",
            rule_id="RULE-TEST-001",
            rule_name="Test Rule",
            action=DecisionAction.ALERT,
            status=DecisionStatus.APPROVED,
            severity=Severity.CRITICAL,
            trigger_data_hash="abc123",
            trigger_summary="Test trigger",
            source_name="internal",
            source_type=SourceType.DERIVED,
        )
        assert log.status == DecisionStatus.APPROVED


# =============================================================================
# 6. SEED DATA TESTS
# =============================================================================

class TestSeedData:
    """Validate every seed file loads and passes schema validation."""

    @pytest.mark.parametrize("dataset_name", list(SEED_FILE_MAP.keys()))
    def test_seed_loads_and_validates(self, dataset_name):
        records = load_and_validate(dataset_name)
        assert len(records) > 0, f"{dataset_name} seed is empty"

    @pytest.mark.parametrize("dataset_name", list(SEED_FILE_MAP.keys()))
    def test_seed_ids_unique(self, dataset_name):
        raw = load_seed(dataset_name)
        ids = [r["id"] for r in raw]
        assert len(ids) == len(set(ids)), f"Duplicate IDs in {dataset_name}"

    def test_all_seeds_load(self):
        all_seeds = load_all_seeds()
        assert len(all_seeds) == len(SEED_FILE_MAP)

    def test_entity_registry_has_gcc_spread(self):
        records = load_seed("entity_registry")
        countries = {r["country"] for r in records}
        assert "KW" in countries
        assert "SA" in countries
        assert "AE" in countries

    def test_entity_types_diverse(self):
        records = load_seed("entity_registry")
        types = {r["entity_type"] for r in records}
        assert "bank" in types
        assert "insurer" in types
        assert "port" in types

    def test_decision_rules_have_valid_actions(self):
        records = load_seed("decision_rules")
        valid_actions = {a.value for a in DecisionAction}
        for r in records:
            assert r["action"] in valid_actions

    def test_decision_logs_reference_valid_rules(self):
        rules = load_seed("decision_rules")
        rule_ids = {r["rule_id"] for r in rules}
        logs = load_seed("decision_logs")
        for log in logs:
            assert log["rule_id"] in rule_ids, f"Log references unknown rule: {log['rule_id']}"


# =============================================================================
# 7. INGESTION TESTS
# =============================================================================

class TestIngestion:
    def _make_contract(self, **overrides) -> IngestionContract:
        defaults = {
            "contract_id": "test-contract",
            "source_id": "test-source",
            "target_model": "p1_foundation.models.base.P1BaseModel",
            "target_dataset": "test_dataset",
            "source_type": SourceType.API,
            "update_frequency": FrequencyType.DAILY,
        }
        defaults.update(overrides)
        return IngestionContract(**defaults)

    def test_api_loader_json_data(self):
        contract = self._make_contract()
        loader = APILoader(contract)
        result = loader.ingest(json_data=[{"field": "value"}, {"field": "value2"}])
        assert result.total_raw == 2
        assert result.accepted == 2

    def test_api_loader_json_path(self):
        contract = self._make_contract()
        loader = APILoader(contract)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([{"a": 1}, {"a": 2}], f)
            f.flush()
            result = loader.ingest(json_path=f.name)
        os.unlink(f.name)
        assert result.total_raw == 2

    def test_api_loader_response_key(self):
        contract = self._make_contract()
        loader = APILoader(contract)
        result = loader.ingest(json_data={"data": [{"x": 1}], "meta": {}}, response_key="data")
        assert result.total_raw == 1

    def test_csv_loader_string(self):
        contract = self._make_contract(source_type=SourceType.CSV)
        loader = CSVLoader(contract)
        csv_str = "name,value\nalpha,10\nbeta,20\n"
        result = loader.ingest(csv_string=csv_str)
        assert result.total_raw == 2
        assert result.accepted == 2

    def test_csv_loader_file(self):
        contract = self._make_contract(source_type=SourceType.CSV)
        loader = CSVLoader(contract)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2\nx,1\ny,2\nz,3\n")
            f.flush()
            result = loader.ingest(csv_path=f.name)
        os.unlink(f.name)
        assert result.total_raw == 3

    def test_manual_loader(self):
        contract = self._make_contract(source_type=SourceType.MANUAL)
        loader = ManualLoader(contract)
        result = loader.ingest(
            records=[{"indicator": "gdp", "value": 2.5}],
            analyst="test_analyst",
        )
        assert result.total_raw == 1
        assert result.records[0]["_submitted_by"] == "test_analyst"

    def test_field_mappings(self):
        contract = self._make_contract(
            field_mappings=[
                FieldMapping(source_field="src_name", target_field="name", required=True),
                FieldMapping(source_field="src_val", target_field="value", transform="to_float"),
            ]
        )
        loader = APILoader(contract)
        result = loader.ingest(json_data=[{"src_name": "test", "src_val": "42.5"}])
        assert result.records[0]["name"] == "test"
        assert result.records[0]["value"] == 42.5

    def test_quality_gate_reject(self):
        contract = self._make_contract(
            quality_gates=[
                QualityGate(field="value", check="range", params={"min": 0, "max": 100}, severity="error"),
            ]
        )
        loader = APILoader(contract)
        result = loader.ingest(json_data=[{"value": 150}])
        assert result.rejected == 1
        assert result.accepted == 0

    def test_quality_gate_warning(self):
        contract = self._make_contract(
            quality_gates=[
                QualityGate(field="value", check="range", params={"min": 0, "max": 100}, severity="warning"),
            ]
        )
        loader = APILoader(contract)
        result = loader.ingest(json_data=[{"value": 150}])
        assert result.accepted == 1
        assert result.warnings == 1

    def test_quality_gate_not_null(self):
        contract = self._make_contract(
            quality_gates=[
                QualityGate(field="required_field", check="not_null", severity="error"),
            ]
        )
        loader = APILoader(contract)
        result = loader.ingest(json_data=[{"required_field": None}])
        assert result.rejected == 1

    def test_quality_gate_in_set(self):
        contract = self._make_contract(
            quality_gates=[
                QualityGate(field="status", check="in_set", params={"values": ["active", "inactive"]}, severity="error"),
            ]
        )
        loader = APILoader(contract)
        result = loader.ingest(json_data=[{"status": "unknown"}])
        assert result.rejected == 1

    def test_provenance_hash_attached(self):
        contract = self._make_contract()
        loader = APILoader(contract)
        result = loader.ingest(json_data=[{"x": 1}])
        assert "provenance_hash" in result.records[0]
        assert len(result.records[0]["provenance_hash"]) == 64

    def test_batch_provenance_hash(self):
        contract = self._make_contract()
        loader = APILoader(contract)
        result = loader.ingest(json_data=[{"x": 1}, {"x": 2}])
        assert len(result.provenance_hash) == 64

    def test_empty_input(self):
        contract = self._make_contract()
        loader = APILoader(contract)
        result = loader.ingest(json_data=[])
        assert result.total_raw == 0
        assert result.accepted == 0


# =============================================================================
# 8. VALIDATION TESTS
# =============================================================================

class TestValidation:
    def test_validate_valid_record(self):
        record = {
            "source_name": "test",
            "source_type": "api",
            "indicator_name": "gdp",
            "display_name": "GDP",
            "value": 2.5,
            "unit": "%",
            "period": "2024-Q3",
            "frequency": "quarterly",
            "country": "KW",
        }
        is_valid, issues = validate_record(record, MacroIndicatorRecord)
        assert is_valid
        assert len(issues) == 0

    def test_validate_invalid_record(self):
        record = {"source_name": "test"}  # Missing required fields
        is_valid, issues = validate_record(record, MacroIndicatorRecord)
        assert not is_valid
        assert len(issues) > 0

    def test_validate_batch(self):
        records = [
            {
                "source_name": "test",
                "source_type": "api",
                "indicator_name": "gdp",
                "display_name": "GDP",
                "value": 2.5,
                "unit": "%",
                "period": "2024-Q3",
                "frequency": "quarterly",
                "country": "KW",
            },
            {"source_name": "test"},  # invalid
        ]
        report = validate_batch(records, MacroIndicatorRecord, "test_batch")
        assert report.total_records == 2
        assert report.valid_records == 1
        assert report.invalid_records == 1
        assert not report.passed

    def test_referential_integrity_pass(self):
        records = [{"entity_id": "ent-001"}, {"entity_id": "ent-002"}]
        valid_ids = {"ent-001", "ent-002", "ent-003"}
        issues = validate_referential_integrity(records, "entity_id", valid_ids, "test")
        assert len(issues) == 0

    def test_referential_integrity_fail(self):
        records = [{"entity_id": "ent-001"}, {"entity_id": "ent-999"}]
        valid_ids = {"ent-001", "ent-002"}
        issues = validate_referential_integrity(records, "entity_id", valid_ids, "test")
        assert len(issues) == 1
        assert "ent-999" in issues[0].message

    def test_referential_integrity_list_field(self):
        records = [{"affected_entities": ["ent-001", "ent-999"]}]
        valid_ids = {"ent-001", "ent-002"}
        issues = validate_referential_integrity(records, "affected_entities", valid_ids, "test")
        assert len(issues) == 1

    def test_referential_integrity_null_skip(self):
        records = [{"entity_id": None}]
        valid_ids = {"ent-001"}
        issues = validate_referential_integrity(records, "entity_id", valid_ids, "test")
        assert len(issues) == 0

    def test_validate_all_datasets(self):
        macro_records = load_seed("macro_indicators")
        datasets = {
            "macro_indicators": (macro_records, MacroIndicatorRecord),
        }
        reports = validate_all_datasets(datasets)
        assert "macro_indicators" in reports
        assert reports["macro_indicators"].passed

    def test_validate_all_seed_datasets(self):
        """Validate every seed dataset passes schema validation."""
        for name, (filename, model_class) in SEED_FILE_MAP.items():
            records = load_seed(name)
            report = validate_batch(records, model_class, name)
            assert report.passed, f"{name}: {report.error_count} errors — {[i.message for i in report.issues[:3]]}"


# =============================================================================
# 9. CROSS-DATASET INTEGRITY TESTS
# =============================================================================

class TestCrossDatasetIntegrity:
    def test_banking_profiles_reference_valid_entities(self):
        entities = load_seed("entity_registry")
        entity_ids = {e["id"] for e in entities}
        banking = load_seed("banking_profiles")
        for bp in banking:
            assert bp["entity_id"] in entity_ids, f"Banking profile references unknown entity: {bp['entity_id']}"

    def test_insurance_profiles_reference_valid_entities(self):
        entities = load_seed("entity_registry")
        entity_ids = {e["id"] for e in entities}
        insurance = load_seed("insurance_profiles")
        for ip in insurance:
            assert ip["entity_id"] in entity_ids, f"Insurance profile references unknown entity: {ip['entity_id']}"

    def test_logistics_nodes_reference_valid_entities(self):
        entities = load_seed("entity_registry")
        entity_ids = {e["id"] for e in entities}
        logistics = load_seed("logistics_nodes")
        for ln in logistics:
            assert ln["entity_id"] in entity_ids, f"Logistics node references unknown entity: {ln['entity_id']}"

    def test_decision_logs_reference_valid_rules(self):
        rules = load_seed("decision_rules")
        rule_ids = {r["rule_id"] for r in rules}
        logs = load_seed("decision_logs")
        for log in logs:
            assert log["rule_id"] in rule_ids

    def test_all_datasets_reference_valid_dataset_ids(self):
        datasets = load_seed("dataset_registry")
        valid_ds_ids = {d["id"] for d in datasets}
        for name in ["macro_indicators", "interest_rate_signals", "oil_energy_signals",
                      "fx_signals", "cbk_indicators", "event_signals",
                      "banking_profiles", "insurance_profiles", "logistics_nodes"]:
            records = load_seed(name)
            for r in records:
                ds_id = r.get("dataset_id")
                if ds_id:
                    assert ds_id in valid_ds_ids, f"{name} record references unknown dataset_id: {ds_id}"
