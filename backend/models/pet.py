from datetime import date, datetime

from . import db


class Pet(db.Model):
    __tablename__ = "pets"

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    name = db.Column(db.String(120), nullable=False)
    species = db.Column(db.String(50), nullable=True)   # dog / cat / ...
    breed = db.Column(db.String(80), nullable=True)
    weight_kg = db.Column(db.Numeric(6, 2), nullable=True)
    chip_id = db.Column(db.String(30), nullable=True, unique=True)  # 晶片號碼

    # 疫苗有效期（None = 未提供）
    rabies_vaccine_expiry = db.Column(db.Date, nullable=True)
    combo_vaccine_expiry = db.Column(db.Date, nullable=True)

    behavior_tag = db.Column(db.String(20), nullable=True)  # normal / aggressive / shy
    dietary_notes = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    owner = db.relationship("User", back_populates="pets")
    bookings = db.relationship("Booking", back_populates="pet", cascade="all, delete-orphan")
    groomings = db.relationship("GroomingService", back_populates="pet", cascade="all, delete-orphan")

    # ── 疫苗核檢 ──────────────────────────────────────────────
    def vaccine_valid(self, check_date: date | None = None) -> tuple[bool, str]:
        """回傳 (是否通過, 拒絕原因)。check_date 預設為今天。"""
        today = check_date or date.today()

        if self.behavior_tag == "aggressive":
            return False, f"寵物 {self.name} 標記為攻擊性，須人工審核後方可入住"

        if not self.rabies_vaccine_expiry:
            return False, f"未提供 {self.name} 的狂犬病疫苗有效期"
        if self.rabies_vaccine_expiry < today:
            return False, f"{self.name} 的狂犬病疫苗已於 {self.rabies_vaccine_expiry} 過期"

        if not self.combo_vaccine_expiry:
            return False, f"未提供 {self.name} 的混合疫苗有效期"
        if self.combo_vaccine_expiry < today:
            return False, f"{self.name} 的混合疫苗已於 {self.combo_vaccine_expiry} 過期"

        return True, ""
