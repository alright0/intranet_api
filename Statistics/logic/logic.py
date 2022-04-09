
from Statistics.logic.dataframes import *
from Statistics.models import *


def get_line_status(line):
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
        if line in IBEA_CAMERA_MAP:

            cam_sides = []  # список процетов брака
            cam_time = []  # время последнего обновления
            line_status_dict["camera"] = {}

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

                cam_last_part = (datetime.now() - cam_info.date_now_sys).seconds // 60

                cam_time.append(f"{cam_last_part} minutes")

            line_status_dict["camera"]["defrate"] = cam_sides
            line_status_dict["camera"]["last_meas"] = cam_time

    except:
        line_status_dict["camera"]["defrate"] = [0.0]  # ["--/--"]
        line_status_dict["camera"]["last_meas"] = 0

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
