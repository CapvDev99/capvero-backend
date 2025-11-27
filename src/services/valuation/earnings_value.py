"""
Earnings Value Valuation Service (Ertragswertverfahren)

Implements the Swiss earnings value method for company valuations.
"""

from decimal import Decimal
from typing import List, Dict, Any, Optional


class EarningsValueParams:
    """Parameters for earnings value valuation."""
    
    def __init__(
        self,
        historical_earnings: List[Decimal],
        risk_free_rate: Decimal,
        risk_premium: Decimal,
        use_practitioner_method: bool = False,
        asset_value: Optional[Decimal] = None,
    ):
        self.historical_earnings = historical_earnings
        self.risk_free_rate = risk_free_rate
        self.risk_premium = risk_premium
        self.use_practitioner_method = use_practitioner_method
        self.asset_value = asset_value
        
        # Validation
        if not historical_earnings:
            raise ValueError("Historical earnings cannot be empty")
        if len(historical_earnings) < 3:
            raise ValueError("At least 3 years of historical earnings required")
        if risk_free_rate < 0:
            raise ValueError("Risk-free rate cannot be negative")
        if risk_premium < 0:
            raise ValueError("Risk premium cannot be negative")
        if use_practitioner_method and asset_value is None:
            raise ValueError("Asset value required when using practitioner method")


class EarningsValueService:
    """Service for earnings value valuation calculations."""
    
    @staticmethod
    def calculate_sustainable_earnings(historical_earnings: List[Decimal]) -> Decimal:
        """
        Calculate sustainable earnings as average of historical earnings.
        
        Args:
            historical_earnings: List of historical earnings (3-5 years)
            
        Returns:
            Sustainable earnings (average)
        """
        return sum(historical_earnings) / len(historical_earnings)
    
    @classmethod
    def calculate(cls, params: EarningsValueParams) -> Dict[str, Any]:
        """
        Calculate company valuation using earnings value method.
        
        Args:
            params: Valuation parameters
            
        Returns:
            Dictionary with valuation results and details
        """
        # Step 1: Calculate sustainable earnings
        sustainable_earnings = cls.calculate_sustainable_earnings(params.historical_earnings)
        
        # Step 2: Calculate capitalization rate
        capitalization_rate = params.risk_free_rate + params.risk_premium
        
        # Step 3: Calculate pure earnings value
        # Formula: (Sustainable Earnings / Capitalization Rate) × 100
        earnings_value = (sustainable_earnings / capitalization_rate) * Decimal("100")
        
        # Step 4: Apply practitioner method if requested
        if params.use_practitioner_method and params.asset_value:
            # Weighted average: 2/3 earnings value, 1/3 asset value
            final_value = (Decimal("2") * earnings_value + params.asset_value) / Decimal("3")
            practitioner_adjustment = True
        else:
            final_value = earnings_value
            practitioner_adjustment = False
        
        # Round to 2 decimal places
        sustainable_earnings = sustainable_earnings.quantize(Decimal("0.01"))
        earnings_value = earnings_value.quantize(Decimal("0.01"))
        final_value = final_value.quantize(Decimal("0.01"))
        
        return {
            "method": "earnings_value",
            "calculated_value": float(final_value),
            "details": {
                "historical_earnings": [float(e) for e in params.historical_earnings],
                "sustainable_earnings": float(sustainable_earnings),
                "risk_free_rate": float(params.risk_free_rate),
                "risk_premium": float(params.risk_premium),
                "capitalization_rate": float(capitalization_rate),
                "pure_earnings_value": float(earnings_value),
                "asset_value": float(params.asset_value) if params.asset_value else None,
                "practitioner_adjustment": practitioner_adjustment,
                "final_value": float(final_value),
            },
        }
