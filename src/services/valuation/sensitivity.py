"""
Sensitivity Analysis Service

Performs sensitivity analysis on valuation parameters.
"""

from decimal import Decimal
from typing import Dict, Any, List, Callable


class SensitivityParams:
    """Parameters for sensitivity analysis."""
    
    def __init__(
        self,
        variable_name: str,
        base_value: Decimal,
        min_value: Decimal,
        max_value: Decimal,
        steps: int = 20,
    ):
        self.variable_name = variable_name
        self.base_value = base_value
        self.min_value = min_value
        self.max_value = max_value
        self.steps = steps
        
        # Validation
        if min_value >= max_value:
            raise ValueError("Min value must be less than max value")
        if steps < 2:
            raise ValueError("Steps must be at least 2")


class SensitivityService:
    """Service for sensitivity analysis calculations."""
    
    @staticmethod
    def perform_analysis(
        params: SensitivityParams,
        base_params: Dict[str, Any],
        valuation_func: Callable,
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on a valuation parameter.
        
        Args:
            params: Sensitivity analysis parameters
            base_params: Base valuation parameters
            valuation_func: Function to calculate valuation with modified parameters
            
        Returns:
            Dictionary with sensitivity analysis results
        """
        results = []
        step_size = (params.max_value - params.min_value) / Decimal(params.steps)
        
        for i in range(params.steps + 1):
            test_value = params.min_value + (Decimal(i) * step_size)
            
            # Create modified parameters
            test_params = base_params.copy()
            test_params[params.variable_name] = test_value
            
            # Calculate valuation with modified parameter
            valuation = valuation_func(test_params)
            
            results.append({
                "variable_value": float(test_value),
                "enterprise_value": valuation.get("enterprise_value"),
                "equity_value": valuation.get("calculated_value"),
            })
        
        return {
            "variable_name": params.variable_name,
            "base_value": float(params.base_value),
            "min_value": float(params.min_value),
            "max_value": float(params.max_value),
            "steps": params.steps,
            "results": results,
        }
    
    @staticmethod
    def calculate_tornado_chart_data(
        base_valuation: Decimal,
        sensitivity_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Calculate data for tornado chart visualization.
        
        Args:
            base_valuation: Base case valuation
            sensitivity_results: List of sensitivity analysis results
            
        Returns:
            List of tornado chart data points sorted by impact
        """
        tornado_data = []
        
        for result in sensitivity_results:
            variable_name = result["variable_name"]
            results = result["results"]
            
            # Find min and max valuations
            valuations = [r["equity_value"] for r in results]
            min_valuation = min(valuations)
            max_valuation = max(valuations)
            
            # Calculate impact
            downside_impact = abs(base_valuation - Decimal(str(min_valuation)))
            upside_impact = abs(Decimal(str(max_valuation)) - base_valuation)
            total_impact = downside_impact + upside_impact
            
            tornado_data.append({
                "variable_name": variable_name,
                "base_valuation": float(base_valuation),
                "min_valuation": min_valuation,
                "max_valuation": max_valuation,
                "downside_impact": float(downside_impact),
                "upside_impact": float(upside_impact),
                "total_impact": float(total_impact),
            })
        
        # Sort by total impact (descending)
        tornado_data.sort(key=lambda x: x["total_impact"], reverse=True)
        
        return tornado_data
