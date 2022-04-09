from __future__ import annotations

import calendar
import json
import math
from datetime import date, datetime, time, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from config import IBEA_CAMERA_MAP, LINES
from dateutil.relativedelta import relativedelta
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder
from Statistics.models import *


# TODO: разделись методы на таблицы и графики
class up_puco_table:
    """Класс возвращает представления таблицы ``up_puco_export`` по датам и линиям.\n
    входные параметры:\n
    ``date`` - datetime - дата, за которую необходимо получить отчет. \n
        По умолчанию идет предыщуший день или текущий месяц\n
    ``period`` - str - ``'month'``, ``'day'`` - день или месяц. По умолчанию ``"month"``\n
    ``delta` - int - количество дней/месяцев от указанной даты. По умолчанию 1\n
    ``lines`` - list - список линий, которые необходимо отобразить.\n
        По умолчанию все линии\n
    """

    def __init__(self, date, delta=1, lines=LINES):

        self.date = date
        self.delta = delta
        self.lines = lines

        self.date_start_with_hours = self.date + timedelta(hours=6)
        self.date_end_with_hours = self.date + timedelta(days=1, hours=6)

    def __repr__(self):
        return (
            f"Информация за период с {datetime.strftime(self.date_start_with_hours, '%Y-%m-%d')} "
            + f"по {datetime.strftime(self.date_end_with_hours, '%Y-%m-%d')} по работе линий:\n{self.lines}"
        )

    def graph(self):

        line_by_shift_list = {}
        camera_table_df = self.__parse_camera()

        for line in self.lines:

            line_by_shift_list[line] = {}
            for shift in range(1, 4):

                empty_flag = True
                fig = make_subplots()
                # работа камер
                if not camera_table_df.empty and line in IBEA_CAMERA_MAP:
                    for line_side in IBEA_CAMERA_MAP[line]:

                        camera_side_df = camera_table_df.loc[
                            (camera_table_df["line_side"] == line_side)
                            & (camera_table_df["shift"] == shift)
                        ]

                        if not camera_side_df.empty:
                            empty_flag = False

                        camera_name_string = (
                            "{}: {:.2f}% ({} шт. выброшено из {} шт.)".format(
                                line_side,
                                camera_side_df["pcs_rejected"].sum()
                                / camera_side_df["pcs_total"].sum()
                                * 100,
                                camera_side_df["pcs_rejected"].sum(),
                                camera_side_df["pcs_total"].sum(),
                            )
                        )

                        fig.add_trace(
                            go.Scatter(
                                x=camera_side_df["date_now_sys"],
                                y=camera_side_df["defect_rate"] * 100,
                                name=camera_name_string,
                                hovertemplate=line_side
                                + "<br>Выброс: %{y:.2f}%.<br>Время: "
                                + camera_side_df["date_now_sys"].astype(str).str[-8:],
                            ),
                        )
                    if empty_flag:
                        fig.add_annotation(
                            x=0.5,
                            y=0.5,
                            xref="paper",
                            yref="paper",
                            showarrow=False,
                            text="NO DATA",
                        )

                    fig.update_layout(
                        title=f"LINE: {line} SHIFT: {shift}",
                        margin=dict(l=10, r=10, t=30, b=10),
                        yaxis=dict(range=[-0.5, 10]),
                        showlegend=True,
                        legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01,
                        ),
                    )

                    line_by_shift_list[line][shift] = self.graph_to_json(fig)

        return line_by_shift_list

    # NOTE: Создание
    def __parse_camera(self):
        """График выпуска камеры. Принимает запрос из ``ibea_agregate`` на ``EN-VM01``"""

        df_line_list = []
        camera_line_df = pd.DataFrame([])

        # запрос под каждую камеру и добавление поля брака
        for line in self.lines:

            camera_result_df = pd.DataFrame([])
            df_camera_list = []

            # основная работа начинается, если линия есть в списке линий для запроса в камеры
            if line in IBEA_CAMERA_MAP:
                df_camera_lvl_0 = pd.DataFrame(
                    Camera.get_camera_info(
                        self.date_start_with_hours, self.date_end_with_hours, line
                    ),
                    columns=[
                        "line",
                        "line_side",
                        "date_now",
                        "date_now_sys",
                        "job",
                        "total",
                        "rejected",
                    ],
                )

                df_line_list.append(df_camera_lvl_0)

        camera_line_df = camera_line_df.append(df_line_list)

        # если фрейм пустой - поставить график-заглушку "Нет информации"
        if not camera_line_df.empty:

            camera_line_df["defect_rate"] = camera_line_df[["rejected", "total"]].apply(
                lambda x: x[0] / x[1] if x[1] != 0 else 0, axis=1
            )

            camera_line_df.fillna(0, inplace=True)
            camera_line_df["shift"] = camera_line_df["date_now_sys"].apply(
                lambda x: 1
                if x.hour >= 6 and x.hour < 14
                else 2
                if x.hour >= 14 and x.hour < 22
                else 3
            )
            camera_line_df["defect_rate"] = camera_line_df["defect_rate"].apply(
                lambda x: 0.1 if x > 0.1 else x
            )
            camera_line_df = camera_line_df.sort_values(by="date_now_sys")

            for line_side in set(camera_line_df["line_side"]):
                camera_side_df = camera_line_df.loc[
                    (camera_line_df["line_side"] == line_side)
                ]
                camera_side_df["pcs_total"] = (
                    camera_side_df["total"].diff().fillna(0).clip(lower=0).astype(int)
                )
                camera_side_df["pcs_rejected"] = self.cumsum_to_any(
                    camera_side_df, "rejected"
                )

                df_camera_list.append(camera_side_df)

            camera_result_df = camera_result_df.append(df_camera_list)
            return camera_result_df
        return pd.DataFrame([])

    # READY: Преобразует графики в json
    @staticmethod
    def graph_to_json(fig):
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    @staticmethod
    def cumsum_to_any(final_df_by_line, cumsum_counter):
        """Конвертирует накопительную сумму в разницу значений накопительной суммы:\n
        ``10 20 25 30 45`` в ``0 10 15 5 5 15``"""

        return (
            final_df_by_line[cumsum_counter].diff().fillna(0).clip(lower=0).astype(int)
        )
