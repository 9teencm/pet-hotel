from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from models import db
from models.user import User

bp = Blueprint("auth", __name__)


@bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""
    name = (payload.get("name") or "").strip() or None
    role = (payload.get("role") or "customer").strip()

    if not email or not password:
        return jsonify({"error": "email/password required"}), 400

    exists = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if exists:
        return jsonify({"error": "email already registered"}), 409

    user = User(email=email, name=name, role=role)  # type: ignore
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}, "access_token": token}), 201


@bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email/password required"}), 400

    user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"user": {"id": user.id, "email": user.email, "name": user.name, "role": user.role}, "access_token": token})

