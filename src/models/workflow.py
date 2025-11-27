from sqlalchemy import Column, String, Text, Integer, Date, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from src.core.database import Base


class WorkflowType(str, enum.Enum):
    """Workflow type enumeration."""
    SUCCESSION = "succession"
    VALUATION = "valuation"
    DUE_DILIGENCE = "due_diligence"


class WorkflowStatus(str, enum.Enum):
    """Workflow status enumeration."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class PhaseStatus(str, enum.Enum):
    """Workflow phase status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Workflow(Base):
    """Workflow database model for structured processes."""
    
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    workflow_type = Column(SQLEnum(WorkflowType), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    current_phase = Column(Integer, nullable=False, default=1)
    status = Column(SQLEnum(WorkflowStatus), nullable=False, default=WorkflowStatus.ACTIVE, index=True)
    start_date = Column(Date, nullable=False)
    target_completion_date = Column(Date, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    company = relationship("Company", back_populates="workflows")
    creator = relationship("User", back_populates="created_workflows", foreign_keys=[created_by])
    phases = relationship("WorkflowPhase", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowPhase.order_index")
    
    def __repr__(self):
        return f"<Workflow {self.name} - {self.status}>"


class WorkflowPhase(Base):
    """Workflow phase database model."""
    
    __tablename__ = "workflow_phases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, index=True)
    status = Column(SQLEnum(PhaseStatus), nullable=False, default=PhaseStatus.PENDING)
    start_date = Column(Date, nullable=True)
    completion_date = Column(Date, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    workflow = relationship("Workflow", back_populates="phases")
    tasks = relationship("Task", back_populates="phase", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('workflow_id', 'order_index', name='unique_workflow_phase_order'),
    )
    
    def __repr__(self):
        return f"<WorkflowPhase {self.name} - {self.status}>"


class Task(Base):
    """Task database model for workflow tasks."""
    
    __tablename__ = "tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_phase_id = Column(UUID(as_uuid=True), ForeignKey("workflow_phases.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True, index=True)
    status = Column(SQLEnum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True)
    priority = Column(SQLEnum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    metadata = Column(JSONB, nullable=False, default=dict, server_default='{}')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    phase = relationship("WorkflowPhase", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<Task {self.title} - {self.status}>"
