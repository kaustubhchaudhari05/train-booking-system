from app.extensions import db


class Train(db.Model):
    __tablename__ = "trains"

    id = db.Column(db.Integer, primary_key=True)
    train_number = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    running_days = db.Column(db.JSON, nullable=False, default=list)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    routes = db.relationship(
        "TrainRoute",
        back_populates="train",
        cascade="all, delete-orphan",
        order_by="TrainRoute.stop_order",
    )

    def __repr__(self):
        return f"<Train {self.train_number}: {self.name}>"
