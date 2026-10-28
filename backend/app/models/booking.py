
from app.extensions import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)

    booking_reference = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    train_schedule_id = db.Column(
        db.Integer,
        db.ForeignKey("train_schedules.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    source_station_id = db.Column(
        db.Integer,
        db.ForeignKey("stations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    destination_station_id = db.Column(
        db.Integer,
        db.ForeignKey("stations.id", ondelete="RESTRICT"),
        nullable=False,
    )

    source_stop_order = db.Column(db.Integer, nullable=False)
    destination_stop_order = db.Column(db.Integer, nullable=False)

    coach_class = db.Column(db.String(2), nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="PENDING",
        index=True,
    )

    total_amount = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0,
    )

    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        nullable=False,
    )

    train_schedule = db.relationship("TrainSchedule")
    source_station = db.relationship(
        "Station",
        foreign_keys=[source_station_id],
    )
    destination_station = db.relationship(
        "Station",
        foreign_keys=[destination_station_id],
    )

    passengers = db.relationship(
        "BookingPassenger",
        back_populates="booking",
        cascade="all, delete-orphan",
        order_by="BookingPassenger.id",
    )

    __table_args__ = (
        db.CheckConstraint(
            "source_stop_order < destination_stop_order",
            name="ck_booking_route_order",
        ),
        db.CheckConstraint(
            "coach_class IN ('SL', '3A', '2A', '1A')",
            name="ck_booking_coach_class",
        ),
        db.CheckConstraint(
            "status IN "
            "('PENDING', 'CONFIRMED', 'WAITLISTED', "
            "'CANCELLED', 'EXPIRED', 'PAYMENT_FAILED')",
            name="ck_booking_status",
        ),
        db.CheckConstraint(
            "total_amount >= 0",
            name="ck_booking_total_amount",
        ),
    )
