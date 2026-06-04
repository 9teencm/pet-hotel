from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.room import Room, RoomStatus
from models.user import User

bp = Blueprint("room", __name__)


def _require_role(*roles):
    """回傳 (user, error_response) 其中一個為 None。"""
    uid = int(get_jwt_identity())
    user = db.session.get(User, uid)
    if not user or user.role not in roles:
        return None, (jsonify({"error": "forbidden"}), 403)
    return user, None


@bp.get("/")
def list_rooms():
    """列出所有房間與目前狀態（公開）。"""
    rooms = db.session.execute(db.select(Room).order_by(Room.room_code)).scalars().all()
    return jsonify({"rooms": [
        {"id": r.id, "room_code": r.room_code, "room_type": r.room_type,
         "status": r.status, "price_per_night": r.price_per_night}
        for r in rooms
    ]})


@bp.post("/<int:room_id>/transition")
@jwt_required()
def transition_room(room_id):
    """前台/管理員手動切換床位狀態。"""
    user, err = _require_role("receptionist", "admin")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    new_status = (payload.get("status") or "").strip()
    if new_status not in (RoomStatus.AVAILABLE, RoomStatus.RESERVED,
                          RoomStatus.OCCUPIED, RoomStatus.CLEANING):
        return jsonify({"error": "invalid status"}), 400

    room = db.session.get(Room, room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404

    try:
        room.transition_to(new_status)
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    db.session.commit()
    return jsonify({"room_code": room.room_code, "status": room.status})
