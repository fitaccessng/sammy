"""Add project_id ForeignKey to Schedule for Project relationship

Revision ID: c172741d8c1d
Revises: 7f7b783a5c2a
Create Date: 2025-09-17 12:35:59.686654

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c172741d8c1d'
down_revision = '7f7b783a5c2a'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old schedules table
    op.drop_table('schedules')
    # Recreate schedules table with project_id foreign key
    op.create_table(
        'schedules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=128), nullable=False),
        sa.Column('description', sa.String(length=255)),
        sa.Column('type', sa.String(length=50)),
        sa.Column('status', sa.String(length=50)),
        sa.Column('start_time', sa.DateTime()),
        sa.Column('end_time', sa.DateTime()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_table('schedules')
    # ### end Alembic commands ###
