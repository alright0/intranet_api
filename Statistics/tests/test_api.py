import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from Statistics import *

camera = "LZ-01"
camera_side = "LZ-01 A"

wrong_camera = "wrong line_name"
wrong_camera_side = "wrong_camera_side"


def test_camera_api_response():

    camera_response = client.get(f"/camera/{camera}")

    assert camera_response.status_code == 200
    assert camera_response.get_json()[0]["message"] == "OK"

    wrong_camera_response = client.get(f"/camera/{wrong_camera}")

    assert wrong_camera_response.status_code == 400
    assert wrong_camera_response.get_json()[0]["message"] == "data not found"


def test_camera_side_api_response():

    camera_side_response = client.get(f"/camera/last/{camera_side}")

    assert camera_side_response.status_code == 200
    assert camera_side_response.get_json()["message"] == "OK"

    wrong_camera_side_response = client.get(f"/camera/{wrong_camera_side}")

    assert wrong_camera_side_response.status_code == 400
    assert wrong_camera_side_response.get_json()[0]["message"] == "data not found"
