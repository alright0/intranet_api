from __future__ import annotations

import json
from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
from config import IBEA_CAMERA_MAP, LINES
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder
from Statistics.models import *


class CameraGraph:
    """Класс формирует данные для plotly.js"""

    def __init__(self, date_start, date_end=None, lines=LINES):
        self.date = date_start
        self.lines = lines
        self.date_start = self.date + timedelta(hours=6)
        self.date_end = date_end + timedelta(hours=6) if date_end else self.date + timedelta(days=1, hours=6)

        self.defrate_cutoff = 0.1

        self.colors = ['dodgerblue', 'tomato', 'darkgreen', 'orange',]

    def graph(self):

        line_by_shift_list = {}
        camera_df = self._parse_camera()

        for line in self.lines:

            line_by_shift_list[line] = {}
            for shift in range(1, 4):

                fig = make_subplots(
                    rows=4,
                    cols=1,
                    vertical_spacing=0.02,
                    shared_xaxes=True,
                )

                if not camera_df.empty and line in IBEA_CAMERA_MAP:
                    for color_index, line_side in enumerate(IBEA_CAMERA_MAP[line]):

                        camera_line_df = camera_df.loc[
                            (camera_df["line"] == line)
                            & (camera_df["shift"] == shift)
                        ]
                        camera_side_df = camera_line_df.loc[(camera_line_df["line_side"] == line_side)]

                        camera_name_string = self._build_legend_string(camera_side_df, line_side)

                        def _add_trace(hovertemplate, row, x, range, showlegend, y_title,):
                            fig.add_trace(
                                go.Scatter(
                                    x=camera_side_df["date_now_sys"],
                                    y=x,
                                    name=camera_name_string,
                                    hovertemplate="<extra></extra>"
                                                  + f"<b>{line_side}</b><br>"
                                                  + 'Работа: '
                                                  + camera_side_df["job"]
                                                  + "<br>Время: "
                                                  + camera_side_df["date_now_sys"].dt.strftime('%H:%M')
                                                  + "<br>"
                                                  + hovertemplate,
                                    hoverinfo='skip',
                                    marker=dict(color=self.colors[color_index]),
                                    showlegend=showlegend,
                                    legendgroup=line_side,
                                ),
                                row=row,
                                col=1,
                            )

                            if camera_line_df.empty:
                                self.add_nodata_annotation(fig, row)

                            fig.update_yaxes(range=range, col=1, row=row, title=y_title)

                        x = camera_side_df["defect_rate"]
                        min_range_ratio, max_range_ratio = -0.05, 1.125
                        min_range, max_range = -0.5, 10
                        _add_trace(
                            hovertemplate="Выброс: %{y:.2f}%",
                            row=1,
                            x=x * 100,
                            range=[min_range, max_range,],
                            showlegend=True,
                            y_title='Брак, %'
                        )

                        x = camera_side_df["total"]
                        min_range, max_range = -5000, 100000
                        _add_trace(
                            hovertemplate="Абсолютый выпуск: %{y}",
                            row=2,
                            x=x,
                            range=[
                                x.max() * min_range_ratio or min_range,
                                x.max() * max_range_ratio or max_range,
                            ],
                            showlegend=False,
                            y_title='Прирост, %'
                        )

                        x = camera_side_df["pcs_total"]
                        min_range, max_range = -50, 1000
                        # x_range - наибольший индекс среди максимальных вхождений. хороший вариант для средней скорости
                        x_range = x.value_counts().head(5).sort_index(ascending=False)
                        x_range = x_range.first_valid_index() if not x_range.empty else 0
                        _add_trace(
                            hovertemplate="Скорость: %{y:} шт.",
                            row=3,
                            x=x,
                            range=[
                                x_range * min_range_ratio or min_range,
                                x_range * max_range_ratio or max_range,
                            ],
                            showlegend=False,
                            y_title='Средняя скорость, шт'
                        )

                        x = camera_side_df["pcs_rejected"]
                        min_range, max_range = -5, 100
                        _add_trace(
                            hovertemplate="выброс: %{y:} шт.",
                            row=4,
                            x=x,
                            range=[
                                x.max() * min_range_ratio or min_range,
                                x.max() * max_range_ratio or max_range,
                            ],
                            showlegend=False,
                            y_title='Динамика выброса, шт',

                        )

                    fig.update_layout(
                        title=f"Line: {line} Shift: {shift}",
                        margin=dict(l=10, r=10, t=30, b=10),
                        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                    )
                    fig.update_traces(xaxis='x4')

                    line_by_shift_list[line][shift] = self.graph_to_json(fig)
        return line_by_shift_list

    def _parse_camera(self):
        """График выпуска камеры. Принимает запрос из ``ibea_agregate`` на ``EN-VM01``"""

        df_line_list, df_camera_list = [], []
        camera_result_df = pd.DataFrame([])

        # запрос под каждую камеру и добавление поля брака
        for line in self.lines:
            if line in IBEA_CAMERA_MAP:
                camera_data = Camera.get_camera_info(self.date_start, self.date_end, line)
                df_camera_lvl_0 = pd.DataFrame(list(camera_data))
                df_line_list.append(df_camera_lvl_0)
        camera_line_df = pd.concat(df_line_list)

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

            camera_result_df = pd.concat(df_camera_list)
        return camera_result_df


    def summary_report(self):
        camera_df = self._parse_camera()

        try:
            camera_df['date'] = camera_df['date_now_sys'].apply(lambda x: x - timedelta(days=1)
                                                                if x.hour < 6 else x).dt.date
            df = pd.pivot_table(
                data=camera_df,
                index=['date', 'shift', 'line', 'line_side', 'job'],
                values=['pcs_total', 'pcs_rejected'],
                aggfunc='sum'
            ).reset_index()
            df['percent'] = df['pcs_rejected']/df['pcs_total'] * 100
            df.fillna(0, inplace=True)

            df['percent'] = df['percent'].apply(lambda x: '{:.2f}'.format(x))
        except KeyError as e:
            return ''
        return self.df_to_html(df)

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
    def add_nodata_annotation(fig, row):
        """
        Добавляет плашку NO DATA в центре пустого графика.

        :param row: Номер ряда
        :param fig: plotly figure
        """
        fig.add_annotation(
            x=0.5,
            y=0.5,
            xref="x domain",
            yref="y domain",
            showarrow=False,
            text="NO DATA",
            col=1,
            row=row,
        )

    def df_to_html(self, df):

        html = (
            df.style.format()
                .set_properties(
                **{
                    "padding": "0 5px 0 5px",
                    "border-bottom": "1px solid #e0e0e0",
                    "text-align": "right",
                    "border": "solid black 1px",
                    "font-weight": "500"
                }
            ).hide_index().render()
        )

        return html