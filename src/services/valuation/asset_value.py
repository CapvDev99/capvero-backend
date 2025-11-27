"""
Asset Value Valuation Service (Substanzwertverfahren)

Implements the asset-based valuation method for company valuations.
"""

from decimal import Decimal
from typing import Dict, Any


class AssetValueParams:
    """Parameters for asset value valuation."""
    
    def __init__(
        self,
        real_estate_market_value: Decimal,
        machinery_replacement_value: Decimal,
        machinery_depreciation: Decimal,
        inventory_value: Decimal,
        receivables: Decimal,
        receivables_risk: Decimal,
        cash: Decimal,
        intangible_assets: Decimal,
        liabilities: Decimal,
    ):
        self.real_estate_market_value = real_estate_market_value
        self.machinery_replacement_value = machinery_replacement_value
        self.machinery_depreciation = machinery_depreciation
        self.inventory_value = inventory_value
        self.receivables = receivables
        self.receivables_risk = receivables_risk
        self.cash = cash
        self.intangible_assets = intangible_assets
        self.liabilities = liabilities
        
        # Validation
        if machinery_depreciation < 0 or machinery_depreciation > 100:
            raise ValueError("Machinery depreciation must be between 0 and 100 percent")
        if receivables_risk < 0 or receivables_risk > 100:
            raise ValueError("Receivables risk must be between 0 and 100 percent")


class AssetValueService:
    """Service for asset value valuation calculations."""
    
    @classmethod
    def calculate(cls, params: AssetValueParams) -> Dict[str, Any]:
        """
        Calculate company valuation using asset value method.
        
        Args:
            params: Valuation parameters
            
        Returns:
            Dictionary with valuation results and details
        """
        # Step 1: Calculate fixed assets
        machinery_net = params.machinery_replacement_value * (
            Decimal("1") - params.machinery_depreciation / Decimal("100")
        )
        
        fixed_assets_total = (
            params.real_estate_market_value
            + machinery_net
            + params.intangible_assets
        )
        
        # Step 2: Calculate current assets
        receivables_provision = params.receivables * params.receivables_risk / Decimal("100")
        receivables_net = params.receivables - receivables_provision
        
        current_assets_total = (
            params.inventory_value
            + receivables_net
            + params.cash
        )
        
        # Step 3: Calculate total assets
        total_assets = fixed_assets_total + current_assets_total
        
        # Step 4: Calculate net asset value (substanzwert)
        net_asset_value = total_assets - params.liabilities
        
        # Round to 2 decimal places
        machinery_net = machinery_net.quantize(Decimal("0.01"))
        fixed_assets_total = fixed_assets_total.quantize(Decimal("0.01"))
        receivables_provision = receivables_provision.quantize(Decimal("0.01"))
        receivables_net = receivables_net.quantize(Decimal("0.01"))
        current_assets_total = current_assets_total.quantize(Decimal("0.01"))
        total_assets = total_assets.quantize(Decimal("0.01"))
        net_asset_value = net_asset_value.quantize(Decimal("0.01"))
        
        return {
            "method": "asset_value",
            "calculated_value": float(net_asset_value),
            "details": {
                "fixed_assets": {
                    "real_estate": float(params.real_estate_market_value),
                    "machinery_gross": float(params.machinery_replacement_value),
                    "machinery_depreciation": float(params.machinery_replacement_value - machinery_net),
                    "machinery_net": float(machinery_net),
                    "intangibles": float(params.intangible_assets),
                    "total": float(fixed_assets_total),
                },
                "current_assets": {
                    "inventory": float(params.inventory_value),
                    "receivables_gross": float(params.receivables),
                    "receivables_provision": float(receivables_provision),
                    "receivables_net": float(receivables_net),
                    "cash": float(params.cash),
                    "total": float(current_assets_total),
                },
                "total_assets": float(total_assets),
                "liabilities": float(params.liabilities),
                "net_asset_value": float(net_asset_value),
            },
        }
