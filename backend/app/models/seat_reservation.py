from app.extensions import db


class SeatReservation(db.Model):
    __tablename__ = "seat_reservations"

    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    booking_passenger_id = db.Column(
        db.Integer,
        db.ForeignKey("booking_passengers.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    seat_id = db.Column(
        db.Integer,
        db.ForeignKey("seats.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Inclusive origin stop, exclusive destination stop.
    # Example: NGP -> WR is [1, 2).
    source_stop_order = db.Column(db.Integer, nullable=False)
    destination_stop_order = db.Column(db.Integer, nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default="HELD",
        index=True,
    )

    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        nullable=False,
    )

    booking = db.relationship("Booking")
    passenger = db.relationship("BookingPassenger")
    seat = db.relationship("Seat")

    __table_args__ = (
        db.CheckConstraint(
            "source_stop_order < destination_stop_order",
            name="ck_reservation_route_order",
        ),
        db.CheckConstraint(
            "status IN ('HELD', 'CONFIRMED', 'CANCELLED', 'EXPIRED')",
            name="ck_reservation_status",
        ),
    )
