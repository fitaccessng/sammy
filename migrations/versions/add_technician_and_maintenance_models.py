"""add technician and maintenance models

Revision ID: add_tech_maint
Revises: 
Create Date: 2025-11-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_tech_maint'
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Create technicians table
    op.create_table('technicians',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('email', sa.String(length=128), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('specialization', sa.String(length=128), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    
    # Create maintenance_schedules table
    op.create_table('maintenance_schedules',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('asset_id', sa.Integer(), nullable=False),
    sa.Column('technician_id', sa.Integer(), nullable=True),
    sa.Column('maintenance_type', sa.String(length=64), nullable=False),
    sa.Column('scheduled_date', sa.Date(), nullable=False),
    sa.Column('completed_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('cost', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['asset_id'], ['inventory_items.id'], ),
    sa.ForeignKeyConstraint(['technician_id'], ['technicians.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('maintenance_schedules')
    op.drop_table('technicians')
