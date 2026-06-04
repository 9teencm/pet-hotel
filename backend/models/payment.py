from datetime import datetime

from . import db


class PaymentStatus:
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, index=True)

    amount_twd = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), nullable=False, default=PaymentStatus.CREATED, index=True)
    provider = db.Column(db.String(50), nullable=True)  # e.g. "linepay", "ecpay", "manual"
    provider_ref = db.Column(db.String(120), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)

    booking = db.relationship("Booking", back_populates="payments")

