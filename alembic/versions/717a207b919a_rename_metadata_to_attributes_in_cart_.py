"""rename metadata to attributes in cart and order items

Revision ID: 717a207b919a
Revises: 609ce4fcfdc6
Create Date: 2026-05-01 15:41:06.694685

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '717a207b919a'
down_revision = '609ce4fcfdc6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('cart_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('attributes', sa.JSON(), nullable=True))

    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('attributes', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('order_items', schema=None) as batch_op:
        batch_op.drop_column('attributes')

    with op.batch_alter_table('cart_items', schema=None) as batch_op:
        batch_op.drop_column('attributes')
