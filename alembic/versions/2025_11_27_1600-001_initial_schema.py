"""Initial database schema with all tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-11-27 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("CREATE TYPE tenanttype AS ENUM ('consultant', 'enterprise')")
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'consultant', 'entrepreneur')")
    op.execute("CREATE TYPE valuationstatus AS ENUM ('draft', 'in_progress', 'completed', 'archived')")
    op.execute("CREATE TYPE valuationmethod AS ENUM ('ebitda_multiple', 'dcf', 'earnings_value', 'asset_value', 'practitioner')")
    op.execute("CREATE TYPE forecasttype AS ENUM ('revenue', 'ebitda')")
    op.execute("CREATE TYPE forecastmethod AS ENUM ('arima', 'prophet', 'manual')")
    op.execute("CREATE TYPE forecastscenario AS ENUM ('base', 'best', 'worst')")
    op.execute("CREATE TYPE workflowtype AS ENUM ('succession', 'valuation', 'due_diligence')")
    op.execute("CREATE TYPE workflowstatus AS ENUM ('active', 'completed', 'paused', 'cancelled')")
    op.execute("CREATE TYPE phasestatus AS ENUM ('pending', 'in_progress', 'completed', 'skipped')")
    op.execute("CREATE TYPE taskstatus AS ENUM ('pending', 'in_progress', 'completed', 'cancelled')")
    op.execute("CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high', 'urgent')")
    op.execute("CREATE TYPE integrationprovider AS ENUM ('bexio', 'abacus', 'sage', 'datev')")
    op.execute("CREATE TYPE integrationstatus AS ENUM ('active', 'inactive', 'error')")
    op.execute("CREATE TYPE exporttype AS ENUM ('excel', 'pdf')")
    op.execute("CREATE TYPE exportstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
    op.execute("CREATE TYPE auditaction AS ENUM ('create', 'update', 'delete', 'view', 'export')")
    
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', postgresql.ENUM('consultant', 'enterprise', name='tenanttype'), nullable=False),
        sa.Column('settings', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_tenant_type', 'tenants', ['type'])
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('role', postgresql.ENUM('admin', 'consultant', 'entrepreneur', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_user_email', 'users', ['email'], unique=True)
    op.create_index('idx_user_tenant', 'users', ['tenant_id'])
    op.create_index('idx_user_role', 'users', ['role'])
    
    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('industry', sa.String(100), nullable=False),
        sa.Column('founded_year', sa.Integer, nullable=True),
        sa.Column('employees', sa.Integer, nullable=True),
        sa.Column('location', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='RESTRICT'),
        sa.CheckConstraint('founded_year >= 1800', name='check_founded_year'),
        sa.CheckConstraint('employees >= 0', name='check_employees'),
    )
    op.create_index('idx_company_tenant', 'companies', ['tenant_id'])
    op.create_index('idx_company_owner', 'companies', ['owner_id'])
    op.create_index('idx_company_industry', 'companies', ['industry'])
    
    # Create financial_years table
    op.create_table(
        'financial_years',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('revenue', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('ebitda', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('ebit', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('net_income', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('total_assets', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('total_liabilities', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('equity', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('capex', sa.DECIMAL(15, 2), nullable=False, server_default='0'),
        sa.Column('depreciation', sa.DECIMAL(15, 2), nullable=False, server_default='0'),
        sa.Column('working_capital', sa.DECIMAL(15, 2), nullable=False, server_default='0'),
        sa.Column('is_actual', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('company_id', 'year', name='unique_company_year'),
    )
    op.create_index('idx_financial_year_company', 'financial_years', ['company_id'])
    op.create_index('idx_financial_year_year', 'financial_years', ['year'])
    
    # Create valuations table
    op.create_table(
        'valuations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('valuation_date', sa.Date, nullable=False),
        sa.Column('assumptions', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('status', postgresql.ENUM('draft', 'in_progress', 'completed', 'archived', name='valuationstatus'), nullable=False, server_default='draft'),
        sa.Column('final_value', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('final_value_min', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('final_value_max', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False, server_default='CHF'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.CheckConstraint('final_value_min <= final_value', name='check_min_value'),
        sa.CheckConstraint('final_value <= final_value_max', name='check_max_value'),
    )
    op.create_index('idx_valuation_company', 'valuations', ['company_id'])
    op.create_index('idx_valuation_created_by', 'valuations', ['created_by'])
    op.create_index('idx_valuation_status', 'valuations', ['status'])
    op.create_index('idx_valuation_date', 'valuations', ['valuation_date'])
    
    # Create valuation_method_results table
    op.create_table(
        'valuation_method_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('valuation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('method', postgresql.ENUM('ebitda_multiple', 'dcf', 'earnings_value', 'asset_value', 'practitioner', name='valuationmethod'), nullable=False),
        sa.Column('parameters', postgresql.JSONB, nullable=False),
        sa.Column('calculated_value', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('weight', sa.DECIMAL(5, 4), nullable=False, server_default='0'),
        sa.Column('details', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['valuation_id'], ['valuations.id'], ondelete='CASCADE'),
        sa.CheckConstraint('weight >= 0 AND weight <= 1', name='check_weight_range'),
    )
    op.create_index('idx_valuation_method_valuation', 'valuation_method_results', ['valuation_id'])
    op.create_index('idx_valuation_method_method', 'valuation_method_results', ['method'])
    
    # Create sensitivity_analyses table
    op.create_table(
        'sensitivity_analyses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('valuation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('variable_name', sa.String(100), nullable=False),
        sa.Column('base_value', sa.DECIMAL(15, 6), nullable=False),
        sa.Column('min_value', sa.DECIMAL(15, 6), nullable=False),
        sa.Column('max_value', sa.DECIMAL(15, 6), nullable=False),
        sa.Column('step_size', sa.DECIMAL(15, 6), nullable=False),
        sa.Column('results', postgresql.JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['valuation_id'], ['valuations.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_sensitivity_valuation', 'sensitivity_analyses', ['valuation_id'])
    
    # Create forecasts table
    op.create_table(
        'forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('base_year_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('forecast_type', postgresql.ENUM('revenue', 'ebitda', name='forecasttype'), nullable=False),
        sa.Column('years', sa.Integer, nullable=False),
        sa.Column('method', postgresql.ENUM('arima', 'prophet', 'manual', name='forecastmethod'), nullable=False),
        sa.Column('model_parameters', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('confidence_level', sa.DECIMAL(5, 4), nullable=False, server_default='0.95'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['base_year_id'], ['financial_years.id'], ondelete='SET NULL'),
        sa.CheckConstraint('years > 0', name='check_forecast_years'),
        sa.CheckConstraint('confidence_level >= 0 AND confidence_level <= 1', name='check_confidence_level'),
    )
    op.create_index('idx_forecast_company', 'forecasts', ['company_id'])
    op.create_index('idx_forecast_type', 'forecasts', ['forecast_type'])
    
    # Create forecast_predictions table
    op.create_table(
        'forecast_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('forecast_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('year', sa.Integer, nullable=False),
        sa.Column('predicted_value', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('lower_bound', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('upper_bound', sa.DECIMAL(15, 2), nullable=False),
        sa.Column('scenario', postgresql.ENUM('base', 'best', 'worst', name='forecastscenario'), nullable=False, server_default='base'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['forecast_id'], ['forecasts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('forecast_id', 'year', 'scenario', name='unique_forecast_year_scenario'),
        sa.CheckConstraint('lower_bound <= predicted_value', name='check_lower_bound'),
        sa.CheckConstraint('predicted_value <= upper_bound', name='check_upper_bound'),
    )
    op.create_index('idx_forecast_prediction_forecast', 'forecast_predictions', ['forecast_id'])
    op.create_index('idx_forecast_prediction_year', 'forecast_predictions', ['year'])
    
    # Create workflows table
    op.create_table(
        'workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workflow_type', postgresql.ENUM('succession', 'valuation', 'due_diligence', name='workflowtype'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('current_phase', sa.Integer, nullable=False, server_default='1'),
        sa.Column('status', postgresql.ENUM('active', 'completed', 'paused', 'cancelled', name='workflowstatus'), nullable=False, server_default='active'),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('target_completion_date', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    )
    op.create_index('idx_workflow_company', 'workflows', ['company_id'])
    op.create_index('idx_workflow_type', 'workflows', ['workflow_type'])
    op.create_index('idx_workflow_status', 'workflows', ['status'])
    
    # Create workflow_phases table
    op.create_table(
        'workflow_phases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('order_index', sa.Integer, nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'skipped', name='phasestatus'), nullable=False, server_default='pending'),
        sa.Column('start_date', sa.Date, nullable=True),
        sa.Column('completion_date', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('workflow_id', 'order_index', name='unique_workflow_phase_order'),
    )
    op.create_index('idx_workflow_phase_workflow', 'workflow_phases', ['workflow_id'])
    op.create_index('idx_workflow_phase_order', 'workflow_phases', ['order_index'])
    
    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workflow_phase_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'cancelled', name='taskstatus'), nullable=False, server_default='pending'),
        sa.Column('priority', postgresql.ENUM('low', 'medium', 'high', 'urgent', name='taskpriority'), nullable=False, server_default='medium'),
        sa.Column('metadata', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['workflow_phase_id'], ['workflow_phases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_task_phase', 'tasks', ['workflow_phase_id'])
    op.create_index('idx_task_assigned', 'tasks', ['assigned_to'])
    op.create_index('idx_task_status', 'tasks', ['status'])
    op.create_index('idx_task_due_date', 'tasks', ['due_date'])
    
    # Create integration_connections table
    op.create_table(
        'integration_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', postgresql.ENUM('bexio', 'abacus', 'sage', 'datev', name='integrationprovider'), nullable=False),
        sa.Column('access_token', sa.Text, nullable=False),
        sa.Column('refresh_token', sa.Text, nullable=False),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('configuration', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('status', postgresql.ENUM('active', 'inactive', 'error', name='integrationstatus'), nullable=False, server_default='active'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
        sa.UniqueConstraint('company_id', 'provider', name='unique_company_provider'),
    )
    op.create_index('idx_integration_company', 'integration_connections', ['company_id'])
    op.create_index('idx_integration_provider', 'integration_connections', ['provider'])
    
    # Create exports table
    op.create_table(
        'exports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('valuation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('export_type', postgresql.ENUM('excel', 'pdf', name='exporttype'), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer, nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='exportstatus'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['valuation_id'], ['valuations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='RESTRICT'),
    )
    op.create_index('idx_export_valuation', 'exports', ['valuation_id'])
    op.create_index('idx_export_created_by', 'exports', ['created_by'])
    op.create_index('idx_export_status', 'exports', ['status'])
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', postgresql.ENUM('create', 'update', 'delete', 'view', 'export', name='auditaction'), nullable=False),
        sa.Column('changes', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_tenant', 'audit_logs', ['tenant_id'])
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('exports')
    op.drop_table('integration_connections')
    op.drop_table('tasks')
    op.drop_table('workflow_phases')
    op.drop_table('workflows')
    op.drop_table('forecast_predictions')
    op.drop_table('forecasts')
    op.drop_table('sensitivity_analyses')
    op.drop_table('valuation_method_results')
    op.drop_table('valuations')
    op.drop_table('financial_years')
    op.drop_table('companies')
    op.drop_table('users')
    op.drop_table('tenants')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS auditaction")
    op.execute("DROP TYPE IF EXISTS exportstatus")
    op.execute("DROP TYPE IF EXISTS exporttype")
    op.execute("DROP TYPE IF EXISTS integrationstatus")
    op.execute("DROP TYPE IF EXISTS integrationprovider")
    op.execute("DROP TYPE IF EXISTS taskpriority")
    op.execute("DROP TYPE IF EXISTS taskstatus")
    op.execute("DROP TYPE IF EXISTS phasestatus")
    op.execute("DROP TYPE IF EXISTS workflowstatus")
    op.execute("DROP TYPE IF EXISTS workflowtype")
    op.execute("DROP TYPE IF EXISTS forecastscenario")
    op.execute("DROP TYPE IF EXISTS forecastmethod")
    op.execute("DROP TYPE IF EXISTS forecasttype")
    op.execute("DROP TYPE IF EXISTS valuationmethod")
    op.execute("DROP TYPE IF EXISTS valuationstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS tenanttype")
