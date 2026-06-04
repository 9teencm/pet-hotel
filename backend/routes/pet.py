from datetime import date

from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.pet import Pet
from models.user import User

bp = Blueprint("pet", __name__)


def _current_user():
    uid = int(get_jwt_identity())
    user = db.session.get(User, uid)
    if not user:
        abort(401)
    return user


def _serialize(pet):
    return {
        "id": pet.id,
        "name": pet.name,
        "species": pet.species,
        "breed": pet.breed,
        "weight_kg": float(pet.weight_kg) if pet.weight_kg else None,
        "chip_id": pet.chip_id,
        "rabies_vaccine_expiry": pet.rabies_vaccine_expiry.isoformat() if pet.rabies_vaccine_expiry else None,
        "combo_vaccine_expiry": pet.combo_vaccine_expiry.isoformat() if pet.combo_vaccine_expiry else None,
        "behavior_tag": pet.behavior_tag,
        "dietary_notes": pet.dietary_notes,
        "notes": pet.notes,
    }


@bp.get("/mine")
@jwt_required()
def list_mine():
    user = _current_user()
    return jsonify({"pets": [_serialize(p) for p in user.pets]})


@bp.post("/")
@jwt_required()
def create_pet():
    user = _current_user()
    payload = request.get_json(silent=True) or {}

    name = (payload.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400

    def _pd(k):
        v = payload.get(k)
        return date.fromisoformat(v) if v else None

    pet = Pet(  # type: ignore
        owner_id=user.id,
        name=name,
        species=(payload.get("species") or "").strip() or None,
        breed=(payload.get("breed") or "").strip() or None,
        weight_kg=payload.get("weight_kg"),
        chip_id=(payload.get("chip_id") or "").strip() or None,
        rabies_vaccine_expiry=_pd("rabies_vaccine_expiry"),
        combo_vaccine_expiry=_pd("combo_vaccine_expiry"),
        behavior_tag=(payload.get("behavior_tag") or "normal").strip(),
        dietary_notes=(payload.get("dietary_notes") or "").strip() or None,
        notes=(payload.get("notes") or "").strip() or None,
    )
    db.session.add(pet)
    db.session.commit()
    return jsonify({"pet": _serialize(pet)}), 201


@bp.put("/<int:pet_id>")
@jwt_required()
def update_pet(pet_id):
    user = _current_user()
    pet = db.session.get(Pet, pet_id)
    if not pet or pet.owner_id != user.id:
        return jsonify({"error": "pet not found"}), 404

    payload = request.get_json(silent=True) or {}

    def _pd(k):
        v = payload.get(k)
        return date.fromisoformat(v) if v else None

    for field in ("name", "species", "breed", "chip_id", "behavior_tag", "dietary_notes", "notes"):
        if field in payload:
            setattr(pet, field, (payload[field] or "").strip() or None)
    if "weight_kg" in payload:
        pet.weight_kg = payload["weight_kg"]
    if "rabies_vaccine_expiry" in payload:
        pet.rabies_vaccine_expiry = _pd("rabies_vaccine_expiry")
    if "combo_vaccine_expiry" in payload:
        pet.combo_vaccine_expiry = _pd("combo_vaccine_expiry")

    db.session.commit()
    return jsonify({"pet": _serialize(pet)})


@bp.get("/chip/<chip_id>")
@jwt_required()
def lookup_by_chip(chip_id):
    user = _current_user()
    if user.role not in ("receptionist", "admin"):
        return jsonify({"error": "forbidden"}), 403

    pet = db.session.execute(db.select(Pet).filter_by(chip_id=chip_id)).scalar_one_or_none()
    if not pet:
        return jsonify({"error": "chip not found"}), 404

    ok, reason = pet.vaccine_valid()
    return jsonify({
        "pet": _serialize(pet),
        "vaccine_valid": ok,
        "vaccine_block_reason": reason if not ok else None,
    })
