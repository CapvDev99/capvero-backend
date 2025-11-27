"""
DCF (Discounted Cash Flow) Valuation Service

Implements the DCF valuation method for company valuations.
"""

from decimal import Decimal
from typing import List, Dict, Any


class DCFParams:
    """Parameters for DCF valuation."""
    
    def __init__(
        self,
        fcf_projections: List[Decimal],
        wacc: Decimal,
        terminal_growth_rate: Decimal,
        cash: Decimal = Decimal("0"),
        debt: Decimal = Decimal("0"),
        non_operating_assets: Decimal = Decimal("0"),
    ):
        self.fcf_projections = fcf_projections
        self.wacc = wacc
        self.terminal_growth_rate = terminal_growth_rate
        self.cash = cash
        self.debt = debt
        self.non_operating_assets = non_operating_assets
        
        # Validation
        if not fcf_projections:
            raise ValueError("FCF projections cannot be empty")
        if wacc <= 0:
            raise ValueError("WACC must be positive")
        if terminal_growth_rate >= wacc:
            raise ValueError("Terminal growth rate must be less than WACC")
        if terminal_growth_rate < 0:
            raise ValueError("Terminal growth rate cannot be negative")


class WACCParams:
    """Parameters for WACC calculation."""
    
    def __init__(
        self,
        risk_free_rate: Decimal,
        beta: Decimal,
        market_risk_premium: Decimal,
        size_premium: Decimal,
        company_specific_risk: Decimal,
        interest_rate: Decimal,
        equity_value: Decimal,
        debt_value: Decimal,
        tax_rate: Decimal,
    ):
        self.risk_free_rate = risk_free_rate
        self.beta = beta
        self.market_risk_premium = market_risk_premium
        self.size_premium = size_premium
        self.company_specific_risk = company_specific_risk
        self.interest_rate = interest_rate
        self.equity_value = equity_value
        self.debt_value = debt_value
        self.tax_rate = tax_rate


class DCFService:
    """Service for DCF valuation calculations."""
    
    @staticmethod
    def calculate_wacc(params: WACCParams) -> Decimal:
        """
        Calculate Weighted Average Cost of Capital (WACC).
        
        Args:
            params: WACC calculation parameters
            
        Returns:
            WACC as decimal (e.g., 0.08 for 8%)
        """
        # Cost of equity (CAPM)
        cost_of_equity = (
            params.risk_free_rate
            + params.beta * params.market_risk_premium
            + params.size_premium
            + params.company_specific_risk
        )
        
        # Cost of debt (after tax)
        cost_of_debt = params.interest_rate
        
        # Capital structure weights
        total_capital = params.equity_value + params.debt_value
        equity_weight = params.equity_value / total_capital if total_capital > 0 else Decimal("1")
        debt_weight = params.debt_value / total_capital if total_capital > 0 else Decimal("0")
        
        # WACC
        wacc = (
            equity_weight * cost_of_equity
            + debt_weight * cost_of_debt * (Decimal("1") - params.tax_rate)
        )
        
        return wacc
    
    @classmethod
    def calculate(cls, params: DCFParams) -> Dict[str, Any]:
        """
        Calculate company valuation using DCF method.
        
        Args:
            params: Valuation parameters
            
        Returns:
            Dictionary with valuation results and details
        """
        # Step 1: Calculate present value of FCFs
        pv_fcfs = []
        sum_pv_fcfs = Decimal("0")
        
        for t, fcf in enumerate(params.fcf_projections, start=1):
            discount_factor = (Decimal("1") + params.wacc) ** t
            pv = fcf / discount_factor
            pv_fcfs.append(float(pv))
            sum_pv_fcfs += pv
        
        # Step 2: Calculate terminal value
        fcf_final = params.fcf_projections[-1]
        terminal_value = (
            fcf_final * (Decimal("1") + params.terminal_growth_rate)
            / (params.wacc - params.terminal_growth_rate)
        )
        
        # Step 3: Calculate present value of terminal value
        n = len(params.fcf_projections)
        discount_factor = (Decimal("1") + params.wacc) ** n
        pv_terminal = terminal_value / discount_factor
        
        # Step 4: Calculate enterprise value
        enterprise_value = sum_pv_fcfs + pv_terminal
        
        # Step 5: Calculate equity value
        equity_value = (
            enterprise_value
            + params.cash
            - params.debt
            + params.non_operating_assets
        )
        
        # Round to 2 decimal places
        enterprise_value = enterprise_value.quantize(Decimal("0.01"))
        equity_value = equity_value.quantize(Decimal("0.01"))
        terminal_value = terminal_value.quantize(Decimal("0.01"))
        pv_terminal = pv_terminal.quantize(Decimal("0.01"))
        sum_pv_fcfs = sum_pv_fcfs.quantize(Decimal("0.01"))
        
        return {
            "method": "dcf",
            "calculated_value": float(equity_value),
            "enterprise_value": float(enterprise_value),
            "equity_value": float(equity_value),
            "details": {
                "wacc": float(params.wacc),
                "terminal_growth_rate": float(params.terminal_growth_rate),
                "forecast_period": n,
                "fcf_projections": [float(fcf) for fcf in params.fcf_projections],
                "pv_fcfs": pv_fcfs,
                "sum_pv_fcfs": float(sum_pv_fcfs),
                "terminal_value": float(terminal_value),
                "pv_terminal_value": float(pv_terminal),
                "bridge": {
                    "enterprise_value": float(enterprise_value),
                    "plus_cash": float(params.cash),
                    "minus_debt": float(-params.debt),
                    "plus_non_operating": float(params.non_operating_assets),
                    "equity_value": float(equity_value),
                },
            },
        }
    
    @staticmethod
    def calculate_fcf_from_ebit(
        ebit: Decimal,
        tax_rate: Decimal,
        depreciation: Decimal,
        capex: Decimal,
        working_capital_change: Decimal,
    ) -> Decimal:
        """
        Calculate Free Cash Flow from EBIT.
        
        Args:
            ebit: Earnings Before Interest and Taxes
            tax_rate: Corporate tax rate (e.g., 0.20 for 20%)
            depreciation: Depreciation and amortization
            capex: Capital expenditures
            working_capital_change: Change in working capital
            
        Returns:
            Free Cash Flow
        """
        nopat = ebit * (Decimal("1") - tax_rate)  # Net Operating Profit After Tax
        fcf = nopat + depreciation - capex - working_capital_change
        return fcf
