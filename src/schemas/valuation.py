"""
Pydantic schemas for valuation API endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import date
from enum import Enum


class ValuationMethodEnum(str, Enum):
    """Valuation method enumeration."""
    EBITDA_MULTIPLE = "ebitda_multiple"
    DCF = "dcf"
    EARNINGS_VALUE = "earnings_value"
    ASSET_VALUE = "asset_value"
    PRACTITIONER = "practitioner"


class CompanySizeEnum(str, Enum):
    """Company size enumeration."""
    MICRO = "micro"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


# EBITDA Multiple Schemas

class EBITDAMultipleParamsSchema(BaseModel):
    """EBITDA multiple valuation parameters."""
    ebitda: Decimal = Field(..., description="Normalized EBITDA")
    base_multiple: Decimal = Field(..., description="Industry multiple")
    growth_rate: Decimal = Field(..., description="Annual growth rate (%)")
    risk_score: int = Field(..., ge=1, le=10, description="Risk score (1-10)")
    company_size: CompanySizeEnum = Field(..., description="Company size")
    cash: Decimal = Field(default=Decimal("0"), description="Cash and equivalents")
    debt: Decimal = Field(default=Decimal("0"), description="Financial debt")
    non_operating_assets: Decimal = Field(default=Decimal("0"), description="Non-operating assets")


# DCF Schemas

class DCFParamsSchema(BaseModel):
    """DCF valuation parameters."""
    fcf_projections: List[Decimal] = Field(..., description="Free cash flow projections")
    wacc: Decimal = Field(..., description="Weighted average cost of capital (%)")
    terminal_growth_rate: Decimal = Field(..., description="Terminal growth rate (%)")
    cash: Decimal = Field(default=Decimal("0"), description="Cash and equivalents")
    debt: Decimal = Field(default=Decimal("0"), description="Financial debt")
    non_operating_assets: Decimal = Field(default=Decimal("0"), description="Non-operating assets")
    
    @validator("fcf_projections")
    def validate_fcf_projections(cls, v):
        if not v:
            raise ValueError("FCF projections cannot be empty")
        return v
    
    @validator("wacc")
    def validate_wacc(cls, v):
        if v <= 0:
            raise ValueError("WACC must be positive")
        return v


# Earnings Value Schemas

class EarningsValueParamsSchema(BaseModel):
    """Earnings value valuation parameters."""
    historical_earnings: List[Decimal] = Field(..., description="Historical earnings (3-5 years)")
    risk_free_rate: Decimal = Field(..., description="Risk-free rate (%)")
    risk_premium: Decimal = Field(..., description="Risk premium (%)")
    use_practitioner_method: bool = Field(default=False, description="Use practitioner method")
    asset_value: Optional[Decimal] = Field(None, description="Asset value (if using practitioner method)")
    
    @validator("historical_earnings")
    def validate_historical_earnings(cls, v):
        if len(v) < 3:
            raise ValueError("At least 3 years of historical earnings required")
        return v


# Asset Value Schemas

class AssetValueParamsSchema(BaseModel):
    """Asset value valuation parameters."""
    real_estate_market_value: Decimal = Field(..., description="Real estate market value")
    machinery_replacement_value: Decimal = Field(..., description="Machinery replacement value")
    machinery_depreciation: Decimal = Field(..., ge=0, le=100, description="Machinery depreciation (%)")
    inventory_value: Decimal = Field(..., description="Inventory value")
    receivables: Decimal = Field(..., description="Accounts receivable")
    receivables_risk: Decimal = Field(..., ge=0, le=100, description="Receivables risk (%)")
    cash: Decimal = Field(..., description="Cash and equivalents")
    intangible_assets: Decimal = Field(..., description="Intangible assets")
    liabilities: Decimal = Field(..., description="Total liabilities")


# Practitioner Method Schemas

class PractitionerParamsSchema(BaseModel):
    """Practitioner method valuation parameters."""
    earnings_value: Decimal = Field(..., description="Earnings value")
    asset_value: Decimal = Field(..., description="Asset value")
    earnings_weight: Decimal = Field(default=Decimal("0.67"), ge=0, le=1, description="Earnings weight (0-1)")


# Valuation Request/Response Schemas

class ValuationMethodRequest(BaseModel):
    """Request for a single valuation method."""
    method: ValuationMethodEnum
    parameters: Dict[str, Any]
    weight: Decimal = Field(default=Decimal("1.0"), ge=0, le=1, description="Weight for final value")


class ValuationCreateRequest(BaseModel):
    """Request to create a new valuation."""
    company_id: str = Field(..., description="Company UUID")
    name: str = Field(..., description="Valuation name")
    valuation_date: date = Field(..., description="Valuation date")
    methods: List[ValuationMethodRequest] = Field(..., description="Valuation methods to apply")
    assumptions: Optional[Dict[str, Any]] = Field(default={}, description="Additional assumptions")
    currency: str = Field(default="CHF", description="Currency code (ISO 4217)")
    
    @validator("methods")
    def validate_methods(cls, v):
        if not v:
            raise ValueError("At least one valuation method required")
        return v


class ValuationMethodResult(BaseModel):
    """Result of a single valuation method."""
    method: ValuationMethodEnum
    calculated_value: float
    enterprise_value: Optional[float] = None
    equity_value: Optional[float] = None
    weight: float
    details: Dict[str, Any]


class ValuationResponse(BaseModel):
    """Response with valuation results."""
    id: str
    company_id: str
    name: str
    valuation_date: date
    status: str
    final_value: Optional[float] = None
    final_value_min: Optional[float] = None
    final_value_max: Optional[float] = None
    currency: str
    method_results: List[ValuationMethodResult]
    assumptions: Dict[str, Any]
    created_at: str
    updated_at: str


# Sensitivity Analysis Schemas

class SensitivityAnalysisRequest(BaseModel):
    """Request for sensitivity analysis."""
    variable_name: str = Field(..., description="Variable to analyze")
    min_value: Decimal = Field(..., description="Minimum value")
    max_value: Decimal = Field(..., description="Maximum value")
    steps: int = Field(default=20, ge=2, le=100, description="Number of steps")
    
    @validator("max_value")
    def validate_max_value(cls, v, values):
        if "min_value" in values and v <= values["min_value"]:
            raise ValueError("Max value must be greater than min value")
        return v


class SensitivityDataPoint(BaseModel):
    """Single data point in sensitivity analysis."""
    variable_value: float
    enterprise_value: Optional[float]
    equity_value: float


class SensitivityAnalysisResponse(BaseModel):
    """Response with sensitivity analysis results."""
    id: str
    valuation_id: str
    variable_name: str
    base_value: float
    min_value: float
    max_value: float
    step_size: float
    results: List[SensitivityDataPoint]
    created_at: str
