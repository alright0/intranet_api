from datetime import date, datetime, timedelta
import pandas as pd
import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request, url_for
from sqlalchemy import create_engine, cast
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from Statistics.config import *
from Statistics.data.table import make_table
from Statistics.models import *
from Statistics.schemas import CameraSchema
from Statistics.logic.dataframes import *


def get_df():

    dt = 20210320
    dt2 = 20210321

    print(get_df_lvl_0(dt, dt2, "LZ-01"))


def order_description(order):
    """Принимает номер заказа в виде строки(прим.: ``10012`` ``00513``) и возвращает описание.\n
    Соответствует двум запросам:\n
    ``SELECT po_id(index) FROM as_line_speed WHERE product_id(order) = '{order}'``\n
    ``SELECT the_name_of_the_holding_company(full_name) FROM as_material_data WHERE article(index) = (first_query)``
    """

    index = as_line_speed.query.filter(as_line_speed.order == order).first().index

    description = (
        as_material_data.query.filter(as_material_data.index == index).first().full_name
    )

    cut = 40
    # если длина описания больше cut, то обрезать его
    return description if len(description) <= cut else f"{description[:cut]}..."


def get_line_status(line):
    """Возвращает словарь состояния линии со следующими переменными:\n
    ``status`` - состояние линии ``STOP`` | ``RUN`` | ``PUCO CODE. 3 минут(ы)``\n
    ``operator`` - имя и фамилия оператора ``Иван Иванов``\n
    ``input`` - счетчик входа линии ``5 513``\n
    ``output`` - счетчик выхода линии ``3 312``\n
    ``order`` - словарь с ключами ``order`` - номер заказа, ``description`` - описанеие заказа \n
    ``camera`` - словарь с ключами ``defrate`` - процент брака, ``last_meas`` - количество минут \n
        с момента последнего измерения\n
        ['0 минут(ы) назад','4 минут(ы)'] - 2 камеры
        ['0 минут(ы) назад]                     - 1 камера
        []                                      - нет камер
        0                                       - ошибка

    Пример:
        {
        "status": "Причина не определена. 24 минут(ы)",
        "operator": "Алексей Ведров",
        "input": "1 412",
        "output": "109 562",
        "order": {"order": "10163", "description": "EOER 083 W+FL/FL"},
        "camera": {
            "defrate": [1.0020991147211828, 1.9277460340641488],
            "last_meas": ["23 минут(ы)", "23 минут(ы)"],
            },
        }
    """

    line_status_dict = dict()

    try:
        # получение списка параметров линии
        line_status = LineStatus.get_line_param(line)

        if int(line_status.shift):

            line_status_dict["status"] = LineStatus.get_status(line)
            line_status_dict["operator"] = fc_users.get_operator_name(line)

            line_status_dict["input"] = "{:,}".format(
                line_status.counter_start
            ).replace(",", " ")
            line_status_dict["output"] = "{:,}".format(line_status.counter_end).replace(
                ",", " "
            )

            line_status_dict["order"] = {}
            line_status_dict["order"]["order"] = line_status.order

            # описание заказа
            try:
                line_status_dict["order"]["description"] = order_description(
                    line_status.order
                )
            except:
                line_status_dict["order_description"] = "Description not found"

            line_status_dict["camera"] = {}

            # процент брака по камерам. Возвращается список от 0 до 2 элементов
            try:
                if line in IBEA_CAMERA_MAP:

                    cam_sides = []  # список процетов брака
                    cam_time = []  # время последнего обновления

                    for cam_side in IBEA_CAMERA_MAP[line]:

                        cam_info = (
                            Camera.query.filter(Camera.line_side == cam_side)
                            .order_by(Camera.date_now.desc())
                            .first()
                        )

                        cam_sides.append(
                            cam_info.rejected / cam_info.total * 100
                            if cam_info.rejected > 0
                            else 0.0
                        )

                        # TODO: привязать время камеры к системному времени(date_now_sys)
                        cam_last_part = (
                            cam_info.date_now - cam_info.last_part
                        ).seconds // 60

                        cam_time.append(f"{cam_last_part} минут(ы)")

                    line_status_dict["camera"]["defrate"] = cam_sides
                    line_status_dict["camera"]["last_meas"] = cam_time
                else:
                    line_status_dict["camera"]["defrate"] = []
                    line_status_dict["camera"]["last_meas"] = []
            except:
                line_status_dict["camera"]["defrate"] = [0.0]  # ["--/--"]
                line_status_dict["camera"]["last_meas"] = 0
        else:
            line_status_dict["status"] = "STOP"

    except AttributeError:
        line_status_dict["status"] = "Line not found"

    finally:
        # print(line_status_dict)
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

    # TODO: перевести логику полностью внутрь таблицы

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
