from sqlalchemy import Column, String, Enum as SQLEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from src.core.database import Base


class TenantType(str, enum.Enum):
    """Tenant type enumeration."""
    CONSULTANT = "consultant"
    ENTERPRISE = "enterprise"


class Tenant(Base):
    """Tenant database model for multi-tenancy."""
    
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    type = Column(SQLEnum(TenantType), nullable=False)
    settings = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant {self.name} ({self.type})>"
