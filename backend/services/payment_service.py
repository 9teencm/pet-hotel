from datetime import datetime

from models import db
from models.payment import Payment, PaymentStatus


class PaymentService:
    @staticmethod
    def mark_paid(payment: Payment) -> Payment:
        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.utcnow()
        db.session.commit()
        return payment

