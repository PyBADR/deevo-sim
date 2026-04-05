"""
Simulation Layer — backend/app/simulation/

Unified 13-stage pipeline runner.
DEPRECATED: Mesa ABM module (mesa_model, behaviors, bridge) removed in v2.0.
"""

from .runner import run_unified_pipeline
from .state import SimulationState

__all__ = ["run_unified_pipeline", "SimulationState"]
