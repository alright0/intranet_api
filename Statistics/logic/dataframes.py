from __future__ import annotations

import json
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
from config import IBEA_CAMERA_MAP, LINES
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder
from Statistics.models import *


# TODO: разделись методы на таблицы и графики
class up_puco_table:
    """Класс формирует данные для plotly.js"""

    def __init__(self, date, lines=LINES):
        self.date = date
        self.lines = lines
        self.date_start = self.date + timedelta(hours=6)
        self.date_end = self.date + timedelta(days=1, hours=6)

        self.defrate_cutoff = 0.1

    def graph(self):

        line_by_shift_list = {}
        camera_df = self._parse_camera()

        for line in self.lines:

            line_by_shift_list[line] = {}
            for shift in range(1, 4):

                empty_flag = True  # флаг, указывающий, стоит ли вешать плашку "NO DATA"

                fig = make_subplots()
                if not camera_df.empty and line in IBEA_CAMERA_MAP:
                    for line_side in IBEA_CAMERA_MAP[line]:

                        camera_side_df = camera_df.loc[
                            (camera_df["line_side"] == line_side)
                            & (camera_df["shift"] == shift)
                        ]

                        if not camera_side_df.empty:
                            empty_flag = False

                        camera_name_string = self._build_legend_string(camera_side_df, line_side)

                        fig.add_trace(
                            go.Scatter(
                                x=camera_side_df["date_now_sys"],
                                y=camera_side_df["defect_rate"] * 100,
                                name=camera_name_string,
                                hovertemplate="<extra></extra>"
                                + "<b>" + line_side
                                + "</b><br>Выброс: %{y:.2f}%<br>Время: "
                                + camera_side_df["date_now_sys"].dt.strftime('%H:%M'),
                                hoverinfo='skip'
                            ),
                        )

                    if empty_flag:
                        self.add_nodata_annotation(fig)

                    fig.update_layout(
                        title=f"Line: {line} Shift: {shift}",
                        margin=dict(l=10, r=10, t=30, b=10),
                        yaxis=dict(range=[-0.5, 10]),
                        showlegend=True,
                        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                    )
                    line_by_shift_list[line][shift] = self.graph_to_json(fig)
        return line_by_shift_list

    def _parse_camera(self):
        """График выпуска камеры. Принимает запрос из ``ibea_agregate`` на ``EN-VM01``"""

        df_line_list, df_camera_list = [], []
        camera_line_df = pd.DataFrame([])
        camera_result_df = pd.DataFrame([])

        # запрос под каждую камеру и добавление поля брака
        for line in self.lines:
            if line in IBEA_CAMERA_MAP:
                camera_data = Camera.get_camera_info(self.date_start, self.date_end, line)
                df_camera_lvl_0 = pd.DataFrame(list(camera_data))
                df_line_list.append(df_camera_lvl_0)
        camera_line_df = camera_line_df.append(df_line_list)

        # если фрейм пустой - поставить график-заглушку "Нет информации"
        if not camera_line_df.empty:

            camera_line_df["defect_rate"] = camera_line_df[["rejected", "total"]].apply(
                lambda x: x[0]/x[1] if x[1] else 0, axis=1
            )
            camera_line_df["defect_rate"] = self._cutoff_high_limit(camera_line_df["defect_rate"])

            camera_line_df.fillna(0, inplace=True)
            camera_line_df["shift"] = self._map_shifts(camera_line_df["date_now_sys"])
            camera_line_df = camera_line_df.sort_values(by="date_now_sys")

            for line_side in set(camera_line_df["line_side"]):
                camera_side_df = camera_line_df.loc[(camera_line_df["line_side"] == line_side)]
                camera_side_df["pcs_total"] = self.cumsum_to_any(camera_side_df, "total")
                camera_side_df["pcs_rejected"] = self.cumsum_to_any(camera_side_df, "rejected")

                df_camera_list.append(camera_side_df)

            camera_result_df = camera_result_df.append(df_camera_list)
        return camera_result_df

    # READY: Преобразует графики в json
    @staticmethod
    def graph_to_json(fig):
        """
        Экспорт фигуры для интерпретации на фронте в plotly.js.

        :param fig: plotly figure
        :return: json
        """
        return json.dumps(fig, cls=PlotlyJSONEncoder)

    @staticmethod
    def cumsum_to_any(df, cumsum_counter):
        """
        Конвертирует накопительную сумму в разницу значений накопительной суммы.
        [10, 20, 25, 30, 45] -> [0, 10, 15, 5, 5, 15].

        :param df: DataFrame
        :param cumsum_counter: Название столбца по котором будет считаться разница
        :return: DataFrame
        """

        return df[cumsum_counter].diff().fillna(0).clip(lower=0).astype(int)

    @staticmethod
    def _build_legend_string(df, line_side):
        """
        Формирует строку для легенды.

        :param df: DataFrame
        :param line_side: Название стороны камеры
        :return: Строку с описанием
        """
        return "{}: {:.2f}% ({} шт. выброшено из {} шт.)".format(
                line_side,
                df["pcs_rejected"].fillna(0).sum() / (df["pcs_total"].sum() if df["pcs_total"].sum() else 1) * 100,
                df["pcs_rejected"].sum(),
                df["pcs_total"].sum(),
            )

    @staticmethod
    def _map_shifts(df_series):
        """
        Размечает series с датами по сменам.

        :param df_series: DataFrame
        :return: DateFrame
        """
        return df_series.apply(
                lambda x: 1
                if x.hour >= 6 and x.hour < 14
                else 2
                if x.hour >= 14 and x.hour < 22
                else 3
        )

    def _cutoff_high_limit(self, df_series):
        return df_series.apply(lambda x: self.defrate_cutoff if x > self.defrate_cutoff else x)

    @staticmethod
    def add_nodata_annotation(fig):
        """
        Добавляет плашку NO DATA в центре пустого графика.

        :param fig: plotly figure
        """
        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            text="NO DATA",
        )