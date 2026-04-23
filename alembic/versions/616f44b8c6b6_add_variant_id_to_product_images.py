"""add_variant_id_to_product_images

Revision ID: 616f44b8c6b6
Revises: adceb3b886e3
Create Date: 2026-04-21 21:23:08.835068

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision = '616f44b8c6b6'
down_revision = 'adceb3b886e3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('product_images') as batch_op:
        batch_op.add_column(sa.Column('variant_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_product_images_variant_id'), ['variant_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_product_images_variant_id_variants',
            'variants',
            ['variant_id'],
            ['id'],
            ondelete='SET NULL'
        )

def downgrade() -> None:
    with op.batch_alter_table('product_images') as batch_op:
        batch_op.drop_constraint('fk_product_images_variant_id_variants', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_product_images_variant_id'))
        batch_op.drop_column('variant_id')
