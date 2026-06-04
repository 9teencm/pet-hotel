from datetime import datetime

from . import db


class GroomingStatus:
    WAITING = "waiting"        # 等待中
    GROOMING = "grooming"      # 美容中
    DRYING = "drying"          # 乾燥中
    COMPLETED = "completed"    # 已完成


VALID_TRANSITIONS = {
    GroomingStatus.WAITING:   [GroomingStatus.GROOMING],
    GroomingStatus.GROOMING:  [GroomingStatus.DRYING],
    GroomingStatus.DRYING:    [GroomingStatus.COMPLETED],
    GroomingStatus.COMPLETED: [],
}

GROOMING_TYPE_PRICE = {
    "bath":    400,   # 洗澡
    "trim":    600,   # 剪毛
    "full":   1000,   # 大修（洗澡+剪毛+造型）
}


class GroomingService(db.Model):
    __tablename__ = "grooming_services"

    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey("pets.id"), nullable=False, index=True)
    groomer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)  # 指派美容師

    service_type = db.Column(db.String(20), nullable=False, default="bath")  # bath/trim/full
    status = db.Column(db.String(20), nullable=False, default=GroomingStatus.WAITING, index=True)

    appointment_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    # 照片回報（美容師拍照上傳後填入）
    photo_url = db.Column(db.Text, nullable=True)
    photo_message = db.Column(db.String(500), nullable=True)
    photo_uploaded_at = db.Column(db.DateTime, nullable=True)

    # 通知是否已推播給飼主
    owner_notified = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    pet = db.relationship("Pet", back_populates="groomings")
    groomer = db.relationship("User", foreign_keys=[groomer_id])

    def transition_to(self, new_status: str) -> None:
        allowed = VALID_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"美容服務狀態 '{self.status}' 不可直接轉換至 '{new_status}'"
            )
        self.status = new_status

    @property
    def price(self) -> int:
        return GROOMING_TYPE_PRICE.get(self.service_type, 0)
