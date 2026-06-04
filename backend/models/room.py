from datetime import datetime

from . import db


class RoomStatus:
    AVAILABLE = "available"    # 有空床
    RESERVED = "reserved"      # 已預約
    OCCUPIED = "occupied"      # 已入住
    CLEANING = "cleaning"      # 清床中


VALID_TRANSITIONS = {
    RoomStatus.AVAILABLE: [RoomStatus.RESERVED],
    RoomStatus.RESERVED:  [RoomStatus.OCCUPIED, RoomStatus.AVAILABLE],  # 取消可退回
    RoomStatus.OCCUPIED:  [RoomStatus.CLEANING],
    RoomStatus.CLEANING:  [RoomStatus.AVAILABLE],
}

ROOM_TYPE_PRICE = {
    "standard_cat":  600,
    "deluxe_dog":   1200,
    "suite":        1800,
}


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    room_code = db.Column(db.String(20), unique=True, nullable=False)   # e.g. "A101"
    room_type = db.Column(db.String(30), nullable=False)                # standard_cat / deluxe_dog / suite
    status = db.Column(db.String(20), nullable=False, default=RoomStatus.AVAILABLE, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookings = db.relationship("Booking", back_populates="room", cascade="all, delete-orphan")

    def transition_to(self, new_status: str) -> None:
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"房間 {self.room_code} 狀態 '{self.status}' 不可直接轉換至 '{new_status}'"
            )
        self.status = new_status

    @property
    def price_per_night(self) -> int:
        return ROOM_TYPE_PRICE.get(self.room_type, 0)
