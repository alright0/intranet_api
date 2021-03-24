import calendar
import json
from datetime import date, datetime, timedelta
import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlalchemy as db
from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify, redirect, render_template, request, url_for
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder

from sqlalchemy import cast, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from Statistics.config import *
from Statistics.data.table import make_table
from Statistics.models import *
from Statistics.schemas import CameraSchema

# import plotly.express as px


def _get_month():
    """возвращает даты начала и конца текущего месяца, подходящие к формату
    запроса в ``up_puco_export`` на ``EN-DB05``\n
    из формата ``2021-03-01 00:00:00`` в ``20210301``
    """

    dt_start = datetime(datetime.today().year, datetime.today().month, 1)
    dt_end = dt_start + relativedelta(months=1)

    # превращение даты из формата 2021-03-01 00:00:00 в 20210301
    dt_start = f"{str(dt_start)[:4]}{str(dt_start)[5:7]}{str(dt_start)[8:10]}"
    dt_end = f"{str(dt_end)[:4]}{str(dt_end)[5:7]}{str(dt_end)[8:10]}"

    return dt_start, dt_end


def _get_df_lvl_0(dt, dt2, line):
    """Функция принимает запрос из ``up_puco_export`` на ``EN-DB05`` и
    возвращает обработанный DataFrame готовый к\n
    дальнейшей обработке, построению таблиц и графиков\n
    Пример возвращаемого фрейма:\n
           line  order  counter_start  counter_end  shift puco_code  sheets           date_stop status         minutes
    0     LZ-01  10117            682        52066      2     OGE04       0 2021-03-01 00:21:28   STOP 0 days 00:01:35
    1     LZ-01  10117            682        52672      2       RUN     606 2021-03-01 00:21:40    RUN 0 days 00:00:12
    2     LZ-01  10117            682        52672      2     OGE04       0 2021-03-01 00:22:47   STOP 0 days 00:01:07
    3     LZ-01  10117            682        53050      2       RUN     378 2021-03-01 00:22:53    RUN 0 days 00:00:06
    """

    df_lvl_0 = pd.DataFrame(up_puco_export.get_production_info(dt, dt2, line))

    # df_lvl_0.to_csv(r"\\en-fs01\en-public\STP\Display\API\site\1.csv", sep=";")

    if not df_lvl_0.empty:

        # преобразование дата финиша из текста в дату
        df_lvl_0["end_date"] = pd.to_datetime(df_lvl_0["end_date"], format="%Y%m%d")

        # Преобразование даты старта из текста в дату
        df_lvl_0["start_date"] = pd.to_datetime(df_lvl_0["start_date"], format="%Y%m%d")

        # Смена
        df_lvl_0["shift"] = pd.to_numeric(df_lvl_0["shift"])

        # преобразование значения датчика входа в цифровой вид
        df_lvl_0["counter_start"] = pd.to_numeric(df_lvl_0["counter_start"])

        # преобразование значения датчика выхода в цифровой вид
        df_lvl_0["counter_end"] = pd.to_numeric(df_lvl_0["counter_end"])

        # форматирование кода остановки. Отрезание первых трех нулей
        df_lvl_0["puco_code"] = df_lvl_0["puco_code"].str[3:]

        # форматирование номера заказа. отрезание первых трех нулей
        df_lvl_0["order"] = df_lvl_0["order"].str[3:]

        # форматирование времени старта простоя
        df_lvl_0["start_time"] = df_lvl_0["start_time"].str[2:]
        df_lvl_0["start_time"] = (
            df_lvl_0["start_time"].str[:2]
            + ":"
            + df_lvl_0["start_time"].str[2:4]
            + ":"
            + df_lvl_0["start_time"].str[4:].replace("60", "59")
        )

        # форматирование времени финиша простоя
        df_lvl_0["end_time"] = df_lvl_0["end_time"].str[2:]
        df_lvl_0["end_time"] = (
            df_lvl_0["end_time"].str[:2]
            + ":"
            + df_lvl_0["end_time"].str[2:4]
            + ":"
            + df_lvl_0["end_time"].str[4:].replace("60", "59")
        )

        # конкатенция даты и времени начала остановки
        df_lvl_0["date_start_time"] = pd.to_datetime(
            df_lvl_0["start_date"].astype(str) + " " + df_lvl_0["start_time"]
        )

        # конкатенация даты и времени конца остановки
        df_lvl_0["date_end_time"] = pd.to_datetime(
            df_lvl_0["end_date"].astype(str) + " " + df_lvl_0["end_time"]
        )

        # получение времени простоя из разницы дат начала и конца
        df_lvl_0["stop_minutes"] = (
            (df_lvl_0["date_end_time"] - df_lvl_0["date_start_time"])
            .astype("timedelta64[s]")
            .astype(int)
        )

        # отрезание отрицетельных остановок(время начала меньше времени окончания)
        df_lvl_0 = df_lvl_0.loc[(df_lvl_0["stop_minutes"] > 1)]

        del df_lvl_0["start_date"]
        del df_lvl_0["start_time"]
        del df_lvl_0["end_date"]
        del df_lvl_0["end_time"]

        df_lvl_0.sort_values(by=["date_start_time"], inplace=True)

        df_lvl_0 = df_lvl_0.loc[
            (df_lvl_0["date_start_time"] < df_lvl_0["date_end_time"])
        ]

        # разделение на коды выпуска и остановки
        df_temp = df_lvl_0.copy()

        df_lvl_0["date_stop"] = df_lvl_0["date_start_time"]
        df_temp["date_stop"] = df_temp["date_end_time"]

        df_lvl_1 = [df_lvl_0, df_temp]
        df_lvl_1 = pd.concat(df_lvl_1)

        del df_lvl_1["date_start_time"]
        del df_lvl_1["date_end_time"]
        del df_lvl_1["stop_minutes"]

        df_lvl_1 = df_lvl_1.sort_values(by=["date_stop", "counter_end"])

        # время события
        df_lvl_1["minutes"] = df_lvl_1["date_stop"].diff().fillna(pd.Timedelta(days=0))

        df_lvl_1 = df_lvl_1.loc[(df_lvl_1["minutes"].dt.seconds > 1)]

        df_lvl_1["sheets"] = (
            df_lvl_1["counter_end"].diff().fillna(0).clip(lower=0).astype(int)
        )

        # фильтрация значений стопов. В данной базе стоп может быть нуленвым или
        # отрицательным если остановка короткая. Это стоит фильтровать.
        df_lvl_1 = df_lvl_1.loc[(df_lvl_1["minutes"].dt.seconds > 0)].reset_index(
            drop=True
        )

        df_lvl_1["status"] = (
            df_lvl_1["counter_start"].diff().fillna(0).clip(lower=0).astype(int)
        )

        df_lvl_1["status"] = df_lvl_1["status"].apply(lambda x: "RUN" if x else "STOP")
        df_lvl_1["puco_code"] = df_lvl_1[["puco_code", "status"]].apply(
            lambda x: "RUN" if x[1] == "RUN" else x, axis=1
        )

        # переразметка дат под соответствие сменам. Если смена переходит из одного
        # дня в другой, то дату необходимо сместить на 8 часов, иначе ничего не менять
        df_lvl_1["date"] = (
            df_lvl_1[["date_stop", "shift"]]
            .apply(
                lambda x: x[0]
                if x[0] > datetime(x[0].year, x[0].month, x[0].day, 8) or x[1] == 1
                else x[0] - timedelta(hours=8),
                axis=1,
            )
            .astype(str)
            .str[:10]
        )

        # print(df_lvl_1)
        # df_lvl_1.to_csv(r"\\en-fs01\en-public\STP\Display\API\site\1.csv", sep=";")

        return df_lvl_1
    else:

        return pd.DataFrame([])


def _month_range():
    """Функция принимает номер месяца в числовом формате от 1 до 12 и возвращает\n
    сформированный DataFrame c с датой, сменой и буквой смены для смерживания с\n
    выпуском\n
    Возвращаемый результат имеет следующий вид:
            date_stop  shift letter
    0   2021-03-01      1      A
    1   2021-03-01      2      D
    2   2021-03-02      1      A
    """

    # текущие год, месяц и последний день текущего месяца
    y = datetime.today().year
    m = datetime.today().month
    last_d = calendar.monthrange(y, m)[1]

    # здесь формируется список дат в формате (03.03.2021 ...) для текущего месяца
    # продублированный дважды для каждой смены
    month_range = (
        pd.date_range(start=date(y, m, 1), end=date(y, m, last_d)).astype(str).str[:10]
    )

    month_range = [day for day in month_range for _ in (0, 1)]
    shift_list = [1 if shift % 2 == 0 else 2 for shift in range(len(month_range))]

    # Константное значение порядка смен.
    LETTER = "CBCBDCDCADADBABA" * 94

    # большой список дат и букв для последующего маппинга
    datelist = pd.date_range(start=date(2021, 2, 1), end=date(2022, 1, 1))
    datelist = [str(day)[:10] for day in datelist for _ in (0, 1)]
    shiftlist = [1 if shift % 2 == 0 else 2 for shift in range(len(datelist))]

    # все даты
    full_date_df = pd.DataFrame(
        list(zip(datelist, shiftlist, LETTER)), columns=["date_stop", "shift", "letter"]
    )

    # этот месяц
    this_month_df = pd.DataFrame(
        list(zip(month_range, shift_list)), columns=["date_stop", "shift"]
    )

    # размеченные даты
    letter_df = pd.merge(
        this_month_df,
        full_date_df,
        how="inner",
        left_on=["date_stop", "shift"],
        right_on=["date_stop", "shift"],
    )

    return letter_df


def get_month_table():

    # переопределение даты для запроса в df_lvl_0
    dates = _get_month()

    # получение df размеченных дней смерживания с датами выпуска
    date_df = _month_range()

    df_list, line_list = [], []

    for line in LINES:
        df = _get_df_lvl_0(dates[0], dates[1], line)

        if not df.empty:

            df[line] = df["sheets"]

            del df["sheets"]

            df_list.append(df)

            df2 = pd.concat(df_list)

            line_list.append(line)

    df2 = pd.pivot_table(
        df2,
        index=[df2["date"], "shift"],
        values=line_list,
        aggfunc="sum",
    ).reset_index()

    df2["date"] = df2["date"].astype(str)

    df3 = pd.merge(
        date_df,
        df2,
        how="left",
        left_on=["date_stop", "shift"],
        right_on=["date", "shift"],
    )

    df3.fillna(0, inplace=True)
    del df3["date"]

    for line in line_list:
        df3[line] = df3[line].astype(int)

    # fig = go.Figure(data=go.Bar(x=(df3["date_stop"], df3["shift"]), y=df3["LL-02"]))

    # fig.show()

    fig2 = make_subplots(rows=5, cols=2, start_cell="bottom-left")

    for i in range(len(line_list)):

        # print(math.ceil((i + 1) / 2 if i > 0 else 1), i)

        fig2.add_trace(
            go.Bar(x=df3["letter"], y=df3[line_list[i]], name=line_list[i]),
            row=math.ceil((i + 1) / 2),
            col=1 if i % 2 == 0 else 2,
        )

    fig2.update_layout(margin=dict(t=0, l=0, b=0, r=0), height=900)

    # fig2.update_layout(width=500, height=500)
    # fig2.show()

    html = (
        df3.style.format({"LL-01": "{:,}"})
        .highlight_max(subset=line_list)
        .hide_index()
        .render()
    )

    plot_json = json.dumps(fig2, cls=PlotlyJSONEncoder)

    # print(plot_json)

    return html, plot_json

    def get_month_by_let():
        pass
