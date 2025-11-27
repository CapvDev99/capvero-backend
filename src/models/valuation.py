from sqlalchemy import Column, String, Date, DateTime, ForeignKey, DECIMAL, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from src.core.database import Base


class ValuationStatus(str, enum.Enum):
    """Valuation status enumeration."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ValuationMethod(str, enum.Enum):
    """Valuation method enumeration."""
    EBITDA_MULTIPLE = "ebitda_multiple"
    DCF = "dcf"
    EARNINGS_VALUE = "earnings_value"
    ASSET_VALUE = "asset_value"
    PRACTITIONER = "practitioner"


class Valuation(Base):
    """Valuation database model."""
    
    __tablename__ = "valuations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    valuation_date = Column(Date, nullable=False, index=True)
    assumptions = Column(JSONB, nullable=False, default=dict, server_default='{}')
    status = Column(SQLEnum(ValuationStatus), nullable=False, default=ValuationStatus.DRAFT, index=True)
    
    # Final Results
    final_value = Column(DECIMAL(15, 2), nullable=True)
    final_value_min = Column(DECIMAL(15, 2), nullable=True)
    final_value_max = Column(DECIMAL(15, 2), nullable=True)
    currency = Column(String(3), nullable=False, default='CHF')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="valuations")
    creator = relationship("User", back_populates="created_valuations", foreign_keys=[created_by])
    method_results = relationship("ValuationMethodResult", back_populates="valuation", cascade="all, delete-orphan")
    sensitivity_analyses = relationship("SensitivityAnalysis", back_populates="valuation", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="valuation", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('final_value_min <= final_value', name='check_min_value'),
        CheckConstraint('final_value <= final_value_max', name='check_max_value'),
    )
    
    def __repr__(self):
        return f"<Valuation {self.name} - {self.status}>"


class ValuationMethodResult(Base):
    """Valuation method result database model."""
    
    __tablename__ = "valuation_method_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    valuation_id = Column(UUID(as_uuid=True), ForeignKey("valuations.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(SQLEnum(ValuationMethod), nullable=False, index=True)
    parameters = Column(JSONB, nullable=False, default=dict)
    calculated_value = Column(DECIMAL(15, 2), nullable=False)
    weight = Column(DECIMAL(5, 4), CheckConstraint('weight >= 0 AND weight <= 1'), nullable=False, default=0)
    details = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    valuation = relationship("Valuation", back_populates="method_results")
    
    def __repr__(self):
        return f"<ValuationMethodResult {self.method} = {self.calculated_value}>"


class SensitivityAnalysis(Base):
    """Sensitivity analysis database model."""
    
    __tablename__ = "sensitivity_analyses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    valuation_id = Column(UUID(as_uuid=True), ForeignKey("valuations.id", ondelete="CASCADE"), nullable=False, index=True)
    variable_name = Column(String(100), nullable=False)
    base_value = Column(DECIMAL(15, 6), nullable=False)
    min_value = Column(DECIMAL(15, 6), nullable=False)
    max_value = Column(DECIMAL(15, 6), nullable=False)
    step_size = Column(DECIMAL(15, 6), nullable=False)
    results = Column(JSONB, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    valuation = relationship("Valuation", back_populates="sensitivity_analyses")
    
    def __repr__(self):
        return f"<SensitivityAnalysis {self.variable_name}>"
