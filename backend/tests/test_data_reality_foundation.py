"""Data Reality Foundation — Test Suite.

Tests ORM model definitions, Pydantic schemas, seed data validation,
and repository class structure. Does NOT require a running database —
all tests are unit-level.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ORM Model Import Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestORMImports:
    """Verify all ORM models can be imported and have correct table names."""

    def test_import_source_truth_registry(self):
        from src.data_foundation.models.reality_tables import SourceTruthRegistryORM
        assert SourceTruthRegistryORM.__tablename__ == "df_source_truth_registry"

    def test_import_raw_source_record(self):
        from src.data_foundation.models.reality_tables import RawSourceRecordORM
        assert RawSourceRecordORM.__tablename__ == "df_raw_source_records"

    def test_import_indicator_catalog(self):
        from src.data_foundation.models.reality_tables import IndicatorCatalogORM
        assert IndicatorCatalogORM.__tablename__ == "df_indicator_catalog"

    def test_import_canonical_observation(self):
        from src.data_foundation.models.reality_tables import CanonicalObservationORM
        assert CanonicalObservationORM.__tablename__ == "df_canonical_observations"

    def test_import_source_fetch_run(self):
        from src.data_foundation.models.reality_tables import SourceFetchRunORM
        assert SourceFetchRunORM.__tablename__ == "df_source_fetch_runs"

    def test_import_normalization_run(self):
        from src.data_foundation.models.reality_tables import NormalizationRunORM
        assert NormalizationRunORM.__tablename__ == "df_normalization_runs"

    def test_all_models_in_package_init(self):
        from src.data_foundation.models import (
            SourceTruthRegistryORM,
            RawSourceRecordORM,
            IndicatorCatalogORM,
            CanonicalObservationORM,
            SourceFetchRunORM,
            NormalizationRunORM,
        )
        assert all([
            SourceTruthRegistryORM,
            RawSourceRecordORM,
            IndicatorCatalogORM,
            CanonicalObservationORM,
            SourceFetchRunORM,
            NormalizationRunORM,
        ])


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ORM Column Structure Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestORMColumnStructure:
    """Verify every table has foundation columns and domain-specific columns."""

    def _column_names(self, orm_cls) -> set:
        return {c.name for c in orm_cls.__table__.columns}

    def test_foundation_columns_present(self):
        from src.data_foundation.models.reality_tables import (
            SourceTruthRegistryORM,
            RawSourceRecordORM,
            IndicatorCatalogORM,
            CanonicalObservationORM,
            SourceFetchRunORM,
            NormalizationRunORM,
        )
        foundation = {"schema_version", "tenant_id", "created_at", "updated_at", "provenance_hash"}
        for cls in [
            SourceTruthRegistryORM,
            RawSourceRecordORM,
            IndicatorCatalogORM,
            CanonicalObservationORM,
            SourceFetchRunORM,
            NormalizationRunORM,
        ]:
            cols = self._column_names(cls)
            missing = foundation - cols
            assert not missing, f"{cls.__tablename__} missing foundation columns: {missing}"

    def test_source_truth_registry_columns(self):
        from src.data_foundation.models.reality_tables import SourceTruthRegistryORM
        cols = self._column_names(SourceTruthRegistryORM)
        required = {"source_id", "source_name", "source_type", "provider_org",
                     "reliability", "update_frequency", "is_active", "base_url"}
        assert required.issubset(cols)

    def test_raw_source_record_mandatory_provenance(self):
        from src.data_foundation.models.reality_tables import RawSourceRecordORM
        cols = self._column_names(RawSourceRecordORM)
        mandatory = {"source_url", "fetch_timestamp", "content_hash", "period_start", "period_end"}
        assert mandatory.issubset(cols)

    def test_indicator_catalog_columns(self):
        from src.data_foundation.models.reality_tables import IndicatorCatalogORM
        cols = self._column_names(IndicatorCatalogORM)
        required = {"indicator_id", "indicator_code", "indicator_name", "category",
                     "unit", "frequency", "is_active"}
        assert required.issubset(cols)

    def test_canonical_observation_mandatory_provenance(self):
        from src.data_foundation.models.reality_tables import CanonicalObservationORM
        cols = self._column_names(CanonicalObservationORM)
        mandatory = {"source_url", "fetch_timestamp", "content_hash", "period_start", "period_end",
                      "source_id", "indicator_id", "indicator_code", "value", "country"}
        assert mandatory.issubset(cols)

    def test_source_fetch_run_mandatory_provenance(self):
        from src.data_foundation.models.reality_tables import SourceFetchRunORM
        cols = self._column_names(SourceFetchRunORM)
        mandatory = {"source_url", "fetch_timestamp", "period_start", "period_end", "status"}
        assert mandatory.issubset(cols)

    def test_normalization_run_columns(self):
        from src.data_foundation.models.reality_tables import NormalizationRunORM
        cols = self._column_names(NormalizationRunORM)
        required = {"run_id", "fetch_run_id", "source_id", "status",
                     "raw_records_input", "observations_created", "validation_errors"}
        assert required.issubset(cols)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ORM Index Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestORMIndexes:
    """Verify strategic indexes exist on each table."""

    def _index_names(self, orm_cls) -> set:
        return {idx.name for idx in orm_cls.__table__.indexes}

    def test_source_truth_indexes(self):
        from src.data_foundation.models.reality_tables import SourceTruthRegistryORM
        idxs = self._index_names(SourceTruthRegistryORM)
        assert "ix_df_str_type_reliability" in idxs
        assert "ix_df_str_active_freq" in idxs

    def test_raw_record_indexes(self):
        from src.data_foundation.models.reality_tables import RawSourceRecordORM
        idxs = self._index_names(RawSourceRecordORM)
        assert "ix_df_raw_source_fetch" in idxs
        assert "ix_df_raw_content_hash" in idxs
        assert "ix_df_raw_norm_status" in idxs

    def test_indicator_catalog_indexes(self):
        from src.data_foundation.models.reality_tables import IndicatorCatalogORM
        idxs = self._index_names(IndicatorCatalogORM)
        assert "ix_df_ic_category_sector" in idxs
        assert "ix_df_ic_active_freq" in idxs

    def test_canonical_observation_indexes(self):
        from src.data_foundation.models.reality_tables import CanonicalObservationORM
        idxs = self._index_names(CanonicalObservationORM)
        assert "ix_df_co_indicator_period" in idxs
        assert "ix_df_co_source_fetch" in idxs
        assert "ix_df_co_country_date" in idxs

    def test_fetch_run_indexes(self):
        from src.data_foundation.models.reality_tables import SourceFetchRunORM
        idxs = self._index_names(SourceFetchRunORM)
        assert "ix_df_sfr_source_status" in idxs
        assert "ix_df_sfr_fetch_ts" in idxs

    def test_normalization_run_indexes(self):
        from src.data_foundation.models.reality_tables import NormalizationRunORM
        idxs = self._index_names(NormalizationRunORM)
        assert "ix_df_nr_fetch_run" in idxs
        assert "ix_df_nr_source_status" in idxs


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Pydantic Schema Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPydanticSchemas:
    """Verify Pydantic schemas validate correctly."""

    def test_source_truth_registry_schema(self):
        from src.data_foundation.schemas.reality_schemas import SourceTruthRegistryEntry
        entry = SourceTruthRegistryEntry(
            source_id="test-src",
            source_name="Test Source",
            source_type="API",
            provider_org="Test Corp",
            update_frequency="DAILY",
        )
        assert entry.source_id == "test-src"
        assert entry.is_active is True
        assert entry.provenance_hash is not None

    def test_raw_source_record_schema(self):
        from src.data_foundation.schemas.reality_schemas import RawSourceRecord
        record = RawSourceRecord(
            record_id=str(uuid4()),
            source_id="test-src",
            fetch_run_id=str(uuid4()),
            source_url="https://example.com/data",
            fetch_timestamp=datetime.now(timezone.utc),
            content_hash="a" * 64,
            period_start="2024-01-01",
            period_end="2024-03-31",
            raw_payload={"key": "value"},
        )
        assert record.normalization_status == "PENDING"
        assert record.content_type == "application/json"

    def test_indicator_catalog_schema(self):
        from src.data_foundation.schemas.reality_schemas import IndicatorCatalogEntry
        indicator = IndicatorCatalogEntry(
            indicator_id="ic-test",
            indicator_code="GDP_GROWTH_TEST",
            indicator_name="Test GDP Growth",
            category="MACRO",
            unit="percent",
            frequency="QUARTERLY",
        )
        assert indicator.value_type == "NUMERIC"
        assert indicator.precision_digits == 2
        assert indicator.is_active is True

    def test_canonical_observation_schema(self):
        from src.data_foundation.schemas.reality_schemas import CanonicalObservation
        obs = CanonicalObservation(
            observation_id=str(uuid4()),
            indicator_id="ic-001",
            indicator_code="GDP_GROWTH_KW",
            value=2.5,
            unit="percent",
            country="KW",
            period_start="2024-01-01",
            period_end="2024-03-31",
            frequency="QUARTERLY",
            observation_date="2024-04-15",
            source_id="src-imf-weo",
            source_url="https://imf.org/weo",
            fetch_timestamp=datetime.now(timezone.utc),
            content_hash="b" * 64,
        )
        assert obs.confidence_score == 0.8
        assert obs.is_provisional is False

    def test_source_fetch_run_schema(self):
        from src.data_foundation.schemas.reality_schemas import SourceFetchRun
        run = SourceFetchRun(
            run_id=str(uuid4()),
            source_id="src-cbk",
            source_url="https://cbk.gov.kw/stats",
            fetch_timestamp=datetime.now(timezone.utc),
            period_start="2024-01-01",
            period_end="2024-03-31",
        )
        assert run.status == "PENDING"
        assert run.records_fetched == 0

    def test_normalization_run_schema(self):
        from src.data_foundation.schemas.reality_schemas import NormalizationRun
        run = NormalizationRun(
            run_id=str(uuid4()),
            fetch_run_id=str(uuid4()),
            source_id="src-cbk",
        )
        assert run.status == "PENDING"
        assert run.normalization_version == "1.0.0"

    def test_provenance_hash_computed(self):
        from src.data_foundation.schemas.reality_schemas import SourceTruthRegistryEntry
        e1 = SourceTruthRegistryEntry(
            source_id="src-a",
            source_name="Source A",
            source_type="API",
            provider_org="Corp",
            update_frequency="DAILY",
        )
        e2 = SourceTruthRegistryEntry(
            source_id="src-b",
            source_name="Source B",
            source_type="API",
            provider_org="Corp",
            update_frequency="DAILY",
        )
        assert e1.provenance_hash != e2.provenance_hash
        assert len(e1.provenance_hash) == 64


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Seed Data Tests
# ═══════════════════════════════════════════════════════════════════════════════

SEED_DIR = Path(__file__).parent.parent / "src" / "data_foundation" / "seed"


class TestSeedData:
    """Validate seed JSON files load and have correct structure."""

    def test_source_truth_registry_loads(self):
        path = SEED_DIR / "source_truth_registry.json"
        with open(path) as f:
            data = json.load(f)
        assert len(data) >= 9
        assert all("source_id" in r for r in data)

    def test_source_truth_ids_unique(self):
        path = SEED_DIR / "source_truth_registry.json"
        with open(path) as f:
            data = json.load(f)
        ids = [r["source_id"] for r in data]
        assert len(ids) == len(set(ids))

    def test_source_truth_required_fields(self):
        path = SEED_DIR / "source_truth_registry.json"
        with open(path) as f:
            data = json.load(f)
        required = {"source_id", "source_name", "source_type", "provider_org",
                     "reliability", "update_frequency", "is_active"}
        for r in data:
            missing = required - set(r.keys())
            assert not missing, f"Source {r['source_id']} missing: {missing}"

    def test_source_truth_validates_as_pydantic(self):
        from src.data_foundation.schemas.reality_schemas import SourceTruthRegistryEntry
        path = SEED_DIR / "source_truth_registry.json"
        with open(path) as f:
            data = json.load(f)
        for r in data:
            entry = SourceTruthRegistryEntry.model_validate(r)
            assert entry.source_id == r["source_id"]

    def test_indicator_catalog_loads(self):
        path = SEED_DIR / "indicator_catalog.json"
        with open(path) as f:
            data = json.load(f)
        assert len(data) >= 18
        assert all("indicator_code" in r for r in data)

    def test_indicator_catalog_codes_unique(self):
        path = SEED_DIR / "indicator_catalog.json"
        with open(path) as f:
            data = json.load(f)
        codes = [r["indicator_code"] for r in data]
        assert len(codes) == len(set(codes))

    def test_indicator_catalog_required_fields(self):
        path = SEED_DIR / "indicator_catalog.json"
        with open(path) as f:
            data = json.load(f)
        required = {"indicator_id", "indicator_code", "indicator_name",
                     "category", "unit", "frequency", "is_active"}
        for r in data:
            missing = required - set(r.keys())
            assert not missing, f"Indicator {r['indicator_code']} missing: {missing}"

    def test_indicator_catalog_validates_as_pydantic(self):
        from src.data_foundation.schemas.reality_schemas import IndicatorCatalogEntry
        path = SEED_DIR / "indicator_catalog.json"
        with open(path) as f:
            data = json.load(f)
        for r in data:
            entry = IndicatorCatalogEntry.model_validate(r)
            assert entry.indicator_code == r["indicator_code"]

    def test_indicator_sources_reference_valid_sources(self):
        """Indicator primary_source_id must exist in source_truth_registry."""
        with open(SEED_DIR / "source_truth_registry.json") as f:
            sources = json.load(f)
        source_ids = {s["source_id"] for s in sources}

        with open(SEED_DIR / "indicator_catalog.json") as f:
            indicators = json.load(f)
        for ind in indicators:
            ps = ind.get("primary_source_id")
            if ps:
                assert ps in source_ids, f"Indicator {ind['indicator_code']} references unknown source: {ps}"

    def test_indicator_categories_valid(self):
        valid_categories = {"MACRO", "INTEREST_RATE", "FX", "OIL_ENERGY", "CBK",
                            "BANKING", "INSURANCE", "LOGISTICS", "COMPOSITE"}
        with open(SEED_DIR / "indicator_catalog.json") as f:
            data = json.load(f)
        for r in data:
            assert r["category"] in valid_categories, f"{r['indicator_code']} has invalid category: {r['category']}"

    def test_gcc_country_coverage(self):
        """Source registry should cover at least KW, SA, AE."""
        with open(SEED_DIR / "source_truth_registry.json") as f:
            data = json.load(f)
        all_countries = set()
        for s in data:
            if s.get("coverage_countries"):
                all_countries.update(s["coverage_countries"])
        assert "KW" in all_countries
        assert "SA" in all_countries
        assert "AE" in all_countries

    def test_indicator_country_spread(self):
        """Indicator catalog should cover KW, SA, AE."""
        with open(SEED_DIR / "indicator_catalog.json") as f:
            data = json.load(f)
        countries = {r.get("country_scope") for r in data if r.get("country_scope")}
        assert "KW" in countries
        assert "SA" in countries
        assert "AE" in countries

    def test_arabic_names_present(self):
        """Both seed files should have Arabic names."""
        with open(SEED_DIR / "source_truth_registry.json") as f:
            sources = json.load(f)
        assert all(s.get("source_name_ar") for s in sources)

        with open(SEED_DIR / "indicator_catalog.json") as f:
            indicators = json.load(f)
        assert all(i.get("indicator_name_ar") for i in indicators)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Repository Structure Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRepositoryStructure:
    """Verify repositories are correctly configured."""

    def test_source_truth_repo(self):
        from src.data_foundation.repositories.source_truth_repo import SourceTruthRepository
        assert SourceTruthRepository.pk_field == "source_id"
        assert hasattr(SourceTruthRepository, "find_active")
        assert hasattr(SourceTruthRepository, "find_by_reliability")
        assert hasattr(SourceTruthRepository, "find_failing")

    def test_raw_record_repo(self):
        from src.data_foundation.repositories.raw_record_repo import RawSourceRecordRepository
        assert RawSourceRecordRepository.pk_field == "record_id"
        assert hasattr(RawSourceRecordRepository, "find_by_content_hash")
        assert hasattr(RawSourceRecordRepository, "find_pending_normalization")

    def test_indicator_catalog_repo(self):
        from src.data_foundation.repositories.indicator_catalog_repo import IndicatorCatalogRepository
        assert IndicatorCatalogRepository.pk_field == "indicator_id"
        assert hasattr(IndicatorCatalogRepository, "find_by_code")
        assert hasattr(IndicatorCatalogRepository, "find_by_category")
        assert hasattr(IndicatorCatalogRepository, "find_with_alerts")

    def test_observation_repo(self):
        from src.data_foundation.repositories.observation_repo import CanonicalObservationRepository
        assert CanonicalObservationRepository.pk_field == "observation_id"
        assert hasattr(CanonicalObservationRepository, "find_by_indicator")
        assert hasattr(CanonicalObservationRepository, "find_latest_by_indicator")
        assert hasattr(CanonicalObservationRepository, "find_provisional")

    def test_fetch_run_repo(self):
        from src.data_foundation.repositories.fetch_run_repo import SourceFetchRunRepository
        assert SourceFetchRunRepository.pk_field == "run_id"
        assert hasattr(SourceFetchRunRepository, "find_latest_by_source")
        assert hasattr(SourceFetchRunRepository, "find_failed")
        assert hasattr(SourceFetchRunRepository, "find_running")

    def test_normalization_run_repo(self):
        from src.data_foundation.repositories.normalization_run_repo import NormalizationRunRepository
        assert NormalizationRunRepository.pk_field == "run_id"
        assert hasattr(NormalizationRunRepository, "find_by_fetch_run")
        assert hasattr(NormalizationRunRepository, "find_pending")

    def test_repos_in_package_init(self):
        from src.data_foundation.repositories import (
            SourceTruthRepository,
            RawSourceRecordRepository,
            IndicatorCatalogRepository,
            CanonicalObservationRepository,
            SourceFetchRunRepository,
            NormalizationRunRepository,
        )
        assert all([
            SourceTruthRepository,
            RawSourceRecordRepository,
            IndicatorCatalogRepository,
            CanonicalObservationRepository,
            SourceFetchRunRepository,
            NormalizationRunRepository,
        ])


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Migration Structure Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMigrationStructure:
    """Verify migration file is well-formed."""

    def test_migration_file_exists(self):
        path = Path(__file__).parent.parent / "alembic" / "versions" / "002_data_reality_foundation_tables.py"
        assert path.exists()

    def test_migration_revision_chain(self):
        path = Path(__file__).parent.parent / "alembic" / "versions" / "002_data_reality_foundation_tables.py"
        content = path.read_text()
        assert 'revision: str = "002_data_reality"' in content
        assert 'down_revision' in content
        assert '"001_p2_foundation"' in content

    def test_migration_creates_all_tables(self):
        path = Path(__file__).parent.parent / "alembic" / "versions" / "002_data_reality_foundation_tables.py"
        content = path.read_text()
        tables = [
            "df_source_truth_registry",
            "df_raw_source_records",
            "df_indicator_catalog",
            "df_canonical_observations",
            "df_source_fetch_runs",
            "df_normalization_runs",
        ]
        for t in tables:
            assert f'"{t}"' in content, f"Migration missing table: {t}"

    def test_migration_has_downgrade(self):
        path = Path(__file__).parent.parent / "alembic" / "versions" / "002_data_reality_foundation_tables.py"
        content = path.read_text()
        assert "def downgrade" in content
        assert "drop_table" in content
