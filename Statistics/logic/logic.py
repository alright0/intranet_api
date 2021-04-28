from datetime import date, datetime, timedelta

import pandas as pd
from config import IBEA_ADDRESS, IBEA_CAMERA_MAP, LINE_OUTPUT, LINES
from flask import jsonify
from Statistics.logic.dataframes import *
from Statistics.models import *
from Statistics.schemas import CameraSchema
from Statistics.logic.queries import get_order_description


def get_date_from_html_input(calendar_date, template):
    "Возвращает формат даты, подходящий для создания экземпляра выпуска линии из input=date"

    return datetime.strptime(calendar_date, template).date()


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
    # пустой словарь
    line_status_dict = dict(
        status="",
        operator="",
        input=0,
        output=0,
        order={"order": "", "description": ""},
        camera={},
    )

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
            line_status_dict["order"]["description"] = get_order_description(
                [line_status.order]
            )[line_status.order]

            # line_status_dict["camera"] = {}

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

        return {"message": "data not found"}

    return serialized


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
