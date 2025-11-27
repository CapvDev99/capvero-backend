"""
Manual Forecast Service

Allows users to create manual forecasts based on their own projections.
"""

from typing import List, Dict, Any
from decimal import Decimal
import numpy as np


class ManualForecastParams:
    """Parameters for manual forecasting."""
    
    def __init__(
        self,
        projections: List[Dict[str, Any]],
        historical_data: List[Dict[str, Any]] = None,
    ):
        self.projections = projections
        self.historical_data = historical_data or []
        
        # Validation
        if not projections:
            raise ValueError("Projections cannot be empty")
        
        # Validate projection structure
        for proj in projections:
            if 'year' not in proj or 'value' not in proj:
                raise ValueError("Each projection must have 'year' and 'value' fields")
            if proj['value'] < 0:
                raise ValueError("Projected values cannot be negative")


class ManualForecastService:
    """Service for manual forecasting."""
    
    @staticmethod
    def validate_plausibility(
        projections: List[Dict[str, Any]],
        historical_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate plausibility of manual projections against historical data.
        
        Args:
            projections: Manual projections
            historical_data: Historical data for comparison
            
        Returns:
            Dictionary with validation results and warnings
        """
        warnings = []
        
        if not historical_data:
            return {
                'is_plausible': True,
                'warnings': ['No historical data available for comparison'],
            }
        
        # Calculate historical growth rates
        historical_values = [d['value'] for d in historical_data]
        historical_growth_rates = []
        
        for i in range(1, len(historical_values)):
            growth_rate = (historical_values[i] - historical_values[i-1]) / historical_values[i-1]
            historical_growth_rates.append(growth_rate)
        
        avg_historical_growth = np.mean(historical_growth_rates) if historical_growth_rates else 0
        
        # Calculate projected growth rates
        last_historical_value = historical_data[-1]['value']
        projected_values = [last_historical_value] + [p['value'] for p in projections]
        
        for i in range(1, len(projected_values)):
            growth_rate = (projected_values[i] - projected_values[i-1]) / projected_values[i-1]
            
            # Check for extreme growth rates
            if abs(growth_rate) > 0.5:  # >50% change
                warnings.append(
                    f"Year {projections[i-1]['year']}: Extreme growth rate of {growth_rate*100:.1f}% "
                    f"(historical average: {avg_historical_growth*100:.1f}%)"
                )
            
            # Check for negative values
            if projected_values[i] < 0:
                warnings.append(
                    f"Year {projections[i-1]['year']}: Negative value projected"
                )
        
        return {
            'is_plausible': len(warnings) == 0,
            'warnings': warnings,
            'historical_avg_growth': float(avg_historical_growth),
        }
    
    @staticmethod
    def calculate_confidence_intervals(
        projections: List[Dict[str, Any]],
        confidence_width: float = 0.15
    ) -> List[Dict[str, Any]]:
        """
        Calculate synthetic confidence intervals for manual projections.
        
        Args:
            projections: Manual projections
            confidence_width: Width of confidence interval (±15% default)
            
        Returns:
            List of projections with confidence intervals
        """
        enriched_projections = []
        
        for proj in projections:
            value = proj['value']
            lower_bound = value * (1 - confidence_width)
            upper_bound = value * (1 + confidence_width)
            
            enriched_projections.append({
                'year': proj['year'],
                'predicted_value': float(value),
                'lower_bound': float(lower_bound),
                'upper_bound': float(upper_bound),
            })
        
        return enriched_projections
    
    @classmethod
    def calculate(cls, params: ManualForecastParams) -> Dict[str, Any]:
        """
        Process manual forecast.
        
        Args:
            params: Manual forecast parameters
            
        Returns:
            Dictionary with forecast results
        """
        # Step 1: Validate plausibility
        validation = cls.validate_plausibility(
            params.projections,
            params.historical_data
        )
        
        # Step 2: Calculate confidence intervals
        predictions = cls.calculate_confidence_intervals(params.projections)
        
        # Step 3: Calculate simple metrics (if historical data available)
        model_metrics = {}
        if params.historical_data:
            historical_values = [d['value'] for d in params.historical_data]
            avg_value = np.mean(historical_values)
            std_value = np.std(historical_values)
            
            model_metrics = {
                'historical_avg': float(avg_value),
                'historical_std': float(std_value),
                'coefficient_of_variation': float(std_value / avg_value) if avg_value > 0 else 0,
            }
        
        return {
            'method': 'manual',
            'predictions': predictions,
            'model_parameters': {
                'projection_count': len(params.projections),
                'confidence_width': 0.15,
            },
            'model_metrics': model_metrics,
            'validation': validation,
            'data_quality': {
                'data_points': len(params.historical_data),
                'projection_points': len(params.projections),
            },
        }
    
    @staticmethod
    def generate_scenarios(
        base_predictions: List[Dict[str, Any]],
        best_case_factor: float = 1.20,
        worst_case_factor: float = 0.80
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate Best/Worst case scenarios for manual projections.
        
        Args:
            base_predictions: List of base case predictions
            best_case_factor: Multiplier for best case (default 1.20 = +20%)
            worst_case_factor: Multiplier for worst case (default 0.80 = -20%)
            
        Returns:
            Dictionary with 'base', 'best', 'worst' scenarios
        """
        scenarios = {
            'base': base_predictions,
            'best': [],
            'worst': []
        }
        
        for pred in base_predictions:
            base_value = pred['predicted_value']
            
            scenarios['best'].append({
                'year': pred['year'],
                'predicted_value': base_value * best_case_factor,
                'lower_bound': pred['lower_bound'],
                'upper_bound': pred['upper_bound'],
                'scenario': 'best',
            })
            
            scenarios['worst'].append({
                'year': pred['year'],
                'predicted_value': base_value * worst_case_factor,
                'lower_bound': pred['lower_bound'],
                'upper_bound': pred['upper_bound'],
                'scenario': 'worst',
            })
        
        return scenarios
