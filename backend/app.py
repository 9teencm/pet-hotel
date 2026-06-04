import os
from flask import Flask, jsonify, request as flask_request
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate  # type: ignore
from werkzeug.exceptions import HTTPException

from config import DevConfig
from models import db
from routes.auth import bp as auth_bp
from routes.booking import bp as booking_bp
from routes.payment import bp as payment_bp
from routes.pet import bp as pet_bp
from routes.grooming import bp as grooming_bp
from routes.room import bp as room_bp
from routes.admin import bp as admin_bp


def create_app(config_object=DevConfig):
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
    app.config.from_object(config_object)

    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)

    with app.app_context():
        db.create_all()

        from models.user import User
        test_accounts = [
            {"email": "customer@test.com",   "name": "測試顧客",   "role": "customer"},
            {"email": "groomer@test.com",     "name": "專業美容師", "role": "groomer"},
            {"email": "nanny@test.com",       "name": "親切保母",   "role": "nanny"},
            {"email": "reception@test.com",   "name": "前台接待員", "role": "receptionist"},
            {"email": "admin@test.com",       "name": "系統管理員", "role": "admin"},
        ]
        for acc in test_accounts:
            exists = db.session.execute(
                db.select(User).filter_by(email=acc["email"])
            ).scalar_one_or_none()
            if not exists:
                u = User(email=acc["email"], name=acc["name"], role=acc["role"])
                u.set_password("123456")
                db.session.add(u)
        db.session.commit()

        from models.room import Room
        if not db.session.execute(db.select(Room)).first():
            seed_rooms = [
                ("A101", "standard_cat"),
                ("A102", "standard_cat"),
                ("A103", "standard_cat"),
                ("B101", "deluxe_dog"),
                ("B102", "deluxe_dog"),
                ("S001", "suite"),
            ]
            for code, rtype in seed_rooms:
                db.session.add(Room(room_code=code, room_type=rtype))
            db.session.commit()

    app.register_blueprint(auth_bp,     url_prefix="/api/auth")
    app.register_blueprint(booking_bp,  url_prefix="/api/booking")
    app.register_blueprint(payment_bp,  url_prefix="/api/payment")
    app.register_blueprint(pet_bp,      url_prefix="/api/pet")
    app.register_blueprint(grooming_bp, url_prefix="/api/grooming")
    app.register_blueprint(room_bp,     url_prefix="/api/room")
    app.register_blueprint(admin_bp,    url_prefix="/api/admin")

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/health")
    def health():
        return jsonify({"ok": True})

    @app.errorhandler(Exception)
    def handle_any_error(e):
        if flask_request.path.startswith("/api/"):
            code = e.code if isinstance(e, HTTPException) else 500
            return jsonify({"error": str(e)}), code
        raise e

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="127.0.0.1", port=5000)
