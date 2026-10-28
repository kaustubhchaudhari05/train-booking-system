from app.extensions import db


class BookingPassenger(db.Model):
    __tablename__ = "booking_passengers"

    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    passenger_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)

    berth_preference = db.Column(
        db.String(20),
        nullable=False,
        default="NO_PREFERENCE",
    )

    booking = db.relationship(
        "Booking",
        back_populates="passengers",
    )

    __table_args__ = (
        db.CheckConstraint(
            "age BETWEEN 0 AND 120",
            name="ck_passenger_age",
        ),
        db.CheckConstraint(
            "gender IN ('MALE', 'FEMALE', 'OTHER')",
            name="ck_passenger_gender",
        ),
        db.CheckConstraint(
            "berth_preference IN "
            "('NO_PREFERENCE', 'LOWER', 'MIDDLE', 'UPPER', "
            "'SIDE_LOWER', 'SIDE_UPPER')",
            name="ck_passenger_berth_preference",
        ),
    )
