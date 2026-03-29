"""
Demo API Routes — Pilot-ready scenario demonstration endpoints.
Wires the trust closure pipeline into HTTP for the demo experience.

Import strategy: uses try/except to support both Docker (from app.*)
and local dev (from backend.app.*) environments.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

demo_router = APIRouter(prefix="/demo", tags=["demo"])


# ── Portable import helper ──
def _import(module_path: str):
    """Import from app.* (Docker) or backend.app.* (local dev)."""
    import importlib
    try:
        return importlib.import_module(module_path)
    except ImportError:
        return importlib.import_module(f"backend.{module_path}")


class ScenarioRequest(BaseModel):
    scenarioType: str = Field(..., description="e.g. hormuz_closure, banking_shock")
    severity: float = Field(0.8, ge=0.0, le=1.0)
    archetypeId: str = Field("sovereign_treasury")
    durationHours: int = Field(72, ge=1, le=8760)


class ScenarioResponse(BaseModel):
    scenarioType: str
    archetypeId: str
    totalLoss: float
    costCredibility: str
    calibrationScore: float
    calibrationSupport: str
    deploymentSuitability: str
    overallTrustLevel: str
    lossBySector: dict
    drivers: list[str]
    narrative: str


@demo_router.post("/run-scenario", response_model=ScenarioResponse)
def run_demo_scenario(req: ScenarioRequest):
    """Run a full trust-closure pipeline scenario for demo purposes."""
    provenance = _import("app.data.reference_provenance_v1")
    loader = _import("app.data.reference_loader_v1")
    cal_mod = _import("app.calibration.systemic_calibration_v1")
    anchor_mod = _import("app.calibration.scenario_anchor_registry_v1")
    val_mod = _import("app.calibration.calibration_validation_v1")
    realism = _import("app.finance.portfolio_realism_v3")
    executive = _import("app.executive.executive_output_v1")

    # Reset and load references
    provenance.clear_references()
    loader.load_all_file_references()

    # Get anchor for scenario type
    anchor = None
    for a in anchor_mod.SCENARIO_ANCHORS.values():
        if a.scenarioType == req.scenarioType:
            anchor = a
            break

    base_impact = anchor.estimatedImpactUSD if anchor else 5_000_000_000
    scaled_impact = base_impact * req.severity

    # Build sector losses from anchor
    primary_sectors = anchor.primarySectors if anchor else ["energy", "logistics", "finance"]
    secondary_sectors = anchor.secondarySectors if anchor else ["aviation", "water", "food"]

    sector_losses = {}
    for s in primary_sectors:
        sector_losses[s] = scaled_impact * 0.25
    for s in secondary_sectors:
        sector_losses[s] = scaled_impact * 0.08

    # Compute archetype loss
    archetype_result = realism.compute_archetype_loss(req.archetypeId, sector_losses, {})

    # Calibration validation
    cal_result = val_mod.validate_calibration_pack(
        "gcc_full", cal_mod.GCC_CALIBRATION_PROFILES, {}, anchor_mod.SCENARIO_ANCHORS
    )

    # Cost credibility
    cred = loader.get_cost_credibility_level()

    # Executive trust brief
    brief = executive.generate_executive_trust_brief(
        sector_losses=sector_losses,
        contagion_multiplier=1.8,
        duration_hours=req.durationHours,
        archetype_label=req.archetypeId,
        archetype_entity_type=archetype_result.credibilityNote,
        validation_score=cal_result.validationScore,
        unsupported_fields=cal_result.unsupportedFields,
        anchor_coverage=cal_result.anchorCoverage,
    )

    return ScenarioResponse(
        scenarioType=req.scenarioType,
        archetypeId=req.archetypeId,
        totalLoss=archetype_result.totalLoss,
        costCredibility=cred["level"],
        calibrationScore=round(cal_result.validationScore, 3),
        calibrationSupport=brief.calibrationConfidence.supportLevel,
        deploymentSuitability=brief.deploymentSuitability,
        overallTrustLevel=brief.overallTrustLevel,
        lossBySector={s: round(v) for s, v in archetype_result.lossBySector.items()},
        drivers=archetype_result.drivers,
        narrative=brief.costCredibility.narrative,
    )


@demo_router.get("/archetypes")
def list_archetypes():
    """List all available portfolio archetypes."""
    mod = _import("app.finance.portfolio_archetypes_v1")
    return {
        "archetypes": [
            {"id": a.id, "label": a.label, "entityType": a.entityType}
            for a in mod.PORTFOLIO_ARCHETYPES.values()
        ]
    }


@demo_router.get("/scenarios")
def list_scenarios():
    """List all available scenario anchors."""
    mod = _import("app.calibration.scenario_anchor_registry_v1")
    return {
        "scenarios": [
            {
                "id": a.id,
                "label": a.label,
                "scenarioType": a.scenarioType,
                "estimatedImpactUSD": a.estimatedImpactUSD,
                "primarySectors": a.primarySectors,
            }
            for a in mod.SCENARIO_ANCHORS.values()
        ]
    }


@demo_router.get("/trust-status")
def get_trust_status():
    """Get current system trust status."""
    provenance = _import("app.data.reference_provenance_v1")
    loader = _import("app.data.reference_loader_v1")
    cal_mod = _import("app.calibration.systemic_calibration_v1")
    anchor_mod = _import("app.calibration.scenario_anchor_registry_v1")
    val_mod = _import("app.calibration.calibration_validation_v1")

    provenance.clear_references()
    loader.load_all_file_references()
    cred = loader.get_cost_credibility_level()
    cal = val_mod.validate_calibration_pack(
        "gcc_full", cal_mod.GCC_CALIBRATION_PROFILES, {}, anchor_mod.SCENARIO_ANCHORS
    )

    return {
        "costCredibility": cred["level"],
        "calibrationScore": round(cal.validationScore, 3),
        "supportedFields": len(cal.supportedFields),
        "weakFields": len(cal.weakFields),
        "unsupportedFields": len(cal.unsupportedFields),
        "fileReferences": cred["file_count"],
        "totalReferences": cred["total"],
    }
