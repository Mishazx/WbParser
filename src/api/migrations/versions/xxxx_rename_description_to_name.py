"""rename_description_to_name

Revision ID: xxxx
Revises: 
Create Date: 2024-01-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'xxxx'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.alter_column('api_keys', 'description',
                    new_column_name='name',
                    existing_type=sa.String())

def downgrade() -> None:
    op.alter_column('api_keys', 'name',
                    new_column_name='description',
                    existing_type=sa.String()) 