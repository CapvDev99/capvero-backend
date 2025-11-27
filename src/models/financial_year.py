from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, DECIMAL, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from src.core.database import Base


class FinancialYear(Base):
    """Financial year database model for storing company financial data."""
    
    __tablename__ = "financial_years"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    
    # Income Statement
    revenue = Column(DECIMAL(15, 2), nullable=False)
    ebitda = Column(DECIMAL(15, 2), nullable=False)
    ebit = Column(DECIMAL(15, 2), nullable=False)
    net_income = Column(DECIMAL(15, 2), nullable=False)
    
    # Balance Sheet
    total_assets = Column(DECIMAL(15, 2), nullable=False)
    total_liabilities = Column(DECIMAL(15, 2), nullable=False)
    equity = Column(DECIMAL(15, 2), nullable=False)
    
    # Cash Flow Statement
    capex = Column(DECIMAL(15, 2), nullable=False, default=0, server_default='0')
    depreciation = Column(DECIMAL(15, 2), nullable=False, default=0, server_default='0')
    working_capital = Column(DECIMAL(15, 2), nullable=False, default=0, server_default='0')
    
    # Metadata
    is_actual = Column(Boolean, nullable=False, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="financial_years")
    forecasts = relationship("Forecast", back_populates="base_year", foreign_keys="Forecast.base_year_id")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('company_id', 'year', name='unique_company_year'),
    )
    
    def __repr__(self):
        return f"<FinancialYear {self.year} for Company {self.company_id}>"
    
    @property
    def ebitda_margin(self):
        """Calculate EBITDA margin as percentage."""
        if self.revenue and self.revenue != 0:
            return (self.ebitda / self.revenue) * 100
        return 0
    
    @property
    def free_cash_flow(self):
        """Calculate Free Cash Flow (FCF)."""
        return self.ebitda - self.capex - self.working_capital
