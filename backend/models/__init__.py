from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models so SQLAlchemy can discover them for db.create_all()
from models.user import User          # noqa: E402, F401
from models.pet import Pet            # noqa: E402, F401
from models.room import Room          # noqa: E402, F401
from models.booking import Booking    # noqa: E402, F401
from models.payment import Payment    # noqa: E402, F401
from models.report import Report      # noqa: E402, F401
from models.grooming import GroomingService  # noqa: E402, F401
