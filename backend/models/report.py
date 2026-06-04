from datetime import datetime
from . import db


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), nullable=False, index=True)
    image_url = db.Column(db.Text, nullable=False)  # base64 data URL or simulated photo path
    message = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship to Booking
    booking = db.relationship("Booking", backref=db.backref("reports", cascade="all, delete-orphan"))
