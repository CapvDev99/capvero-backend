from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, DECIMAL, Enum as SQLEnum, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from src.core.database import Base


class ForecastType(str, enum.Enum):
    """Forecast type enumeration."""
    REVENUE = "revenue"
    EBITDA = "ebitda"


class ForecastMethod(str, enum.Enum):
    """Forecast method enumeration."""
    ARIMA = "arima"
    PROPHET = "prophet"
    MANUAL = "manual"


class ForecastScenario(str, enum.Enum):
    """Forecast scenario enumeration."""
    BASE = "base"
    BEST = "best"
    WORST = "worst"


class Forecast(Base):
    """Forecast database model for AI-based predictions."""
    
    __tablename__ = "forecasts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    base_year_id = Column(UUID(as_uuid=True), ForeignKey("financial_years.id", ondelete="SET NULL"), nullable=True)
    
    forecast_type = Column(SQLEnum(ForecastType), nullable=False, index=True)
    years = Column(Integer, CheckConstraint('years > 0'), nullable=False)
    method = Column(SQLEnum(ForecastMethod), nullable=False)
    model_parameters = Column(JSONB, nullable=False, default=dict, server_default='{}')
    confidence_level = Column(DECIMAL(5, 4), CheckConstraint('confidence_level >= 0 AND confidence_level <= 1'), nullable=False, default=0.95)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="forecasts")
    creator = relationship("User", back_populates="created_forecasts", foreign_keys=[created_by])
    base_year = relationship("FinancialYear", back_populates="forecasts", foreign_keys=[base_year_id])
    predictions = relationship("ForecastPrediction", back_populates="forecast", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Forecast {self.forecast_type} - {self.method}>"


class ForecastPrediction(Base):
    """Forecast prediction database model for individual year predictions."""
    
    __tablename__ = "forecast_predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    forecast_id = Column(UUID(as_uuid=True), ForeignKey("forecasts.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    predicted_value = Column(DECIMAL(15, 2), nullable=False)
    lower_bound = Column(DECIMAL(15, 2), nullable=False)
    upper_bound = Column(DECIMAL(15, 2), nullable=False)
    scenario = Column(SQLEnum(ForecastScenario), nullable=False, default=ForecastScenario.BASE)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    forecast = relationship("Forecast", back_populates="predictions")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('forecast_id', 'year', 'scenario', name='unique_forecast_year_scenario'),
        CheckConstraint('lower_bound <= predicted_value', name='check_lower_bound'),
        CheckConstraint('predicted_value <= upper_bound', name='check_upper_bound'),
    )
    
    def __repr__(self):
        return f"<ForecastPrediction {self.year} = {self.predicted_value}>"
