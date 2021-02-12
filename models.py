from app import db, sessionmaker, Base


class Camera(Base):
    __tablename__ = "ibea_agregate"

    id = db.Column(
        db.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True
    )
    line = db.Column(
        db.String(10),
    )
    line_side = db.Column(
        db.String(10),
    )
    date_now = db.Column(
        db.DateTime,
    )
    job = db.Column(
        db.String(50),
    )
    start_time = db.Column(
        db.DateTime,
    )
    last_part = db.Column(
        db.DateTime,
    )
    total = db.Column(
        db.Integer,
    )
    rejected = db.Column(
        db.Integer,
    )
