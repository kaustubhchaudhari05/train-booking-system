"""Add users and booking owner

Revision ID: e2a5c8f1b374
Revises: c4e7a9b2d815
Create Date: 2026-11-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2a5c8f1b374'
down_revision = 'c4e7a9b2d815'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_users_email'), ['email'], unique=True
        )

    # Existing bookings have no owner and stay that way.
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_bookings_user_id'), ['user_id'], unique=False
        )
        batch_op.create_foreign_key(
            'fk_bookings_user_id_users',
            'users',
            ['user_id'],
            ['id'],
            ondelete='RESTRICT',
        )


def downgrade():
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_constraint('fk_bookings_user_id_users', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_bookings_user_id'))
        batch_op.drop_column('user_id')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
