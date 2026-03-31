"""
Shockwave propagation modeling.

Physics metaphor: A shock event (disruption, conflict, natural disaster)
propagates outward at a certain speed. Intensity decays with distance and
time using a wavefront model. Points further from the origin and reached
later experience reduced shock intensity.

GCC Physics Model:
Temporal shockwave dynamics follow the exact formula:
    R(t+1) = alpha*A*R(t) + beta*S(t) + delta*E

where:
    alpha = 0.58 (recursive decay factor - memory of prior shocks)
    beta = 0.92 (shockwave amplitude damping - energy dissipation)
    A = amplitude coefficient
    R(t) = shock intensity at time t
    S(t) = source shock magnitude
    delta = 0.47 (energy coupling - external disruptions drive response)
    E = external energy source

This implementation uses GCC defaults for all parameters.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
from .gcc_physics_config import (
    SHOCKWAVE_PROPAGATION_SPEED_KMH,
    SHOCKWAVE_SPATIAL_DECAY_LAMBDA,
    SHOCKWAVE_MAGNITUDE_SCALE,
    SHOCKWAVE_AMPLITUDE_DAMPING,
    SHOCKWAVE_DECAY_FACTOR,
    SHOCKWAVE_ENERGY_COUPLING,
)


@dataclass
class ShockEvent:
    """
    A shock event with spatiotemporal propagation.
    
    Attributes:
        origin_lat: Shock origin latitude
        origin_lon: Shock origin longitude
        magnitude: Initial shock intensity [0, 1]
        propagation_speed_kmh: Speed at which shockwave expands
        start_time: When the shock event begins
    """
    origin_lat: float
    origin_lon: float
    magnitude: float
    propagation_speed_kmh: float = None
    start_time: datetime = None

    def __post_init__(self):
        """Validate parameters and apply GCC defaults."""
        if not (0 <= self.magnitude <= 1):
            raise ValueError(f"magnitude must be in [0, 1], got {self.magnitude}")
        
        if self.propagation_speed_kmh is None:
            self.propagation_speed_kmh = SHOCKWAVE_PROPAGATION_SPEED_KMH
        
        if self.propagation_speed_kmh <= 0:
            raise ValueError(f"propagation_speed_kmh must be positive, got {self.propagation_speed_kmh}")
        
        if self.start_time is None:
            self.start_time = datetime.now()


class ShockwaveEngine:
    """
    Collection of shocks modeling spatiotemporal disruption propagation.
    
    Computational model: A shockwave expands as a circular wavefront from the
    origin. Intensity follows:
        intensity = magnitude * exp(-lambda * distance) * H(distance - speed * dt)
    where:
        - lambda: decay rate (inverse of characteristic length scale) = GCC 0.05
        - H(x): Heaviside step function (0 if x < 0, else 1) - ensures causality
        - distance: Euclidean distance from origin
        - dt: time elapsed since start
        
    Temporal dynamics follow GCC formula:
        R(t+1) = alpha*A*R(t) + beta*S(t) + delta*E
    where alpha=0.58, A=amplitude, beta=0.92, delta=0.47
    """

    def __init__(
        self,
        decay_lambda: float = None,
        amplitude_damping: float = None,
        decay_factor: float = None,
        energy_coupling: float = None
    ):
        """
        Initialize shockwave engine with GCC defaults.
        
        Args:
            decay_lambda: Spatial decay rate [default: GCC 0.05 = 20 km characteristic length]
            amplitude_damping: Amplitude damping (beta) [default: GCC 0.92]
            decay_factor: Recursive decay (alpha) [default: GCC 0.58]
            energy_coupling: Energy coupling (delta) [default: GCC 0.47]
        """
        self.shocks: List[ShockEvent] = []
        self.decay_lambda = decay_lambda if decay_lambda is not None else SHOCKWAVE_SPATIAL_DECAY_LAMBDA
        self.amplitude_damping = amplitude_damping if amplitude_damping is not None else SHOCKWAVE_AMPLITUDE_DAMPING
        self.decay_factor = decay_factor if decay_factor is not None else SHOCKWAVE_DECAY_FACTOR
        self.energy_coupling = energy_coupling if energy_coupling is not None else SHOCKWAVE_ENERGY_COUPLING

    def add_shock(self, shock: ShockEvent) -> None:
        """
        Register a shock event.
        
        Args:
            shock: ShockEvent instance
        """
        self.shocks.append(shock)

    def evaluate_at(
        self,
        lat: float,
        lon: float,
        time: datetime,
        external_energy: float = 0.0
    ) -> float:
        """
        Evaluate shock intensity at a point and time using GCC formula.
        
        Sums contributions from all registered shocks. Each shock contributes
        only after its wavefront reaches the point (Heaviside step function).
        
        Temporal dynamics:
            R(t+1) = alpha*A*R(t) + beta*S(t) + delta*E
        where:
            - alpha = 0.58 (decay_factor)
            - A = amplitude coefficient (from spatial evaluation)
            - R(t) = previous intensity
            - beta = 0.92 (amplitude_damping)
            - S(t) = source magnitude
            - delta = 0.47 (energy_coupling)
            - E = external energy source
        
        Args:
            lat: Query latitude
            lon: Query longitude
            time: Query time
            external_energy: External energy contribution [0, 1]
            
        Returns:
            Total shock intensity [0, 1], clamped
        """
        if not self.shocks:
            return 0.0

        total_intensity = 0.0

        for shock in self.shocks:
            # Time elapsed since shock started
            time_delta = time - shock.start_time
            
            if time_delta.total_seconds() < 0:
                # Shock hasn't started yet
                continue

            dt_hours = time_delta.total_seconds() / 3600.0

            # Distance from shock origin (in km)
            dx_km = (lat - shock.origin_lat) * 111.0
            dy_km = (lon - shock.origin_lon) * 111.0 * np.cos(np.radians(lat))
            distance_km = np.sqrt(dx_km * dx_km + dy_km * dy_km)

            # Wavefront distance at current time
            wavefront_distance_km = shock.propagation_speed_kmh * dt_hours

            # Heaviside step: shock intensity is zero until wavefront arrives
            if distance_km > wavefront_distance_km:
                continue

            # Spatial intensity: magnitude * exp(-lambda * distance)
            # This gives amplitude coefficient A for temporal formula
            amplitude = SHOCKWAVE_MAGNITUDE_SCALE * np.exp(-self.decay_lambda * distance_km)

            # Temporal dynamics: R(t+1) = alpha*A*R(t) + beta*S(t) + delta*E
            # Simplified for single evaluation: direct amplitude contribution
            # with damping and energy coupling
            intensity = (
                self.amplitude_damping * amplitude * shock.magnitude
                + self.energy_coupling * external_energy
            )
            
            total_intensity += intensity

        return float(np.clip(total_intensity, 0.0, 1.0))

    def propagate(
        self,
        targets: List[Tuple[float, float, str]],
        time: datetime,
        external_energy: float = 0.0
    ) -> Dict[str, float]:
        """
        Evaluate shock impact on multiple targets using GCC dynamics.
        
        Args:
            targets: List of (lat, lon, target_id) tuples
            time: Evaluation time
            external_energy: External energy driving shock response
            
        Returns:
            Dictionary mapping target_id -> shock intensity at that target
        """
        impacts = {}
        for lat, lon, target_id in targets:
            impacts[target_id] = self.evaluate_at(lat, lon, time, external_energy)

        return impacts

    def compute_recursive_shockwave(
        self,
        previous_intensity: float,
        source_magnitude: float,
        external_energy: float = 0.0,
        amplitude_coefficient: float = 1.0
    ) -> float:
        """
        Compute next shockwave state using exact GCC temporal formula.
        
        Formula: R(t+1) = alpha*A*R(t) + beta*S(t) + delta*E
        
        Args:
            previous_intensity: R(t) - shock intensity at previous time
            source_magnitude: S(t) - magnitude of source shock
            external_energy: E - external energy driving response
            amplitude_coefficient: A - amplitude coefficient from spatial evaluation
            
        Returns:
            Next shockwave intensity R(t+1), clamped to [0, 1]
        """
        # Validate inputs
        if not (0 <= previous_intensity <= 1):
            raise ValueError(f"previous_intensity must be in [0, 1], got {previous_intensity}")
        if not (0 <= source_magnitude <= 1):
            raise ValueError(f"source_magnitude must be in [0, 1], got {source_magnitude}")
        if not (0 <= external_energy <= 1):
            raise ValueError(f"external_energy must be in [0, 1], got {external_energy}")
        if amplitude_coefficient < 0:
            raise ValueError(f"amplitude_coefficient must be non-negative, got {amplitude_coefficient}")
        
        # Apply exact GCC formula
        next_intensity = (
            self.decay_factor * amplitude_coefficient * previous_intensity
            + self.amplitude_damping * source_magnitude
            + self.energy_coupling * external_energy
        )
        
        return float(np.clip(next_intensity, 0.0, 1.0))
