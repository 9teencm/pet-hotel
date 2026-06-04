from datetime import date

from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.booking import Booking, BookingStatus
from models.pet import Pet
from models.report import Report
from models.room import Room, RoomStatus
from models.user import User

bp = Blueprint("booking", __name__)


def _current_user():
    uid = int(get_jwt_identity())
    user = db.session.get(User, uid)
    if not user:
        abort(401)
    return user


def _parse_date(value):
    return date.fromisoformat(value)


def _serialize_booking(b):
    pet = db.session.get(Pet, b.petId)
    return {
        "id": b.id,
        "petId": b.petId,
        "petName": pet.name if pet else "未知寵物",
        "petNotes": pet.notes if pet else "",
        "roomCode": b.roomCode,
        "checkIn": b.checkIn.isoformat(),
        "checkOut": b.checkOut.isoformat(),
        "status": b.status,
    }


def _resolve_pet(user, payload):
    pet_id = payload.get("petId") or payload.get("pet_id")
    pet_name = (payload.get("petName") or payload.get("pet_name") or "").strip()

    if pet_id:
        pet = db.session.get(Pet, int(pet_id))
        if not pet or pet.owner_id != user.id:
            return None, (jsonify({"error": "pet not found"}), 404)
        return pet, None

    if pet_name:
        notes = (payload.get("notes") or "").strip() or None
        def _pd(k):
            v = payload.get(k)
            return date.fromisoformat(v) if v else None

        pet = Pet(  # type: ignore
            owner_id=user.id,
            name=pet_name,
            dietary_notes=notes,
            rabies_vaccine_expiry=_pd("rabiesExpiry") or _pd("rabies_vaccine_expiry"),
            combo_vaccine_expiry=_pd("comboExpiry") or _pd("combo_vaccine_expiry"),
        )
        db.session.add(pet)
        db.session.flush()
        return pet, None

    return None, (jsonify({"error": "petId or petName required"}), 400)


@bp.post("/")
@jwt_required()
def create_booking():
    user = _current_user()
    payload = request.get_json(silent=True) or {}

    room_code = (payload.get("roomCode") or payload.get("roomId") or payload.get("room_id") or "").strip()
    check_in_str = payload.get("checkIn") or payload.get("check_in")
    check_out_str = payload.get("checkOut") or payload.get("check_out")

    if not room_code or not check_in_str or not check_out_str:
        return jsonify({"error": "roomCode/checkIn/checkOut required"}), 400

    try:
        check_in = _parse_date(check_in_str)
        check_out = _parse_date(check_out_str)
    except ValueError:
        return jsonify({"error": "invalid date format (YYYY-MM-DD)"}), 400

    if check_out < check_in:
        return jsonify({"error": "checkOut must be at or after checkIn"}), 400

    pet, err = _resolve_pet(user, payload)
    if err:
        return err

    if pet.rabies_vaccine_expiry or pet.combo_vaccine_expiry:
        ok, reason = pet.vaccine_valid(check_in)
        if not ok:
            db.session.rollback()
            return jsonify({"error": reason, "blocked": True}), 422

    room = db.session.execute(db.select(Room).filter_by(room_code=room_code)).scalar_one_or_none()

    room_id_fk = None
    if room:
        if not Booking.is_room_available(room.id, check_in, check_out):
            db.session.rollback()
            return jsonify({"error": "房間 " + room_code + " 在指定日期已被預約，請選擇其他房間或日期"}), 409
        room_id_fk = room.id
        if room.status == RoomStatus.AVAILABLE:
            room.transition_to(RoomStatus.RESERVED)

    notes = (payload.get("notes") or "").strip() or None
    booking = Booking(  # type: ignore
        userId=user.id,
        petId=pet.id,
        room_id=room_id_fk,
        roomCode=room_code,
        checkIn=check_in,
        checkOut=check_out,
        notes=notes,
    )
    db.session.add(booking)
    db.session.commit()
    return jsonify({"booking": _serialize_booking(booking)}), 201


@bp.get("/mine")
@jwt_required()
def list_my_bookings():
    user = _current_user()
    bookings = db.session.execute(
        db.select(Booking).filter_by(userId=user.id).order_by(Booking.id.desc())
    ).scalars().all()
    return jsonify({"bookings": [_serialize_booking(b) for b in bookings]})


@bp.get("/all")
@jwt_required()
def get_all_bookings():
    user = _current_user()
    if user.role not in ("receptionist", "admin", "nanny"):
        return jsonify({"error": "forbidden"}), 403
    bookings = db.session.execute(db.select(Booking).order_by(Booking.id.desc())).scalars().all()
    return jsonify({"bookings": [_serialize_booking(b) for b in bookings]})


@bp.post("/<int:booking_id>/confirm")
@jwt_required()
def confirm_booking_route(booking_id):
    user = _current_user()
    if user.role not in ("receptionist", "admin"):
        return jsonify({"error": "forbidden"}), 403

    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "booking not found"}), 404

    pet = db.session.get(Pet, booking.petId)
    if pet and (pet.rabies_vaccine_expiry or pet.combo_vaccine_expiry):
        ok, reason = pet.vaccine_valid(booking.checkIn)
        if not ok:
            return jsonify({"error": reason, "blocked": True}), 422

    booking.status = BookingStatus.CONFIRMED
    db.session.commit()
    return jsonify({"success": True, "status": booking.status})


@bp.post("/<int:booking_id>/check-in")
@jwt_required()
def check_in_route(booking_id):
    user = _current_user()
    if user.role not in ("receptionist", "admin"):
        return jsonify({"error": "forbidden"}), 403

    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "booking not found"}), 404
    if booking.status != BookingStatus.CONFIRMED:
        return jsonify({"error": "booking must be confirmed before check-in"}), 422

    booking.status = BookingStatus.CHECKED_IN
    if booking.room_id:
        room = db.session.get(Room, booking.room_id)
        if room:
            room.transition_to(RoomStatus.OCCUPIED)
    db.session.commit()
    return jsonify({"success": True, "status": booking.status})


@bp.post("/<int:booking_id>/check-out")
@jwt_required()
def check_out_route(booking_id):
    user = _current_user()
    if user.role not in ("receptionist", "admin"):
        return jsonify({"error": "forbidden"}), 403

    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "booking not found"}), 404
    if booking.status != BookingStatus.CHECKED_IN:
        return jsonify({"error": "booking must be checked_in before check-out"}), 422

    booking.status = BookingStatus.CHECKED_OUT
    if booking.room_id:
        room = db.session.get(Room, booking.room_id)
        if room:
            room.transition_to(RoomStatus.CLEANING)
    db.session.commit()
    return jsonify({"success": True, "status": booking.status})


@bp.post("/<int:booking_id>/report")
@jwt_required()
def create_report(booking_id):
    user = _current_user()
    if user.role not in ("groomer", "nanny", "receptionist", "admin"):
        return jsonify({"error": "forbidden"}), 403

    payload = request.get_json(silent=True) or {}
    image_url = payload.get("image_url")
    message = payload.get("message")

    if not image_url:
        return jsonify({"error": "image_url required"}), 400

    booking = db.session.get(Booking, booking_id)
    if not booking:
        return jsonify({"error": "booking not found"}), 404

    report = Report(booking_id=booking_id, image_url=image_url, message=message)  # type: ignore
    db.session.add(report)
    db.session.commit()

    return jsonify({
        "report": {
            "id": report.id,
            "booking_id": report.booking_id,
            "image_url": report.image_url,
            "message": report.message,
            "created_at": report.created_at.isoformat(),
        }
    }), 201


@bp.get("/<int:booking_id>/reports")
@jwt_required()
def get_reports(booking_id):
    token = None  # JWT already checked by decorator
    reports = Report.query.filter_by(booking_id=booking_id).order_by(Report.created_at.desc()).all()
    return jsonify({
        "reports": [
            {
                "id": r.id,
                "booking_id": r.booking_id,
                "image_url": r.image_url,
                "message": r.message,
                "created_at": r.created_at.isoformat(),
            }
            for r in reports
        ]
    })
