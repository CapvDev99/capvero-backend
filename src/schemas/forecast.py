"""
Pydantic schemas for forecast API endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import date
from enum import Enum


class ForecastMethodEnum(str, Enum):
    """Forecast method enumeration."""
    PROPHET = "prophet"
    ARIMA = "arima"
    MANUAL = "manual"


class ForecastTypeEnum(str, Enum):
    """Forecast type enumeration."""
    REVENUE = "revenue"
    EBITDA = "ebitda"
    CUSTOM = "custom"


class ScenarioEnum(str, Enum):
    """Scenario enumeration."""
    BASE = "base"
    BEST = "best"
    WORST = "worst"


# Historical Data Schema

class HistoricalDataPoint(BaseModel):
    """Single historical data point."""
    year: int = Field(..., description="Year")
    value: Decimal = Field(..., description="Value (revenue or EBITDA)")
    
    @validator("year")
    def validate_year(cls, v):
        if v < 1900 or v > 2100:
            raise ValueError("Year must be between 1900 and 2100")
        return v
    
    @validator("value")
    def validate_value(cls, v):
        if v < 0:
            raise ValueError("Value cannot be negative")
        return v


# Prophet Forecast Schemas

class ProphetForecastParamsSchema(BaseModel):
    """Prophet forecast parameters."""
    changepoint_prior_scale: Decimal = Field(
        default=Decimal("0.05"),
        ge=0.001,
        le=0.5,
        description="Flexibility of trend (0.001-0.5)"
    )
    seasonality_mode: str = Field(
        default="additive",
        description="Seasonality mode (additive or multiplicative)"
    )
    yearly_seasonality: bool = Field(
        default=True,
        description="Include yearly seasonality"
    )
    
    @validator("seasonality_mode")
    def validate_seasonality_mode(cls, v):
        if v not in ["additive", "multiplicative"]:
            raise ValueError("Seasonality mode must be 'additive' or 'multiplicative'")
        return v


# ARIMA Forecast Schemas

class ARIMAForecastParamsSchema(BaseModel):
    """ARIMA forecast parameters."""
    auto_order: bool = Field(
        default=True,
        description="Automatically select ARIMA order"
    )
    order: Optional[Tuple[int, int, int]] = Field(
        None,
        description="ARIMA order (p, d, q) if not auto"
    )
    
    @validator("order")
    def validate_order(cls, v, values):
        if not values.get("auto_order") and v is None:
            raise ValueError("Order must be specified when auto_order is False")
        if v is not None:
            p, d, q = v
            if p < 0 or d < 0 or q < 0:
                raise ValueError("ARIMA order parameters must be non-negative")
            if p > 5 or d > 2 or q > 5:
                raise ValueError("ARIMA order parameters too large (max: p=5, d=2, q=5)")
        return v


# Manual Forecast Schemas

class ManualProjection(BaseModel):
    """Manual projection for a single year."""
    year: int = Field(..., description="Year")
    value: Decimal = Field(..., description="Projected value")
    
    @validator("year")
    def validate_year(cls, v):
        if v < 2020 or v > 2100:
            raise ValueError("Year must be between 2020 and 2100")
        return v
    
    @validator("value")
    def validate_value(cls, v):
        if v < 0:
            raise ValueError("Projected value cannot be negative")
        return v


class ManualForecastParamsSchema(BaseModel):
    """Manual forecast parameters."""
    projections: List[ManualProjection] = Field(
        ...,
        description="Manual projections"
    )
    
    @validator("projections")
    def validate_projections(cls, v):
        if not v:
            raise ValueError("At least one projection required")
        # Check for duplicate years
        years = [p.year for p in v]
        if len(years) != len(set(years)):
            raise ValueError("Duplicate years in projections")
        return v


# Forecast Request/Response Schemas

class ForecastCreateRequest(BaseModel):
    """Request to create a new forecast."""
    company_id: str = Field(..., description="Company UUID")
    forecast_type: ForecastTypeEnum = Field(..., description="Type of forecast")
    method: ForecastMethodEnum = Field(..., description="Forecast method")
    years: int = Field(..., ge=1, le=10, description="Number of years to forecast")
    confidence_level: Decimal = Field(
        default=Decimal("0.95"),
        ge=0.5,
        le=0.99,
        description="Confidence level (0.5-0.99)"
    )
    generate_scenarios: bool = Field(
        default=True,
        description="Generate best/worst case scenarios"
    )
    historical_data: List[HistoricalDataPoint] = Field(
        ...,
        description="Historical data points"
    )
    model_parameters: Optional[Dict[str, Any]] = Field(
        default={},
        description="Method-specific parameters"
    )
    
    @validator("historical_data")
    def validate_historical_data(cls, v):
        if len(v) < 3:
            raise ValueError("At least 3 years of historical data required")
        return v


class PredictionDataPoint(BaseModel):
    """Single prediction data point."""
    year: int
    predicted_value: float
    lower_bound: float
    upper_bound: float
    scenario: ScenarioEnum = ScenarioEnum.BASE
    trend: Optional[float] = None
    seasonal: Optional[float] = None


class ModelMetrics(BaseModel):
    """Model evaluation metrics."""
    mape: float = Field(..., description="Mean Absolute Percentage Error (%)")
    rmse: float = Field(..., description="Root Mean Square Error")
    mae: float = Field(..., description="Mean Absolute Error")
    outlier_count: Optional[int] = None


class DataQuality(BaseModel):
    """Data quality information."""
    data_points: int
    outliers_detected: Optional[int] = None
    missing_values: int = 0
    projection_points: Optional[int] = None


class ForecastResponse(BaseModel):
    """Response with forecast results."""
    id: str
    company_id: str
    forecast_type: ForecastTypeEnum
    method: ForecastMethodEnum
    years: int
    confidence_level: float
    predictions: List[PredictionDataPoint]
    scenarios: Optional[Dict[str, List[PredictionDataPoint]]] = None
    model_parameters: Dict[str, Any]
    model_metrics: ModelMetrics
    data_quality: DataQuality
    validation: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str


# Forecast List Schema

class ForecastListItem(BaseModel):
    """Forecast list item (summary)."""
    id: str
    company_id: str
    forecast_type: ForecastTypeEnum
    method: ForecastMethodEnum
    years: int
    status: str
    created_at: str


# Visualization Schema

class ForecastVisualizationRequest(BaseModel):
    """Request to generate forecast visualization."""
    include_scenarios: bool = Field(default=True, description="Include best/worst scenarios")
    chart_type: str = Field(default="line", description="Chart type (line, area)")
    width: int = Field(default=1200, ge=400, le=2000, description="Chart width in pixels")
    height: int = Field(default=600, ge=300, le=1200, description="Chart height in pixels")
    
    @validator("chart_type")
    def validate_chart_type(cls, v):
        if v not in ["line", "area"]:
            raise ValueError("Chart type must be 'line' or 'area'")
        return v


class ForecastVisualizationResponse(BaseModel):
    """Response with visualization data."""
    chart_url: str
    chart_type: str
    data: Dict[str, Any]
