"""
Impact Observatory | مرصد الأثر — V1 Hormuz Strait Closure Seed Data

Flagship V1 scenario: 14-day severe disruption of Hormuz Strait shipping corridor.
Shock intensity 4.25 (0-5 scale).

Entities: 12 representative GCC financial system nodes
Edges: 15 inter-entity transmission paths
"""

from ..domain.models.scenario import (
    Scenario, RegulatoryProfile, ScenarioTimeConfig,
    ScenarioDna, TriggerEvent, SectorImpactLink,
)
from ..domain.models.entity import Entity
from ..domain.models.edge import Edge


def build_hormuz_v1_scenario() -> Scenario:
    """Build the V1 Hormuz Closure scenario with full entity/edge graph."""

    entities = [
        # Banking sector (4 entities)
        Entity(
            entity_id="bank-gcc-001", entity_type="bank",
            name="GCC Tier-1 Banks (Aggregate)", jurisdiction="GCC",
            exposure=1800, capital_buffer=315, liquidity_buffer=243,
            capacity=1.0, availability=0.995, route_efficiency=0.98,
            criticality=0.95, regulatory_classification="systemic", active=True,
        ),
        Entity(
            entity_id="bank-gcc-002", entity_type="bank",
            name="GCC Tier-2 Banks (Aggregate)", jurisdiction="GCC",
            exposure=700, capital_buffer=122.5, liquidity_buffer=94.5,
            capacity=1.0, availability=0.99, route_efficiency=0.95,
            criticality=0.80, regulatory_classification="material", active=True,
        ),
        Entity(
            entity_id="bank-gcc-003", entity_type="bank",
            name="GCC Islamic Banks", jurisdiction="GCC",
            exposure=300, capital_buffer=60, liquidity_buffer=45,
            capacity=1.0, availability=0.99, route_efficiency=0.93,
            criticality=0.65, regulatory_classification="material", active=True,
        ),
        Entity(
            entity_id="bank-gcc-004", entity_type="bank",
            name="Central Bank Reserves", jurisdiction="GCC",
            exposure=780, capital_buffer=780, liquidity_buffer=780,
            capacity=1.0, availability=1.0, route_efficiency=1.0,
            criticality=0.99, regulatory_classification="systemic", active=True,
        ),

        # Insurance sector (3 entities)
        Entity(
            entity_id="ins-gcc-001", entity_type="insurer",
            name="GCC Primary Insurers", jurisdiction="GCC",
            exposure=280, capital_buffer=112, liquidity_buffer=56,
            capacity=1.0, availability=0.99, route_efficiency=0.95,
            criticality=0.75, regulatory_classification="material", active=True,
        ),
        Entity(
            entity_id="ins-gcc-002", entity_type="insurer",
            name="GCC Reinsurers", jurisdiction="GCC",
            exposure=120, capital_buffer=60, liquidity_buffer=30,
            capacity=1.0, availability=0.995, route_efficiency=0.97,
            criticality=0.70, regulatory_classification="material", active=True,
        ),
        Entity(
            entity_id="ins-gcc-003", entity_type="insurer",
            name="GCC Takaful Operators", jurisdiction="GCC",
            exposure=50, capital_buffer=20, liquidity_buffer=10,
            capacity=1.0, availability=0.98, route_efficiency=0.90,
            criticality=0.50, regulatory_classification="standard", active=True,
        ),

        # Fintech sector (3 entities)
        Entity(
            entity_id="fin-gcc-001", entity_type="fintech",
            name="GCC Payment Gateways", jurisdiction="GCC",
            exposure=90, capital_buffer=22.5, liquidity_buffer=13.5,
            capacity=1.0, availability=0.999, route_efficiency=0.98,
            criticality=0.85, regulatory_classification="systemic", active=True,
        ),
        Entity(
            entity_id="fin-gcc-002", entity_type="fintech",
            name="GCC Digital Banks", jurisdiction="GCC",
            exposure=60, capital_buffer=15, liquidity_buffer=9,
            capacity=1.0, availability=0.995, route_efficiency=0.95,
            criticality=0.65, regulatory_classification="material", active=True,
        ),
        Entity(
            entity_id="fin-gcc-003", entity_type="fintech",
            name="GCC Settlement Infrastructure", jurisdiction="GCC",
            exposure=30, capital_buffer=7.5, liquidity_buffer=4.5,
            capacity=1.0, availability=0.9999, route_efficiency=0.99,
            criticality=0.90, regulatory_classification="systemic", active=True,
        ),

        # Market infrastructure (2 entities)
        Entity(
            entity_id="mkt-gcc-001", entity_type="market_infrastructure",
            name="GCC Stock Exchanges", jurisdiction="GCC",
            exposure=420, capital_buffer=84, liquidity_buffer=63,
            capacity=1.0, availability=0.999, route_efficiency=0.99,
            criticality=0.80, regulatory_classification="systemic", active=True,
        ),
        Entity(
            entity_id="mkt-gcc-002", entity_type="market_infrastructure",
            name="GCC Commodity Markets", jurisdiction="GCC",
            exposure=540, capital_buffer=108, liquidity_buffer=81,
            capacity=1.0, availability=0.995, route_efficiency=0.97,
            criticality=0.85, regulatory_classification="systemic", active=True,
        ),
    ]

    edges = [
        Edge(edge_id="e-001", source_entity_id="mkt-gcc-002", target_entity_id="bank-gcc-001",
             relation_type="funding", exposure=450, transmission_coefficient=0.75,
             capacity=1.0, availability=0.99, route_efficiency=0.95, latency_ms=100, active=True),
        Edge(edge_id="e-002", source_entity_id="mkt-gcc-002", target_entity_id="bank-gcc-002",
             relation_type="funding", exposure=200, transmission_coefficient=0.65,
             capacity=1.0, availability=0.99, route_efficiency=0.93, latency_ms=150, active=True),
        Edge(edge_id="e-003", source_entity_id="bank-gcc-001", target_entity_id="ins-gcc-001",
             relation_type="insurance", exposure=120, transmission_coefficient=0.55,
             capacity=1.0, availability=0.99, route_efficiency=0.95, latency_ms=200, active=True),
        Edge(edge_id="e-004", source_entity_id="bank-gcc-001", target_entity_id="ins-gcc-002",
             relation_type="insurance", exposure=80, transmission_coefficient=0.60,
             capacity=1.0, availability=0.99, route_efficiency=0.97, latency_ms=180, active=True),
        Edge(edge_id="e-005", source_entity_id="ins-gcc-001", target_entity_id="ins-gcc-002",
             relation_type="insurance", exposure=150, transmission_coefficient=0.70,
             capacity=1.0, availability=0.995, route_efficiency=0.97, latency_ms=120, active=True),
        Edge(edge_id="e-006", source_entity_id="bank-gcc-001", target_entity_id="fin-gcc-001",
             relation_type="payment", exposure=90, transmission_coefficient=0.80,
             capacity=1.0, availability=0.999, route_efficiency=0.98, latency_ms=50, active=True),
        Edge(edge_id="e-007", source_entity_id="bank-gcc-002", target_entity_id="fin-gcc-002",
             relation_type="payment", exposure=60, transmission_coefficient=0.70,
             capacity=1.0, availability=0.995, route_efficiency=0.95, latency_ms=80, active=True),
        Edge(edge_id="e-008", source_entity_id="fin-gcc-001", target_entity_id="fin-gcc-003",
             relation_type="technology", exposure=30, transmission_coefficient=0.85,
             capacity=1.0, availability=0.9999, route_efficiency=0.99, latency_ms=20, active=True),
        Edge(edge_id="e-009", source_entity_id="bank-gcc-001", target_entity_id="bank-gcc-004",
             relation_type="funding", exposure=300, transmission_coefficient=0.50,
             capacity=1.0, availability=1.0, route_efficiency=1.0, latency_ms=10, active=True),
        Edge(edge_id="e-010", source_entity_id="mkt-gcc-001", target_entity_id="bank-gcc-001",
             relation_type="market", exposure=200, transmission_coefficient=0.60,
             capacity=1.0, availability=0.999, route_efficiency=0.99, latency_ms=30, active=True),
        Edge(edge_id="e-011", source_entity_id="mkt-gcc-002", target_entity_id="ins-gcc-001",
             relation_type="insurance", exposure=100, transmission_coefficient=0.65,
             capacity=1.0, availability=0.99, route_efficiency=0.95, latency_ms=250, active=True),
        Edge(edge_id="e-012", source_entity_id="fin-gcc-001", target_entity_id="mkt-gcc-001",
             relation_type="technology", exposure=50, transmission_coefficient=0.40,
             capacity=1.0, availability=0.999, route_efficiency=0.98, latency_ms=40, active=True),
        Edge(edge_id="e-013", source_entity_id="bank-gcc-003", target_entity_id="ins-gcc-003",
             relation_type="insurance", exposure=30, transmission_coefficient=0.50,
             capacity=1.0, availability=0.98, route_efficiency=0.90, latency_ms=300, active=True),
        Edge(edge_id="e-014", source_entity_id="fin-gcc-002", target_entity_id="fin-gcc-001",
             relation_type="payment", exposure=40, transmission_coefficient=0.75,
             capacity=1.0, availability=0.995, route_efficiency=0.95, latency_ms=60, active=True),
        Edge(edge_id="e-015", source_entity_id="bank-gcc-004", target_entity_id="mkt-gcc-001",
             relation_type="market", exposure=150, transmission_coefficient=0.35,
             capacity=1.0, availability=1.0, route_efficiency=1.0, latency_ms=5, active=True),
    ]

    # v4 §18.1 Scenario DNA
    scenario_dna = ScenarioDna(
        scenario_type="compound_systemic_event",
        trigger_event=TriggerEvent(
            event_type="compound_event",
            event_name="Hormuz Strait Complete Closure",
            event_time="2026-04-02T00:00:00Z",
            origin_scope_level="system",
            origin_scope_ref="mkt-gcc-002",
            initial_shock_intensity=4.25,
        ),
        sector_impact_chain=[
            SectorImpactLink(step=1, source_sector="market_infrastructure", target_sector="bank",
                             impact_channel="liquidity", transmission_strength=0.75, expected_lag_steps=1),
            SectorImpactLink(step=2, source_sector="bank", target_sector="insurer",
                             impact_channel="claims", transmission_strength=0.55, expected_lag_steps=2),
            SectorImpactLink(step=3, source_sector="bank", target_sector="fintech",
                             impact_channel="payment", transmission_strength=0.80, expected_lag_steps=1),
            SectorImpactLink(step=4, source_sector="insurer", target_sector="bank",
                             impact_channel="capital", transmission_strength=0.30, expected_lag_steps=3),
        ],
        primary_sector="cross_sector",
        secondary_sectors=["bank", "insurer", "fintech"],
        transmission_mode="mixed",
        severity_band="extreme",
    )

    # v4 §17.2 Time config
    time_config = ScenarioTimeConfig(
        time_granularity_minutes=1440,  # daily
        time_horizon_steps=14,          # 14 days
        shock_decay_rate=0.05,
        propagation_delay_steps=1,
        recovery_rate=0.02,
        max_temporal_iterations_per_step=10,
    )

    # v4 Regulatory profile
    regulatory_profile = RegulatoryProfile(
        jurisdiction="GCC",
        regulatory_version="2.4.0",
        lcr_min=1.0,
        nsfr_min=1.0,
        cet1_min=0.045,
        capital_adequacy_min=0.08,
        insurance_solvency_min=1.0,
        insurance_reserve_min=1.0,
        fintech_availability_min=0.995,
        settlement_delay_max_minutes=30,
    )

    return Scenario(
        scenario_id="hormuz-closure-v1",
        scenario_version="1.0.0",
        name="Hormuz Strait Closure",
        description="14-day severe disruption of Hormuz Strait shipping corridor. "
                    "Complete blockage of maritime traffic affecting 30% of global oil transit, "
                    "GCC trade finance, marine insurance, and payment settlement infrastructure.",
        as_of_date="2026-04-02",
        horizon_days=14,
        currency="USD",
        shock_intensity=4.25,
        market_liquidity_haircut=0.35,
        deposit_run_rate=0.08,
        claims_spike_rate=0.85,  # v4: 0-1 scale (not absolute multiplier)
        fraud_loss_rate=0.02,
        regulatory_profile=regulatory_profile,
        entities=entities,
        edges=edges,
        created_by="system",
        created_at="2026-04-02T00:00:00Z",
        status="active",
        scenario_dna=scenario_dna,
        time_config=time_config,
    )
