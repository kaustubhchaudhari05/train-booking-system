from app.extensions import db


class TrainSchedule(db.Model):
    __tablename__ = "train_schedules"

    id = db.Column(db.Integer, primary_key=True)

    train_id = db.Column(
        db.Integer,
        db.ForeignKey("trains.id", ondelete="CASCADE"),
        nullable=False,
    )

    journey_date = db.Column(db.Date, nullable=False)
    status = db.Column(
        db.String(20),
        nullable=False,
        default="SCHEDULED",
    )

    train = db.relationship("Train")

    __table_args__ = (
        db.UniqueConstraint(
            "train_id",
            "journey_date",
            name="uq_train_schedule_date",
        ),
        db.CheckConstraint(
            "status IN ('SCHEDULED', 'CANCELLED')",
            name="ck_train_schedule_status",
        ),
    )
