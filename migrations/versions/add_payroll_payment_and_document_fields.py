"""Add payroll payment and document fields

Revision ID: add_payroll_docs_fields
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_payroll_docs_fields'
down_revision = '1b6e992f12df'  # Latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Add new fields to PayrollApproval table
    with op.batch_alter_table('payroll_approval', schema=None) as batch_op:
        batch_op.add_column(sa.Column('finance_comments', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('paid_by', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('paid_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('payment_reference', sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column('payment_notes', sa.Text(), nullable=True))
        batch_op.create_foreign_key('fk_payroll_approval_paid_by', 'user', ['paid_by'], ['id'])
    
    # Add new fields to Document table
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('original_name', sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column('description', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('file_type', sa.String(length=10), nullable=True))


def downgrade():
    # Remove fields from Document table
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_column('file_type')
        batch_op.drop_column('description')
        batch_op.drop_column('original_name')
    
    # Remove fields from PayrollApproval table
    with op.batch_alter_table('payroll_approval', schema=None) as batch_op:
        batch_op.drop_constraint('fk_payroll_approval_paid_by', type_='foreignkey')
        batch_op.drop_column('payment_notes')
        batch_op.drop_column('payment_reference')
        batch_op.drop_column('paid_at')
        batch_op.drop_column('paid_by')
        batch_op.drop_column('finance_comments')
