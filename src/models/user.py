from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from src.core.database import Base


class UserRole(str, enum.Enum):
    """User role enumeration."""
    ADMIN = "admin"
    CONSULTANT = "consultant"
    ENTREPRENEUR = "entrepreneur"


class User(Base):
    """User database model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.ENTREPRENEUR)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    owned_companies = relationship("Company", back_populates="owner", foreign_keys="Company.owner_id")
    created_valuations = relationship("Valuation", back_populates="creator", foreign_keys="Valuation.created_by")
    created_workflows = relationship("Workflow", back_populates="creator", foreign_keys="Workflow.created_by")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assigned_to")
    created_forecasts = relationship("Forecast", back_populates="creator", foreign_keys="Forecast.created_by")
    created_integrations = relationship("IntegrationConnection", back_populates="creator", foreign_keys="IntegrationConnection.created_by")
    created_exports = relationship("Export", back_populates="creator", foreign_keys="Export.created_by")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
