from datetime import date, datetime

from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.grooming import GroomingService, GroomingStatus
from models.pet import Pet
from models.user import User

bp = Blueprint("grooming", __name__)


def _current_user():
    uid = int(get_jwt_identity())
    user = db.session.get(User, uid)
    if not user:
        abort(401)
    return user


def _serialize(svc):
    pet = db.session.get(Pet, svc.pet_id)
    return {
        "id": svc.id,
        "pet_id": svc.pet_id,
        "pet_name": pet.name if pet else None,
        "service_type": svc.service_type,
        "status": svc.status,
        "appointment_date": svc.appointment_date.isoformat(),
        "price": svc.price,
        "notes": svc.notes,
        "photo_url": svc.photo_url,
        "photo_message": svc.photo_message,
        "owner_notified": svc.owner_notified,
    }


@bp.post("/")
@jwt_required()
def create_grooming():
    user = _current_user()
    payload = request.get_json(silent=True) or {}

    pet_id = payload.get("pet_id")
    service_type = (payload.get("service_type") or "bath").strip()
    appt_date_str = payload.get("appointment_date")
    notes = (payload.get("notes") or "").strip() or None

    if not pet_id or not appt_date_str:
        return jsonify({"error": "pet_id/appointment_date required"}), 400

    pet = db.session.get(Pet, int(pet_id))
    if not pet or pet.owner_id != user.id:
        return jsonify({"error": "pet not found"}), 404

    try:
        appt_date = date.fromisoformat(appt_date_str)
    except ValueError:
        return jsonify({"error": "invalid appointment_date format (YYYY-MM-DD)"}), 400

    if pet.rabies_vaccine_expiry or pet.combo_vaccine_expiry:
        ok, reason = pet.vaccine_valid(appt_date)
        if not ok:
            return jsonify({"error": reason, "blocked": True}), 422

    svc = GroomingService(  # type: ignore
        pet_id=pet.id,
        service_type=service_type,
        appointment_date=appt_date,
        notes=notes,
    )
    db.session.add(svc)
    db.session.commit()
    return jsonify({"grooming": _serialize(svc)}), 201


@bp.get("/mine")
@jwt_required()
def list_mine():
    user = _current_user()
    pet_ids = [p.id for p in user.pets]
    svcs = db.session.execute(
        db.select(GroomingService).where(GroomingService.pet_id.in_(pet_ids))
        .order_by(GroomingService.id.desc())
    ).scalars().all()
    return jsonify({"groomings": [_serialize(s) for s in svcs]})


@bp.get("/all")
@jwt_required()
def list_all():
    user = _current_user()
    if user.role not in ("groomer", "receptionist", "admin"):
        return jsonify({"error": "forbidden"}), 403
    svcs = db.session.execute(
        db.select(GroomingService).order_by(GroomingService.appointment_date, GroomingService.id)
    ).scalars().all()
    return jsonify({"groomings": [_serialize(s) for s in svcs]})


@bp.post("/<int:svc_id>/transition")
@jwt_required()
def transition(svc_id):
    user = _current_user()
    if user.role not in ("groomer", "admin"):
        return jsonify({"error": "forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    new_status = (payload.get("status") or "").strip()

    svc = db.session.get(GroomingService, svc_id)
    if not svc:
        return jsonify({"error": "not found"}), 404

    try:
        svc.transition_to(new_status)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    if new_status == GroomingStatus.COMPLETED:
        svc.owner_notified = True

    db.session.commit()
    return jsonify({"grooming": _serialize(svc)})


@bp.post("/<int:svc_id>/photo")
@jwt_required()
def upload_photo(svc_id):
    user = _current_user()
    if user.role not in ("groomer", "admin"):
        return jsonify({"error": "forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    photo_url = payload.get("photo_url")
    message = (payload.get("message") or "").strip() or None

    if not photo_url:
        return jsonify({"error": "photo_url required"}), 400

    svc = db.session.get(GroomingService, svc_id)
    if not svc:
        return jsonify({"error": "not found"}), 404

    svc.photo_url = photo_url
    svc.photo_message = message
    svc.photo_uploaded_at = datetime.utcnow()
    svc.owner_notified = True

    db.session.commit()
    return jsonify({"grooming": _serialize(svc)})
