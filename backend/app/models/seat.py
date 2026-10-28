from app.extensions import db


class Seat(db.Model):
    __tablename__ = "seats"

    id = db.Column(db.Integer, primary_key=True)

    coach_id = db.Column(
        db.Integer,
        db.ForeignKey("coaches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    seat_number = db.Column(db.String(10), nullable=False)
    berth_type = db.Column(db.String(20), nullable=False)

    coach = db.relationship("Coach", back_populates="seats")

    __table_args__ = (
        db.UniqueConstraint(
            "coach_id", "seat_number",
            name="uq_seat_coach_number",
        ),
        db.CheckConstraint(
            "berth_type IN "
            "('LOWER', 'MIDDLE', 'UPPER', "
            "'SIDE_LOWER', 'SIDE_UPPER', 'SEAT')",
            name="ck_seat_berth_type",
        ),
    )
