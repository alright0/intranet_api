from datetime import date, datetime, timedelta
import pandas as pd
import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request, url_for
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from Statistics.config import VM
from Statistics.data.table import make_table
from Statistics.models import Camera
from Statistics.schemas import CameraSchema


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
        return {"message": "data not found"}

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
