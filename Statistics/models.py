from Statistics import db, Base_cam

class Camera(Base_cam):
    """Класс описывает таблицу ``ibea_agregate`` в ``EN-VM01``\n
    Таблица хранит данные с камер\n
    доступные поля таблицы:\n
    ``id`` - int - порядковый номер строки\n
    ``line`` - str(10) - название линии(прим.: LZ-1)\n
    ``line_side`` - str(10) - название камеры(прим.: LZ-1 A)\n
    ``date_now`` - datetime - системное время камеря\n
    ``date_now_sys`` - datetime - системное время системы\n
    ``job`` - str(50) - номер заказа(прим.: 10132)\n
    ``start_time`` - datetime - дата и время открытия смены на камере\n
    ``last_part`` - datetime - дата и время последнего прохождения крышки через камеру\n
    ``total`` - int - всего проконтролировано\n
    ``rejected`` - int - всего выброшено
    """

    __bind_key__ = "engine"
    __tablename__ = "ibea_agregate"

    id = db.Column(
        db.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True
    )
    line = db.Column(db.String(10))
    line_side = db.Column(db.String(10))
    date_now = db.Column(db.DateTime)
    date_now_sys = db.Column(db.DateTime)
    job = db.Column(db.String(50))
    start_time = db.Column(db.DateTime)
    last_part = db.Column(db.DateTime)
    total = db.Column(db.Integer)
    rejected = db.Column(db.Integer)

    @classmethod
    def get_camera_info(self, dt1, dt2, line):

        camera_query = self.query.with_entities(
            self.line,
            self.line_side,
            self.date_now,
            self.date_now_sys,
            self.job,
            self.total,
            self.rejected,
        ).filter(self.date_now_sys >= dt1, self.date_now_sys <= dt2, self.line == line)

        return camera_query
