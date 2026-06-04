from datetime import date, datetime

from . import db


class BookingStatus:
    PENDING_REVIEW = "pending_review"
    CONFIRMED      = "confirmed"
    CHECKED_IN     = "checked_in"
    CHECKED_OUT    = "checked_out"
    CANCELLED      = "cancelled"


class Booking(db.Model):
    __tablename__ = "bookings"

    id       = db.Column(db.Integer, primary_key=True)
    userId   = db.Column(db.Integer, db.ForeignKey("users.id"),  nullable=False, index=True)
    petId    = db.Column(db.Integer, db.ForeignKey("pets.id"),   nullable=False, index=True)
    room_id  = db.Column(db.Integer, db.ForeignKey("rooms.id"),  nullable=True,  index=True)

    checkIn  = db.Column(db.Date, nullable=False)
    checkOut = db.Column(db.Date, nullable=False)
    roomCode = db.Column(db.String(20), nullable=True)   # human-readable code e.g. "A101"

    status    = db.Column(db.String(40), nullable=False, default=BookingStatus.PENDING_REVIEW, index=True)
    notes     = db.Column(db.Text, nullable=True)
    createdAt = db.Column(db.DateTime, nullable=False, default=datetime.now)

    user     = db.relationship("User",    back_populates="bookings")
    pet      = db.relationship("Pet",     back_populates="bookings")
    room     = db.relationship("Room",    back_populates="bookings")
    payments = db.relationship("Payment", back_populates="booking", cascade="all, delete-orphan")

    def validate_dates(self) -> None:
        if not isinstance(self.checkIn, date) or not isinstance(self.checkOut, date):
            raise ValueError("checkIn/checkOut must be dates")
        if self.checkOut < self.checkIn:
            raise ValueError("checkOut must be at or after checkIn")

    @staticmethod
    def is_room_available(room_id: int, check_in: date, check_out: date,
                          exclude_id: int | None = None) -> bool:
        """True if no confirmed/pending booking overlaps the requested period."""
        query = db.select(Booking).where(
            Booking.room_id == room_id,
            Booking.status.notin_([BookingStatus.CANCELLED]),
            Booking.checkIn  < check_out,
            Booking.checkOut > check_in,
        )
        if exclude_id:
            query = query.where(Booking.id != exclude_id)
        conflict = db.session.execute(query).scalar_one_or_none()
        return conflict is None
