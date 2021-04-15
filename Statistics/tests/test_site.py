import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2]))

from Statistics import *


def test_index():

    result = client.get("/")

    assert result.status_code == 200


def test_pp_staff():

    result = client.get("/production_plan_staff")

    assert result.status_code == 200


def test_pp():

    result = client.get("/production_plan")

    assert result.status_code == 200
