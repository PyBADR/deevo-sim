"""
Impact Observatory | مرصد الأثر — Scenario Module
Templates, catalog, and engine for scenario management.
"""

from app.scenarios.templates import (
    ScenarioTemplate,
    DisruptionType,
    ScenarioDomain,
    SCENARIO_TEMPLATES,
    get_template,
    list_templates,
    get_templates_by_disruption_type,
    get_templates_by_domain,
)

from app.scenarios.catalog import (
    SCENARIO_CATALOG,
    get_scenario_catalog,
    get_scenario_by_id,
    get_catalog_ids,
    get_scenarios_by_sector,
    CATALOG_TO_DOMAIN_FIELD_MAP,
)

__all__ = [
    # Templates
    "ScenarioTemplate",
    "DisruptionType",
    "ScenarioDomain",
    "SCENARIO_TEMPLATES",
    "get_template",
    "list_templates",
    "get_templates_by_disruption_type",
    "get_templates_by_domain",
    # Catalog
    "SCENARIO_CATALOG",
    "get_scenario_catalog",
    "get_scenario_by_id",
    "get_catalog_ids",
    "get_scenarios_by_sector",
    "CATALOG_TO_DOMAIN_FIELD_MAP",
]
