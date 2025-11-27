from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from src.core.database import Base


class IntegrationProvider(str, enum.Enum):
    """Integration provider enumeration."""
    BEXIO = "bexio"
    ABACUS = "abacus"
    SAGE = "sage"
    DATEV = "datev"


class IntegrationStatus(str, enum.Enum):
    """Integration status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class ExportType(str, enum.Enum):
    """Export type enumeration."""
    EXCEL = "excel"
    PDF = "pdf"


class ExportStatus(str, enum.Enum):
    """Export status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class IntegrationConnection(Base):
    """Integration connection database model for external accounting systems."""
    
    __tablename__ = "integration_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    provider = Column(SQLEnum(IntegrationProvider), nullable=False, index=True)
    
    # OAuth Tokens (should be encrypted in production)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Configuration
    configuration = Column(JSONB, nullable=False, default=dict, server_default='{}')
    status = Column(SQLEnum(IntegrationStatus), nullable=False, default=IntegrationStatus.ACTIVE)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="integrations")
    creator = relationship("User", back_populates="created_integrations", foreign_keys=[created_by])
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('company_id', 'provider', name='unique_company_provider'),
    )
    
    def __repr__(self):
        return f"<IntegrationConnection {self.provider} - {self.status}>"


class Export(Base):
    """Export database model for generated files."""
    
    __tablename__ = "exports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    valuation_id = Column(UUID(as_uuid=True), ForeignKey("valuations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    export_type = Column(SQLEnum(ExportType), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    status = Column(SQLEnum(ExportStatus), nullable=False, default=ExportStatus.PENDING, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    valuation = relationship("Valuation", back_populates="exports")
    creator = relationship("User", back_populates="created_exports", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<Export {self.file_name} - {self.status}>"
