from models import db
from models.booking import Booking


class BookingService:
    @staticmethod
    def get_booking(booking_id: int) -> Booking | None:
        return db.session.get(Booking, booking_id)

