"""Add WAITLISTED passenger status

Revision ID: 8b3d6f1a4c92
Revises: 5c1e8a2f9d47
Create Date: 2026-11-02 11:00:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '8b3d6f1a4c92'
down_revision = '5c1e8a2f9d47'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('booking_passengers', schema=None) as batch_op:
        batch_op.drop_constraint('ck_passenger_status', type_='check')
        batch_op.create_check_constraint(
            'ck_passenger_status',
            "status IN ('ACTIVE', 'WAITLISTED', 'CANCELLED')",
        )


def downgrade():
    # Waitlisted passengers have no seat; treat them as cancelled.
    op.execute(
        "UPDATE booking_passengers SET status = 'CANCELLED' "
        "WHERE status = 'WAITLISTED'"
    )

    with op.batch_alter_table('booking_passengers', schema=None) as batch_op:
        batch_op.drop_constraint('ck_passenger_status', type_='check')
        batch_op.create_check_constraint(
            'ck_passenger_status',
            "status IN ('ACTIVE', 'CANCELLED')",
        )
