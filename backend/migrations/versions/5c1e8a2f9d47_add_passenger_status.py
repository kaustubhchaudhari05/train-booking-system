"""Add passenger status

Revision ID: 5c1e8a2f9d47
Revises: 238ef4d1cac1
Create Date: 2026-10-31 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c1e8a2f9d47'
down_revision = '238ef4d1cac1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('booking_passengers', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'status',
            sa.String(length=20),
            server_default='ACTIVE',
            nullable=False,
        ))
        batch_op.create_check_constraint(
            'ck_passenger_status',
            "status IN ('ACTIVE', 'CANCELLED')",
        )

    # Passengers of bookings that were already cancelled are cancelled too.
    op.execute(
        "UPDATE booking_passengers SET status = 'CANCELLED' "
        "WHERE booking_id IN "
        "(SELECT id FROM bookings WHERE status = 'CANCELLED')"
    )


def downgrade():
    with op.batch_alter_table('booking_passengers', schema=None) as batch_op:
        batch_op.drop_constraint('ck_passenger_status', type_='check')
        batch_op.drop_column('status')
