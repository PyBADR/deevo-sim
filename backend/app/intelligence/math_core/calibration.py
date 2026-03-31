"""
Calibration framework for GCC risk assessment models.

Supports four-phase calibration:
Phase 1: Expert initialization of weights
Phase 2: Backtesting with historical data
Phase 3: Regional calibration with geographic adjustments
Phase 4: Insurance calibration with premium adjustments
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import numpy as np

from .gcc_weights import (
    AIRPORT_WEIGHTS,
    SEAPORT_WEIGHTS,
    ROAD_HUB_WEIGHTS,
    RAIL_HUB_WEIGHTS,
    WAREHOUSE_WEIGHTS,
    PIPELINE_WEIGHTS,
)


@dataclass
class CalibrationMetrics:
    """Metrics from a single calibration event."""
    
    predicted_risk: float  # Model-predicted risk score [0, 1]
    actual_risk: float  # Observed/realized risk [0, 1]
    event_type: str  # Type of event for stratification
    asset_class: str  # Asset class (AIRPORT, SEAPORT, etc.)
    timestamp: float  # Unix timestamp of event
    region: str  # Geographic region for regional calibration
    insurance_cost: Optional[float] = None  # Actual insurance cost if available


@dataclass
class CalibrationResults:
    """Results from calibration phase."""
    
    phase: int  # Calibration phase (1-4)
    mae: float  # Mean absolute error
    rmse: float  # Root mean squared error
    correlation: float  # Pearson correlation
    bias: float  # Mean prediction error (predicted - actual)
    updated_weights: Dict[str, float] = field(default_factory=dict)
    regional_adjustments: Dict[str, float] = field(default_factory=dict)
    insurance_adjustments: Dict[str, float] = field(default_factory=dict)


class CalibrationEngine:
    """Manages four-phase calibration for GCC risk models."""
    
    def __init__(self):
        """Initialize calibration engine with default weights."""
        self.asset_class_weights = {
            "AIRPORT": AIRPORT_WEIGHTS.copy(),
            "SEAPORT": SEAPORT_WEIGHTS.copy(),
            "ROAD_HUB": ROAD_HUB_WEIGHTS.copy(),
            "RAIL_HUB": RAIL_HUB_WEIGHTS.copy(),
            "WAREHOUSE": WAREHOUSE_WEIGHTS.copy(),
            "PIPELINE": PIPELINE_WEIGHTS.copy(),
        }
        
        self.phase1_weights = {k: v.copy() for k, v in self.asset_class_weights.items()}
        self.regional_adjustments = {}  # Region -> adjustment factor
        self.insurance_adjustments = {}  # Asset class -> adjustment factor
        
        self.calibration_history = []
    
    def phase1_expert_initialization(
        self,
        expert_weights: Dict[str, List[float]],
        consistency_threshold: float = 0.85,
    ) -> CalibrationResults:
        """
        Phase 1: Initialize weights from expert judgment.
        
        Expert provides weight vectors for each asset class.
        Validates consistency across multiple experts if available.
        
        Args:
            expert_weights: Dict mapping asset classes to weight lists
            consistency_threshold: Minimum consistency score [0, 1]
            
        Returns:
            CalibrationResults with validated initial weights
        """
        # Validate expert weights
        for asset_class, weights in expert_weights.items():
            if asset_class not in self.asset_class_weights:
                continue
            
            weights_array = np.array(weights)
            
            # Check weights sum to 1.0
            weight_sum = np.sum(weights_array)
            if not np.isclose(weight_sum, 1.0, rtol=1e-6):
                # Normalize if sum is close to 1.0
                if np.isclose(weight_sum, 0.0, atol=1e-9):
                    continue
                weights_array = weights_array / weight_sum
            
            # Check weights are in valid range
            if np.any(weights_array < 0) or np.any(weights_array > 1):
                # Clip to valid range
                weights_array = np.clip(weights_array, 0.0, 1.0)
                # Re-normalize
                weight_sum = np.sum(weights_array)
                if weight_sum > 0:
                    weights_array = weights_array / weight_sum
            
            self.phase1_weights[asset_class] = weights_array.tolist()
        
        # Update working weights
        self.asset_class_weights = {k: v.copy() for k, v in self.phase1_weights.items()}
        
        results = CalibrationResults(
            phase=1,
            mae=0.0,
            rmse=0.0,
            correlation=1.0,
            bias=0.0,
            updated_weights=self.phase1_weights,
        )
        
        self.calibration_history.append(results)
        return results
    
    def phase2_backtest(
        self,
        calibration_data: List[CalibrationMetrics],
        adjustment_rate: float = 0.1,
    ) -> CalibrationResults:
        """
        Phase 2: Backtest against historical data and adjust weights.
        
        Compares predictions to actual outcomes and adjusts weights
        to reduce prediction error.
        
        Args:
            calibration_data: List of CalibrationMetrics from historical events
            adjustment_rate: Rate of weight adjustment [0, 1]
            
        Returns:
            CalibrationResults with updated weights and error metrics
        """
        if not calibration_data:
            return CalibrationResults(
                phase=2, mae=0.0, rmse=0.0, correlation=1.0, bias=0.0
            )
        
        predictions = np.array([m.predicted_risk for m in calibration_data])
        actuals = np.array([m.actual_risk for m in calibration_data])
        
        # Compute error metrics
        errors = predictions - actuals
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        bias = float(np.mean(errors))
        
        # Compute correlation
        if np.std(predictions) > 0 and np.std(actuals) > 0:
            correlation = float(np.corrcoef(predictions, actuals)[0, 1])
        else:
            correlation = 0.0
        
        # Adjust weights based on error direction
        adjustment_rate = np.clip(adjustment_rate, 0.0, 1.0)
        
        # For each asset class, adjust weights slightly toward reducing bias
        for asset_class in self.asset_class_weights:
            class_data = [m for m in calibration_data if m.asset_class == asset_class]
            
            if not class_data:
                continue
            
            class_errors = np.array([m.predicted_risk - m.actual_risk for m in class_data])
            class_bias = np.mean(class_errors)
            
            # If model over-predicts (positive bias), reduce weight slightly
            # If model under-predicts (negative bias), increase weight slightly
            if abs(class_bias) > 0.05:  # Threshold for adjustment
                current_weights = np.array(self.asset_class_weights[asset_class])
                
                # Gentle adjustment toward center
                adjustment = -class_bias * adjustment_rate * 0.5
                adjusted_weights = current_weights + adjustment / len(current_weights)
                
                # Clip and re-normalize
                adjusted_weights = np.clip(adjusted_weights, 0.01, 0.5)
                adjusted_weights = adjusted_weights / np.sum(adjusted_weights)
                
                self.asset_class_weights[asset_class] = adjusted_weights.tolist()
        
        results = CalibrationResults(
            phase=2,
            mae=mae,
            rmse=rmse,
            correlation=correlation,
            bias=bias,
            updated_weights={k: v.copy() for k, v in self.asset_class_weights.items()},
        )
        
        self.calibration_history.append(results)
        return results
    
    def phase3_regional_calibration(
        self,
        calibration_data: List[CalibrationMetrics],
        min_samples_per_region: int = 10,
    ) -> CalibrationResults:
        """
        Phase 3: Calibrate regional adjustments for geographic variations.
        
        Computes regional adjustment factors to account for differences
        in model performance across geographic regions.
        
        Args:
            calibration_data: List of CalibrationMetrics with region field
            min_samples_per_region: Minimum events per region for adjustment
            
        Returns:
            CalibrationResults with regional adjustment factors
        """
        if not calibration_data:
            return CalibrationResults(
                phase=3, mae=0.0, rmse=0.0, correlation=1.0, bias=0.0
            )
        
        # Group by region
        regions = {}
        for metric in calibration_data:
            if metric.region not in regions:
                regions[metric.region] = []
            regions[metric.region].append(metric)
        
        regional_adjustments = {}
        region_errors = {}
        
        for region, region_data in regions.items():
            if len(region_data) < min_samples_per_region:
                continue
            
            predictions = np.array([m.predicted_risk for m in region_data])
            actuals = np.array([m.actual_risk for m in region_data])
            
            errors = predictions - actuals
            mae = float(np.mean(np.abs(errors)))
            bias = float(np.mean(errors))
            
            region_errors[region] = mae
            
            # Adjustment factor: 1.0 = no adjustment, <1.0 = reduce predictions, >1.0 = increase
            if mae > 0.05:
                # If prediction error is significant, compute correction factor
                # correction = actuals / predictions (avoid division by zero)
                valid_idx = predictions > 0.01
                if np.any(valid_idx):
                    ratios = actuals[valid_idx] / predictions[valid_idx]
                    adjustment = float(np.median(ratios))
                    adjustment = np.clip(adjustment, 0.7, 1.3)
                else:
                    adjustment = 1.0
            else:
                adjustment = 1.0
            
            regional_adjustments[region] = adjustment
        
        self.regional_adjustments = regional_adjustments
        
        # Compute overall metrics
        all_predictions = np.array([m.predicted_risk for m in calibration_data])
        all_actuals = np.array([m.actual_risk for m in calibration_data])
        
        errors = all_predictions - all_actuals
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        bias = float(np.mean(errors))
        
        if np.std(all_predictions) > 0 and np.std(all_actuals) > 0:
            correlation = float(np.corrcoef(all_predictions, all_actuals)[0, 1])
        else:
            correlation = 0.0
        
        results = CalibrationResults(
            phase=3,
            mae=mae,
            rmse=rmse,
            correlation=correlation,
            bias=bias,
            regional_adjustments=regional_adjustments,
        )
        
        self.calibration_history.append(results)
        return results
    
    def phase4_insurance_calibration(
        self,
        calibration_data: List[CalibrationMetrics],
        target_loss_ratio: float = 0.75,
    ) -> CalibrationResults:
        """
        Phase 4: Calibrate insurance premium adjustments.
        
        Adjusts risk scores to align with insurance claim experience
        and premium adequacy.
        
        Args:
            calibration_data: List of CalibrationMetrics with insurance_cost field
            target_loss_ratio: Target ratio of claims to premiums (default 0.75)
            
        Returns:
            CalibrationResults with insurance adjustment factors
        """
        if not calibration_data:
            return CalibrationResults(
                phase=4, mae=0.0, rmse=0.0, correlation=1.0, bias=0.0
            )
        
        # Filter to events with insurance data
        insured_data = [m for m in calibration_data if m.insurance_cost is not None]
        
        if not insured_data:
            return CalibrationResults(
                phase=4, mae=0.0, rmse=0.0, correlation=1.0, bias=0.0
            )
        
        # Group by asset class
        asset_classes = {}
        for metric in insured_data:
            if metric.asset_class not in asset_classes:
                asset_classes[metric.asset_class] = []
            asset_classes[metric.asset_class].append(metric)
        
        insurance_adjustments = {}
        
        for asset_class, class_data in asset_classes.items():
            if len(class_data) < 5:  # Minimum 5 events per class
                continue
            
            # Compute actual loss ratio
            total_claims = sum(m.actual_risk for m in class_data)  # Normalized loss
            total_premiums = sum(m.insurance_cost for m in class_data)
            
            if total_premiums <= 0:
                continue
            
            actual_loss_ratio = total_claims / total_premiums
            
            # Compute adjustment to reach target loss ratio
            if actual_loss_ratio > 0:
                adjustment = target_loss_ratio / actual_loss_ratio
                adjustment = np.clip(adjustment, 0.8, 1.5)  # Bound adjustment
            else:
                adjustment = 1.0
            
            insurance_adjustments[asset_class] = adjustment
        
        self.insurance_adjustments = insurance_adjustments
        
        # Compute overall metrics
        all_predictions = np.array([m.predicted_risk for m in insured_data])
        all_actuals = np.array([m.actual_risk for m in insured_data])
        
        errors = all_predictions - all_actuals
        mae = float(np.mean(np.abs(errors)))
        rmse = float(np.sqrt(np.mean(errors ** 2)))
        bias = float(np.mean(errors))
        
        if np.std(all_predictions) > 0 and np.std(all_actuals) > 0:
            correlation = float(np.corrcoef(all_predictions, all_actuals)[0, 1])
        else:
            correlation = 0.0
        
        results = CalibrationResults(
            phase=4,
            mae=mae,
            rmse=rmse,
            correlation=correlation,
            bias=bias,
            insurance_adjustments=insurance_adjustments,
        )
        
        self.calibration_history.append(results)
        return results
    
    def apply_regional_adjustment(
        self,
        risk_score: float,
        region: str,
    ) -> float:
        """
        Apply regional adjustment factor to risk score.
        
        Args:
            risk_score: Base risk score [0, 1]
            region: Geographic region
            
        Returns:
            Adjusted risk score [0, 1]
        """
        if region not in self.regional_adjustments:
            return float(np.clip(risk_score, 0.0, 1.0))
        
        adjustment = self.regional_adjustments[region]
        adjusted = risk_score * adjustment
        
        return float(np.clip(adjusted, 0.0, 1.0))
    
    def apply_insurance_adjustment(
        self,
        risk_score: float,
        asset_class: str,
    ) -> float:
        """
        Apply insurance adjustment factor to risk score.
        
        Args:
            risk_score: Base risk score [0, 1]
            asset_class: Asset class (AIRPORT, SEAPORT, etc.)
            
        Returns:
            Adjusted risk score [0, 1]
        """
        if asset_class not in self.insurance_adjustments:
            return float(np.clip(risk_score, 0.0, 1.0))
        
        adjustment = self.insurance_adjustments[asset_class]
        adjusted = risk_score * adjustment
        
        return float(np.clip(adjusted, 0.0, 1.0))
    
    def get_current_weights(self) -> Dict[str, List[float]]:
        """
        Get current asset class weights after calibration.
        
        Returns:
            Dict mapping asset classes to weight lists
        """
        return {k: v.copy() for k, v in self.asset_class_weights.items()}
    
    def get_calibration_summary(self) -> Dict[str, any]:
        """
        Get summary of all calibration phases completed.
        
        Returns:
            Dict with results from each phase
        """
        summary = {
            "total_phases": len(self.calibration_history),
            "phases": {},
        }
        
        for result in self.calibration_history:
            phase_key = f"phase_{result.phase}"
            summary["phases"][phase_key] = {
                "mae": result.mae,
                "rmse": result.rmse,
                "correlation": result.correlation,
                "bias": result.bias,
            }
        
        return summary
