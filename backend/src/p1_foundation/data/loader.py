"""P1 Data Foundation — Seed Data Loader.

Loads seed JSON files and validates them against their Pydantic models.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Type

from p1_foundation.models.base import P1BaseModel
from p1_foundation.models.dataset_registry import DatasetRegistryEntry
from p1_foundation.models.decision_logs import DecisionLogRecord
from p1_foundation.models.decision_rules import DecisionRuleRecord
from p1_foundation.models.entity_registry import EntityRegistryEntry
from p1_foundation.models.events import EventSignalRecord
from p1_foundation.models.logistics import LogisticsNodeProfile
from p1_foundation.models.macro_indicators import MacroIndicatorRecord
from p1_foundation.models.sector_profiles import BankingSectorProfile, InsuranceSectorProfile
from p1_foundation.models.signals import (
    FXSignalRecord,
    InterestRateSignalRecord,
    KuwaitCBKIndicatorRecord,
    OilEnergySignalRecord,
)
from p1_foundation.models.source_registry import SourceRegistryEntry

SEEDS_DIR = Path(__file__).parent / "seeds"

SEED_FILE_MAP: dict[str, tuple[str, Type[P1BaseModel]]] = {
    "dataset_registry": ("dataset_registry.json", DatasetRegistryEntry),
    "source_registry": ("source_registry.json", SourceRegistryEntry),
    "entity_registry": ("entity_registry.json", EntityRegistryEntry),
    "macro_indicators": ("macro_indicators.json", MacroIndicatorRecord),
    "interest_rate_signals": ("interest_rate_signals.json", InterestRateSignalRecord),
    "oil_energy_signals": ("oil_energy_signals.json", OilEnergySignalRecord),
    "fx_signals": ("fx_signals.json", FXSignalRecord),
    "cbk_indicators": ("cbk_indicators.json", KuwaitCBKIndicatorRecord),
    "event_signals": ("event_signals.json", EventSignalRecord),
    "banking_profiles": ("banking_profiles.json", BankingSectorProfile),
    "insurance_profiles": ("insurance_profiles.json", InsuranceSectorProfile),
    "logistics_nodes": ("logistics_nodes.json", LogisticsNodeProfile),
    "decision_rules": ("decision_rules.json", DecisionRuleRecord),
    "decision_logs": ("decision_logs.json", DecisionLogRecord),
}


def load_seed(dataset_name: str) -> list[dict]:
    """Load raw JSON data for a dataset."""
    if dataset_name not in SEED_FILE_MAP:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    filename, _ = SEED_FILE_MAP[dataset_name]
    path = SEEDS_DIR / filename
    with open(path) as f:
        return json.load(f)


def load_and_validate(dataset_name: str) -> list[P1BaseModel]:
    """Load seed data and validate each record against its model."""
    if dataset_name not in SEED_FILE_MAP:
        raise ValueError(f"Unknown dataset: {dataset_name}")
    filename, model_class = SEED_FILE_MAP[dataset_name]
    raw = load_seed(dataset_name)
    return [model_class.model_validate(record) for record in raw]


def load_all_seeds() -> dict[str, list[dict]]:
    """Load all seed datasets as raw dicts."""
    return {name: load_seed(name) for name in SEED_FILE_MAP}


def get_all_entity_ids() -> set[str]:
    """Get all entity IDs from the entity registry seed."""
    records = load_seed("entity_registry")
    return {r["id"] for r in records}


def get_all_dataset_ids() -> set[str]:
    """Get all dataset IDs from the dataset registry seed."""
    records = load_seed("dataset_registry")
    return {r["id"] for r in records}
