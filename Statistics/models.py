from Statistics import Base_cam
from sqlalchemy import Column, String, Integer, DateTime


class Camera(Base_cam):
    """Класс описывает таблицу ibea_agregate в EN-VM01. Таблица хранит данные с камер."""

    __bind_key__ = "engine"
    __tablename__ = "ibea_agregate"

    id = Column(
        Integer, nullable=False, unique=True, primary_key=True, autoincrement=True
    )
    line = Column(String(10))
    line_side = Column(String(10))
    date_now = Column(DateTime)
    date_now_sys = Column(DateTime)
    job = Column(String(50))
    start_time = Column(DateTime)
    last_part = Column(DateTime)
    total = Column(Integer)
    rejected = Column(Integer)

    @classmethod
    def get_camera_info(cls, dt1, dt2, line):
        return cls.query.filter(cls.date_now_sys >= dt1, cls.date_now_sys <= dt2, cls.line == line).values(
            cls.line,
            cls.line_side,
            cls.date_now,
            cls.date_now_sys,
            cls.job,
            cls.total,
            cls.rejected)
