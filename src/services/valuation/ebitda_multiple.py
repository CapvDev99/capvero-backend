"""
EBITDA Multiple Valuation Service

Implements the EBITDA multiple valuation method for company valuations.
"""

from decimal import Decimal
from typing import Dict, Any
from enum import Enum


class CompanySize(str, Enum):
    """Company size classification."""
    MICRO = "micro"      # < 1M revenue
    SMALL = "small"      # 1-10M revenue
    MEDIUM = "medium"    # 10-50M revenue
    LARGE = "large"      # > 50M revenue


class EBITDAMultipleParams:
    """Parameters for EBITDA multiple valuation."""
    
    def __init__(
        self,
        ebitda: Decimal,
        base_multiple: Decimal,
        growth_rate: Decimal,
        risk_score: int,
        company_size: CompanySize,
        cash: Decimal = Decimal("0"),
        debt: Decimal = Decimal("0"),
        non_operating_assets: Decimal = Decimal("0"),
    ):
        self.ebitda = ebitda
        self.base_multiple = base_multiple
        self.growth_rate = growth_rate
        self.risk_score = risk_score
        self.company_size = company_size
        self.cash = cash
        self.debt = debt
        self.non_operating_assets = non_operating_assets
        
        # Validation
        if not 1 <= risk_score <= 10:
            raise ValueError("Risk score must be between 1 and 10")
        if growth_rate < 0:
            raise ValueError("Growth rate cannot be negative")


class EBITDAMultipleService:
    """Service for EBITDA multiple valuation calculations."""
    
    @staticmethod
    def calculate_growth_factor(growth_rate: Decimal) -> Decimal:
        """
        Calculate growth adjustment factor.
        
        Args:
            growth_rate: Annual growth rate as percentage (e.g., 8.5 for 8.5%)
            
        Returns:
            Growth factor (0.0 to 0.30)
        """
        if growth_rate < 10:
            return Decimal("0")
        elif growth_rate < 20:
            return (growth_rate - Decimal("10")) * Decimal("0.015")
        else:
            return min(Decimal("0.30"), (growth_rate - Decimal("10")) * Decimal("0.015"))
    
    @staticmethod
    def calculate_risk_factor(risk_score: int) -> Decimal:
        """
        Calculate risk adjustment factor.
        
        Args:
            risk_score: Risk score from 1 (low) to 10 (high)
            
        Returns:
            Risk factor (0.0 to 0.30)
        """
        return Decimal(risk_score - 1) / Decimal(9) * Decimal("0.30")
    
    @staticmethod
    def calculate_size_factor(company_size: CompanySize) -> Decimal:
        """
        Calculate size adjustment factor.
        
        Args:
            company_size: Company size classification
            
        Returns:
            Size factor (-0.20 to 0.10)
        """
        size_map = {
            CompanySize.MICRO: Decimal("-0.20"),
            CompanySize.SMALL: Decimal("-0.10"),
            CompanySize.MEDIUM: Decimal("0.00"),
            CompanySize.LARGE: Decimal("0.10"),
        }
        return size_map.get(company_size, Decimal("0"))
    
    @classmethod
    def calculate(cls, params: EBITDAMultipleParams) -> Dict[str, Any]:
        """
        Calculate company valuation using EBITDA multiple method.
        
        Args:
            params: Valuation parameters
            
        Returns:
            Dictionary with valuation results and details
        """
        # Step 1: Calculate adjustment factors
        growth_factor = cls.calculate_growth_factor(params.growth_rate)
        risk_factor = cls.calculate_risk_factor(params.risk_score)
        size_factor = cls.calculate_size_factor(params.company_size)
        
        # Step 2: Calculate adjusted multiple
        adjusted_multiple = params.base_multiple * (
            Decimal("1") + growth_factor - risk_factor + size_factor
        )
        
        # Step 3: Calculate enterprise value
        enterprise_value = params.ebitda * adjusted_multiple
        
        # Step 4: Calculate equity value
        equity_value = (
            enterprise_value
            + params.cash
            - params.debt
            + params.non_operating_assets
        )
        
        # Round to 2 decimal places
        enterprise_value = enterprise_value.quantize(Decimal("0.01"))
        equity_value = equity_value.quantize(Decimal("0.01"))
        adjusted_multiple = adjusted_multiple.quantize(Decimal("0.01"))
        
        return {
            "method": "ebitda_multiple",
            "calculated_value": float(equity_value),
            "enterprise_value": float(enterprise_value),
            "equity_value": float(equity_value),
            "details": {
                "ebitda_normalized": float(params.ebitda),
                "base_multiple": float(params.base_multiple),
                "adjusted_multiple": float(adjusted_multiple),
                "adjustments": {
                    "growth_factor": float(growth_factor),
                    "risk_factor": float(risk_factor),
                    "size_factor": float(size_factor),
                },
                "bridge": {
                    "enterprise_value": float(enterprise_value),
                    "plus_cash": float(params.cash),
                    "minus_debt": float(-params.debt),
                    "plus_non_operating": float(params.non_operating_assets),
                    "equity_value": float(equity_value),
                },
            },
        }
