from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from src.core.database import Base


class Company(Base):
    """Company database model."""
    
    __tablename__ = "companies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=False, index=True)
    founded_year = Column(Integer, CheckConstraint('founded_year >= 1800'), nullable=True)
    employees = Column(Integer, CheckConstraint('employees >= 0'), nullable=True)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="companies")
    owner = relationship("User", back_populates="owned_companies", foreign_keys=[owner_id])
    financial_years = relationship("FinancialYear", back_populates="company", cascade="all, delete-orphan")
    valuations = relationship("Valuation", back_populates="company", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="company", cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="company", cascade="all, delete-orphan")
    integrations = relationship("IntegrationConnection", back_populates="company", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Company {self.name}>"
