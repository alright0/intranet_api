import math

from Statistics.logic.dataframes import *
from Statistics.models import *


def get_line_status(line):

    line_status_dict = {}

    if line in IBEA_CAMERA_MAP:
        cam_sides = []  # список процетов брака
        cam_time = []  # время последнего обновления
        line_status_dict["camera"] = {}

        for cam_side in IBEA_CAMERA_MAP[line]:
            cam_info = Camera.query.filter(Camera.line_side == cam_side).order_by(Camera.date_now.desc()).first()
            if not cam_info:
                line_status_dict["camera"]["defrate"] = [0.0]
                line_status_dict["camera"]["last_meas"] = ['NO DATA']
                continue

            total = cam_info.total
            rejected = cam_info.rejected
            last_part = datetime.now() - cam_info.date_now_sys
            last_part_h = last_part.total_seconds() / 60 / 60 - last_part.days * 24
            last_part_m = math.floor((last_part_h - math.floor(last_part_h)) * 60)

            cam_sides.append(rejected / total * 100 if rejected else 0.0)
            if last_part.days == 1:
                cam_time.append("{} day ago".format(last_part.days))
            elif last_part.days > 1:
                cam_time.append("{} days ago".format(last_part.days))

            else:
                cam_time.append("{:0>2}h {:0>2}m ago".format(math.floor(last_part_h), last_part_m))

            line_status_dict["camera"]["defrate"] = cam_sides
            line_status_dict["camera"]["last_meas"] = cam_time
    return line_status_dict


def get_camera_now(line):
    """Эта функция принимает название камеры('LZ-1 A', 'LZ-2 ST' и т.п.) и отдает последнюю запись"""
    cam = Camera.query.filter(Camera.line_side == line).order_by(Camera.date_now.desc()).first()
    if cam:
        return {
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

    return {"message": "data not found"}