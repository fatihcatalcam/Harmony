"""Add bio, age, and location columns

Revision ID: 883509d52059
Revises: ffdd1d8c61aa
Create Date: 2025-01-16 18:45:08.009680

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '883509d52059'
down_revision = 'ffdd1d8c61aa'
branch_labels = None
depends_on = None


def upgrade():
    # Yeni sütunları 'user' tablosuna ekle
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bio', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('age', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('location', sa.String(length=100), nullable=True))


def downgrade():
    # Yeni sütunları 'user' tablosundan kaldır
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('location')
        batch_op.drop_column('age')
        batch_op.drop_column('bio')
