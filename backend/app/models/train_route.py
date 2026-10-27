from app.extensions import db


class TrainRoute(db.Model):
    __tablename__ = "train_routes"

    id = db.Column(db.Integer, primary_key=True)

    train_id = db.Column(
        db.Integer,
        db.ForeignKey("trains.id", ondelete="CASCADE"),
        nullable=False,
    )

    station_id = db.Column(
        db.Integer,
        db.ForeignKey("stations.id"),
        nullable=False,
    )

    stop_order = db.Column(db.Integer, nullable=False)
    arrival_time = db.Column(db.Time, nullable=True)
    departure_time = db.Column(db.Time, nullable=True)
    distance_km = db.Column(db.Numeric(8, 2), nullable=False, default=0)

    train = db.relationship("Train", back_populates="routes")
    station = db.relationship("Station")

    __table_args__ = (
        db.UniqueConstraint(
            "train_id",
            "stop_order",
            name="uq_train_route_stop_order",
        ),
    )
