from app.extensions import db


class Coach(db.Model):
    __tablename__ = "coaches"

    id = db.Column(db.Integer, primary_key=True)

    train_id = db.Column(
        db.Integer,
        db.ForeignKey("trains.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    coach_number = db.Column(db.String(10), nullable=False)
    coach_class = db.Column(db.String(2), nullable=False)

    seats = db.relationship(
        "Seat",
        back_populates="coach",
        cascade="all, delete-orphan",
        order_by="Seat.seat_number",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "train_id", "coach_number",
            name="uq_coach_train_number",
        ),
        db.CheckConstraint(
            "coach_class IN ('SL', '3A', '2A', '1A')",
            name="ck_coach_class",
        ),
    )
