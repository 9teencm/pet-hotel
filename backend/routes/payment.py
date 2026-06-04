from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.booking import Booking
from models.payment import Payment, PaymentStatus

bp = Blueprint("payment", __name__)


@bp.post("/create")
@jwt_required()
def create_payment():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}

    booking_id = payload.get("booking_id")
    amount_twd = payload.get("amount_twd")
    provider = (payload.get("provider") or "manual").strip()

    if not booking_id or not amount_twd:
        return jsonify({"error": "booking_id/amount_twd required"}), 400

    booking = db.session.get(Booking, int(booking_id))
    if not booking or booking.userId != user_id:
        return jsonify({"error": "booking not found"}), 404

    payment = Payment(booking_id=booking.id, amount_twd=int(amount_twd), provider=provider)  # type: ignore
    db.session.add(payment)
    db.session.commit()

    return jsonify({"payment": {"id": payment.id, "status": payment.status, "amount_twd": payment.amount_twd}}), 201


@bp.post("/mark-paid")
@jwt_required()
def mark_paid():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}

    payment_id = payload.get("payment_id")
    if not payment_id:
        return jsonify({"error": "payment_id required"}), 400

    payment = db.session.get(Payment, int(payment_id))
    if not payment:
        return jsonify({"error": "payment not found"}), 404

    booking = db.session.get(Booking, payment.booking_id)
    if not booking or booking.userId != user_id:
        return jsonify({"error": "not allowed"}), 403

    payment.status = PaymentStatus.PAID
    payment.paid_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()

    return jsonify({"payment": {"id": payment.id, "status": payment.status, "paid_at": payment.paid_at.isoformat()}})

