"""
Practitioner Method Valuation Service (Praktikerverfahren)

Implements the Swiss practitioner method (weighted average of earnings and asset value).
"""

from decimal import Decimal
from typing import Dict, Any


class PractitionerParams:
    """Parameters for practitioner method valuation."""
    
    def __init__(
        self,
        earnings_value: Decimal,
        asset_value: Decimal,
        earnings_weight: Decimal = Decimal("0.67"),  # 2/3 default
    ):
        self.earnings_value = earnings_value
        self.asset_value = asset_value
        self.earnings_weight = earnings_weight
        
        # Validation
        if earnings_weight < 0 or earnings_weight > 1:
            raise ValueError("Earnings weight must be between 0 and 1")


class PractitionerService:
    """Service for practitioner method valuation calculations."""
    
    @classmethod
    def calculate(cls, params: PractitionerParams) -> Dict[str, Any]:
        """
        Calculate company valuation using practitioner method.
        
        Args:
            params: Valuation parameters
            
        Returns:
            Dictionary with valuation results and details
        """
        # Calculate asset weight (complement of earnings weight)
        asset_weight = Decimal("1") - params.earnings_weight
        
        # Calculate weighted value
        practitioner_value = (
            params.earnings_value * params.earnings_weight
            + params.asset_value * asset_weight
        )
        
        # Round to 2 decimal places
        practitioner_value = practitioner_value.quantize(Decimal("0.01"))
        
        return {
            "method": "practitioner",
            "calculated_value": float(practitioner_value),
            "details": {
                "earnings_value": float(params.earnings_value),
                "asset_value": float(params.asset_value),
                "earnings_weight": float(params.earnings_weight),
                "asset_weight": float(asset_weight),
                "weighted_value": float(practitioner_value),
            },
        }
