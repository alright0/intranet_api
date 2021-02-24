from Statistics.app import db, sessionmaker, Base_cam, Base_fc


class Camera(Base_cam):
    __bind_key__ = "cam_engine"
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


class LineStatus(Base_fc):
    __bind_key__ = "fc_engine"
    __tablename__ = "up_line_def"

    nr_line = db.Column(db.Text)
    fc_line = db.Column(db.Text, nullable=False, unique=True, primary_key=True)
    prod_order = db.Column(db.Text)
    shift = db.Column(db.Text)
    starus_line = db.Column(db.Integer)
    puco_need = db.Column(db.Integer)
    puco_code = db.Column(db.Integer)
    counter_start = db.Column(db.Integer)
    counter_end = db.Column(db.Integer)
    stop_time = db.Column(db.Integer)
    puco_string = db.Column(db.Text)
    qv_name = db.Column(db.Text)
    id_worker = db.Column(db.Integer)
    id_master_plc = db.Column(db.VARCHAR(8))
    local_name = db.Column(db.VARCHAR)


"""
class LineStatusOrm(LineStatus):
    __bind_key__ = "4Can"

    pk=db.Column(db.Text, primary_key=True)
"""