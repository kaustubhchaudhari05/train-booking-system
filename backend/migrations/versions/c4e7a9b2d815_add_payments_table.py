"""Add payments table

Revision ID: c4e7a9b2d815
Revises: 8b3d6f1a4c92
Create Date: 2026-11-02 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4e7a9b2d815'
down_revision = '8b3d6f1a4c92'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column(
            'provider',
            sa.String(length=20),
            server_default='RAZORPAY',
            nullable=False,
        ),
        sa.Column('provider_order_id', sa.String(length=64), nullable=False),
        sa.Column('provider_payment_id', sa.String(length=64), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            'currency',
            sa.String(length=3),
            server_default='INR',
            nullable=False,
        ),
        sa.Column(
            'status',
            sa.String(length=20),
            server_default='CREATED',
            nullable=False,
        ),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint(
            "provider IN ('RAZORPAY')",
            name='ck_payment_provider',
        ),
        sa.CheckConstraint(
            "status IN ('CREATED', 'PAID', 'FAILED', 'REFUND_PENDING')",
            name='ck_payment_status',
        ),
        sa.CheckConstraint('amount > 0', name='ck_payment_amount'),
        sa.ForeignKeyConstraint(
            ['booking_id'], ['bookings.id'], ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_order_id'),
        sa.UniqueConstraint('provider_payment_id'),
    )

    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_payments_booking_id'), ['booking_id'], unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_payments_status'), ['status'], unique=False
        )


def downgrade():
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_payments_status'))
        batch_op.drop_index(batch_op.f('ix_payments_booking_id'))

    op.drop_table('payments')
