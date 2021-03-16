from datetime import date, datetime, timedelta
import pandas as pd
import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request, url_for
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from Statistics.config import VM, FC
from Statistics.data.table import make_table
from Statistics.models import Camera, LineStatus, fc_produkcja, fc_users
from Statistics.schemas import CameraSchema

IBEA_CAMERA_MAP = {
    "LZ-01": ["LZ-1 A", "LZ-1 B"],
    "LZ-02": ["LZ-2 A", "LZ-2 B"],
    "LZ-03": ["LZ-3"],
    "LZ-04": ["LZ-4"],
    "LZ-05": ["LZ-5 A", "LZ-5 B"],
}


def get_line_status(line):
    """Эта функция возвращает данные для таблицы текущего состояния: имя оператора"""

    line_status_dict = dict()

    line_status = LineStatus.get_line_param(line)

    if int(line_status.shift):

        line_status_dict["status"] = LineStatus.get_status(line)
        line_status_dict["operator"] = fc_users.get_operator_name(line)

        line_status_dict["input"] = line_status.counter_start
        line_status_dict["output"] = line_status.counter_end

        if line in IBEA_CAMERA_MAP:
            cam_sides = []
            for cam_side in IBEA_CAMERA_MAP[line]:

                cam_info = (
                    Camera.query.filter(Camera.line_side == cam_side)
                    .order_by(Camera.date_now.desc())
                    .first()
                )
                cam_sides.append(
                    "{:.2f}%".format(
                        cam_info.rejected / cam_info.total * 100
                        if cam_info.rejected > 0
                        else 0
                    )
                )

            line_status_dict["camera"] = cam_sides
        else:
            line_status_dict["camera"] = []
    else:
        line_status_dict["status"] = "STOP"

    return line_status_dict


def get_camera_now(line):
    """Эта функция принимает название камеры('LZ-1 A', 'LZ-2 ST' и т.п.) и отдает последнюю запись"""

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
            "message": "OK",
        }

    except:
        return jsonify({"message": "data not found"})

    return jsonify(serialized)


def camera_json_deserialize(json_response):
    """Эта функция принимает последнюю запись из БД камеры и превращает ее в таблицу"""

    # TODO перевести логику полностью внутрь таблицы

    try:
        converted_dict = json_response.json

    except:

        converted_dict = {"message": "data not found"}

    df = pd.Series(converted_dict)
    df = df.to_frame().transpose()

    return df.to_html()


def makedate(dt):
    """Эта функция принимает значение даты в строки в формате (%Y-%m-%d = YYYY-MM-DD)
    и возвращает 2 кортежа datetime входящей даты и + 1 сутки"""
    try:
        dt = datetime.strptime(dt[:10], "%Y-%m-%d")

    except:
        dt = datetime.strptime(str(datetime.now() - timedelta(days=1))[:10], "%Y-%m-%d")

    dt2 = dt + timedelta(days=1)

    return dt, dt2
