from app.extensions import db


class Payment(db.Model):
    """One payment attempt (a Razorpay order) for a booking."""

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    provider = db.Column(
        db.String(20),
        nullable=False,
        default="RAZORPAY",
        server_default="RAZORPAY",
    )

    provider_order_id = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
    )

    provider_payment_id = db.Column(
        db.String(64),
        unique=True,
        nullable=True,
    )

    amount = db.Column(db.Numeric(10, 2), nullable=False)

    currency = db.Column(
        db.String(3),
        nullable=False,
        default="INR",
        server_default="INR",
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="CREATED",
        server_default="CREATED",
        index=True,
    )

    failure_reason = db.Column(db.String(255), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    booking = db.relationship("Booking")

    __table_args__ = (
        db.CheckConstraint(
            "provider IN ('RAZORPAY')",
            name="ck_payment_provider",
        ),
        db.CheckConstraint(
            "status IN ('CREATED', 'PAID', 'FAILED', 'REFUND_PENDING')",
            name="ck_payment_status",
        ),
        db.CheckConstraint(
            "amount > 0",
            name="ck_payment_amount",
        ),
    )
