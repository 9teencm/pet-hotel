from flask import Blueprint, jsonify, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.user import User

bp = Blueprint("admin", __name__)

VALID_ROLES = {"customer", "groomer", "nanny", "receptionist", "admin"}


def _current_admin():
    uid = int(get_jwt_identity())
    user = db.session.get(User, uid)
    if not user:
        abort(401)
    if user.role != "admin":
        abort(403)
    return user


def _serialize(u):
    return {
        "id": u.id,
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "created_at": u.created_at.isoformat(),
    }


@bp.get("/users")
@jwt_required()
def list_users():
    _current_admin()
    users = db.session.execute(db.select(User).order_by(User.id)).scalars().all()
    return jsonify({"users": [_serialize(u) for u in users]})


@bp.post("/users")
@jwt_required()
def create_user():
    _current_admin()
    payload = request.get_json(silent=True) or {}

    email = (payload.get("email") or "").strip().lower()
    name = (payload.get("name") or "").strip()
    role = (payload.get("role") or "customer").strip()
    password = (payload.get("password") or "").strip()

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400
    if role not in VALID_ROLES:
        return jsonify({"error": f"invalid role; must be one of {sorted(VALID_ROLES)}"}), 400

    existing = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if existing:
        return jsonify({"error": "email already in use"}), 409

    u = User(email=email, name=name or None, role=role)  # type: ignore
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    return jsonify({"user": _serialize(u)}), 201


@bp.put("/users/<int:user_id>")
@jwt_required()
def update_user(user_id):
    me = _current_admin()
    payload = request.get_json(silent=True) or {}

    u = db.session.get(User, user_id)
    if not u:
        return jsonify({"error": "user not found"}), 404

    if "name" in payload:
        u.name = (payload["name"] or "").strip() or None
    if "role" in payload:
        role = (payload["role"] or "").strip()
        if role not in VALID_ROLES:
            return jsonify({"error": f"invalid role"}), 400
        u.role = role
    if "email" in payload:
        new_email = (payload["email"] or "").strip().lower()
        if new_email and new_email != u.email:
            clash = db.session.execute(db.select(User).filter_by(email=new_email)).scalar_one_or_none()
            if clash:
                return jsonify({"error": "email already in use"}), 409
            u.email = new_email
    if "password" in payload and payload["password"]:
        u.set_password(payload["password"].strip())

    db.session.commit()
    return jsonify({"user": _serialize(u)})


@bp.delete("/users/<int:user_id>")
@jwt_required()
def delete_user(user_id):
    me = _current_admin()
    if me.id == user_id:
        return jsonify({"error": "cannot delete your own account"}), 400

    u = db.session.get(User, user_id)
    if not u:
        return jsonify({"error": "user not found"}), 404

    db.session.delete(u)
    db.session.commit()
    return jsonify({"success": True})
