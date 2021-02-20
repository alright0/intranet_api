from datetime import date, datetime, timedelta

import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request, url_for, Blueprint
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from Statistics.config import VM
from Statistics.data.table import make_table
from Statistics.models import Camera
from Statistics.schemas import CameraSchema

camera = Blueprint("camera", __name__)


def get_camera_now(line):

    try:
        cam = (
            Camera.query.filter(Camera.line_side == line)
            .order_by(Camera.date_now.desc())
            .first()
        )

        serialized = {
            "id": cam.id,
            "line": cam.line,
            "line_side": cam.line_side,
            "date_now": cam.date_now,
            "job": cam.job,
            "start_time": cam.start_time,
            "last_part": cam.last_part,
            "total": cam.total,
            "rejected": cam.rejected,
        }

    except:
        return {"message": "data not found"}

    return jsonify(serialized)


def makedate(dt):

    dt = datetime.strptime(dt[:10], "%Y-%m-%d")

    dt2 = dt + timedelta(days=1)

    return dt, dt2


# api-ответ, возвращающий json из EN-VM01.ibea_agregate
@camera.route("/camera/<line>", methods=["GET"])
def get_camera_info(line):

    one = Camera.query.filter(Camera.line == line).limit(5)

    serialized = []
    for cam in one:
        serialized.append(
            {
                "id": cam.id,
                "line": cam.line,
                "line_side": cam.line_side,
                "date_now": cam.date_now,
                "job": cam.job,
                "start_time": cam.start_time,
                "last_part": cam.last_part,
                "total": cam.total,
                "rejected": cam.rejected,
            }
        )

    if not serialized:
        return {"message": "data not found"}

    return jsonify(serialized)


# api-ответ Нахождение последней записи в базе
@camera.route("/camera/last/<line>", methods=["GET"])
def get_camera_info_last(line):
    return get_camera_now(line)