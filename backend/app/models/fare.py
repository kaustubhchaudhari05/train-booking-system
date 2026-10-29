from app.extensions import db


class Fare(db.Model):
    __tablename__ = "fares"

    id = db.Column(db.Integer, primary_key=True)

    coach_class = db.Column(db.String(2), nullable=False)
    fare_per_km = db.Column(db.Numeric(10, 2), nullable=False)
    minimum_fare = db.Column(
        db.Numeric(10, 2),
        nullable=False,
        default=0,
    )

    __table_args__ = (
        db.UniqueConstraint(
            "coach_class",
            name="uq_fare_coach_class",
        ),
        db.CheckConstraint(
            "coach_class IN ('SL', '3A', '2A', '1A')",
            name="ck_fare_coach_class",
        ),
        db.CheckConstraint(
            "fare_per_km >= 0",
            name="ck_fare_per_km",
        ),
        db.CheckConstraint(
            "minimum_fare >= 0",
            name="ck_fare_minimum",
        ),
    )
