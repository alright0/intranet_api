# TODO: удалить лишние импорты
import calendar
import json
import math
from datetime import date, datetime, timedelta

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


# TODO: разделись методы на таблицы и графики
class up_puco_table:
    """Класс возвращает представления таблицы up_puco_export по датам и линиям.\n
    входные параметры:\n
    ``date`` - datetime - дата, за которую необходимо получить отчет. \n
        По умолчанию идет предыщуший день или текущий месяц\n
    ``period`` - str - ``'month'``, ``'day'`` - день или месяц. По умолчанию ``"month"``\n
    ``delta` - int - количество дней/месяцев от указанной даты. По умолчанию 1\n
    ``lines`` - list - список линий, которые необходимо отобразить.\n
        По умолчанию все линии\n
    """

    # NOTE: Конструктор класса
    def __init__(
        self,
        date=datetime.today() - timedelta(days=1),
        period="month",
        delta=1,
        lines=LINES,
    ):
        self.date = date
        self.period = period
        self.delta = delta
        self.lines = lines

    # NOTE: парсинг периодов входящей даты
    def __parsedata(self):
        """Приватная функция, реализующая парсинг даты для последующего формирования запоса\n
        Возвращает словарь значений дат, для передачи в функции формирования запроса(SQL)\n
        и итоговой выборки(Pandas).\n
        Возвращает словарь значений:\n
        ``"date_start"``: ``dt_start`` - datetime - если период равен месяцу, датой старта будет считаться\n
            первое число месяца указаное во входящей дате(self.date), если день, то возвращается\n
            дата без изменений.\n
        ``"date_end"``: ``dt_end``, - datetime - если период равен месяцу, то датой конца будет первое число\n
            следующего месяца. Если self.delta > 1, то прибавляется количество месяцев\n
        ``"date_start_sql"``: ``date_start_sql`` - str - преобразует dt_start из вида "25-02-2021" в "20210225"\n
        ``"date_end_sql"``: ``date_end_sql`` - str - dt_end + 1 день. Такое дополнение необходимо из-за того, что\n
            ночная смена заканчивается в 8:00 следующего дня, но выборка времени(dt_start, dt_end) должна содежрать\n
            только актуальные даты, отсекая лишние значения. Возвращает дату в формате "20210225"
        """

        dt_start = datetime(
            self.date.year,
            self.date.month,
            1 if self.period == "month" else self.date.day,
        )

        if self.period == "month":

            dt_end = (
                datetime(
                    dt_start.year,
                    dt_start.month,
                    1,
                )
                + relativedelta(months=self.delta - 1)
            )

            dt_end = datetime(
                dt_end.year,
                dt_end.month,
                calendar.monthrange(dt_end.year, dt_end.month)[1],
            )

        elif self.period == "day":

            dt_end = dt_start + relativedelta(days=self.delta - 1)

        # превращение даты из формата 2021-03-01 00:00:00 в 20210301
        date_start_sql = f"{str(dt_start)[:4]}{str(dt_start)[5:7]}{str(dt_start)[8:10]}"

        date_end_sql = dt_end + timedelta(days=1)
        date_end_sql = (
            f"{str(date_end_sql)[:4]}{str(date_end_sql)[5:7]}{str(date_end_sql)[8:10]}"
        )

        return {
            "date_start": dt_start,
            "date_end": dt_end,
            "date_start_sql": date_start_sql,
            "date_end_sql": date_end_sql,
        }

    # NOTE: на основе этого фрейма строятся все остальные
    def __get_df_lvl_0(self, line):
        """Принимает запрос из ``up_puco_export`` на ``EN-DB05`` и
        возвращает обработанный DataFrame готовый к\n
        дальнейшей обработке, построению таблиц и графиков\n
        Пример возвращаемого фрейма:\n
            line  order  counter_start  counter_end  shift puco_code  sheets           date_stop status         minutes
        0     LZ-01  10117            682        52066      2     OGE04       0 2021-03-01 00:21:28   STOP 0 days 00:01:35
        1     LZ-01  10117            682        52672      2       RUN     606 2021-03-01 00:21:40    RUN 0 days 00:00:12
        2     LZ-01  10117            682        52672      2     OGE04       0 2021-03-01 00:22:47   STOP 0 days 00:01:07
        3     LZ-01  10117            682        53050      2       RUN     378 2021-03-01 00:22:53    RUN 0 days 00:00:06
        """
        dates = self.__parsedata()

        df_lvl_0 = pd.DataFrame(
            up_puco_export.get_production_info(
                dates["date_start_sql"], dates["date_end_sql"], line
            )
        )

        if not df_lvl_0.empty:

            # преобразование дата финиша из текста в дату
            df_lvl_0["end_date"] = pd.to_datetime(df_lvl_0["end_date"], format="%Y%m%d")

            # Преобразование даты старта из текста в дату
            df_lvl_0["start_date"] = pd.to_datetime(
                df_lvl_0["start_date"], format="%Y%m%d"
            )

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
            df_lvl_1["minutes"] = (
                df_lvl_1["date_stop"].diff().fillna(pd.Timedelta(days=0))
            )

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

            df_lvl_1["status"] = df_lvl_1["status"].apply(
                lambda x: "RUN" if x else "STOP"
            )
            df_lvl_1["puco_code"] = df_lvl_1[["puco_code", "status"]].apply(
                lambda x: "RUN" if x[1] == "RUN" else x, axis=1
            )

            # переразметка дат под соответствие сменам. Если смена переходит из одного
            # дня в другой, то дату необходимо сместить на 8 часов, иначе ничего не менять
            df_lvl_1["shift"] = df_lvl_1[["shift", "date_stop"]].apply(
                lambda x: 1 if x[1].hour >= 8 and x[1].hour < 20 else 2,
                axis=1,
            )

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

            return df_lvl_1
        else:

            return pd.DataFrame([])

    # NOTE: эта функция размечает даты буквами смен
    def __month_range(self, dt_start, dt_end):
        """Приватная функция принимает даты ``date_start`` и ``date_end`` из ``__parsedata``\n
        и возвращает DataFrame следующего вида:
                date_stop  shift letter
        0   2021-03-01      1      A
        1   2021-03-01      2      D
        2   2021-03-02      1      A
        Из-за особенностей производства, переходя через новый год, порядок смен может измениться\n
        Эта проблема решается, если задать переменные всего года(или периодов), в отдельные переменные\n
        и выполнять конкатенацию в порядке возрастания даты, не допуская наложения. \n
        Для добавления новой даты необхоидмо сформировать 3 переменных:\n
        ``datelist_##`` - df - список дат, дублирующихся дважды(для первой и второй смен)\n
        ``shiftlist_##`` - list - список смен содержит попеременно повторяющиеся 1 и 2 смены\n
        ``LETTER_##`` - str - список букв смен. Должен содержать паттерн перестановки смен:\n
            (прим.: "DADACDCDBCBCABAB")
        """

        # здесь формируется список дат в формате (03.03.2021 ...) для текущего месяца
        month_range = pd.date_range(start=dt_start, end=dt_end).astype(str).str[:10]
        month_range = [day for day in month_range for _ in (0, 1)]

        # список смен для df с актуальными датами
        shift_list = [1 if shift % 2 == 0 else 2 for shift in range(len(month_range))]

        """Этот список переменных можно брать и использовать для прочих периодов, если порядок смен
        будет отличаться"""
        # 2020 год
        datelist_20 = pd.date_range(start=date(2020, 1, 1), end=date(2020, 12, 31))
        datelist_20 = [str(day)[:10] for day in datelist_20 for _ in (0, 1)]

        shiftlist_20 = [1 if shift % 2 == 0 else 2 for shift in range(len(datelist_20))]

        LETTER_20 = "DADACDCDBCBCABAB" * 94

        df_2020 = pd.DataFrame(
            list(zip(datelist_20, shiftlist_20, LETTER_20)),
            columns=["date_stop", "shift", "letter"],
        )

        """Этот список переменных можно брать и использовать для прочих периодов, если порядок смен
        будет отличаться"""
        # 2021 год
        datelist_21 = pd.date_range(start=date(2021, 1, 1), end=date(2022, 1, 1))
        datelist_21 = [str(day)[:10] for day in datelist_21 for _ in (0, 1)]

        LETTER_21 = "CBDCDCADADBABACB" * 94

        shiftlist_21 = [1 if shift % 2 == 0 else 2 for shift in range(len(datelist_21))]

        df_2021 = pd.DataFrame(
            list(zip(datelist_21, shiftlist_21, LETTER_21)),
            columns=["date_stop", "shift", "letter"],
        )

        # Сюда добавляются все периоды смен, в хронологическом порядке
        full_date_df = pd.concat([df_2020, df_2021])

        # этот месяц
        this_month_df = pd.DataFrame(
            list(zip(month_range, shift_list)), columns=["date_stop", "shift"]
        )

        # смерживание выбранного актуального периода с паттернами смен
        df = pd.merge(
            this_month_df,
            full_date_df,
            how="inner",
            left_on=["date_stop", "shift"],
            right_on=["date_stop", "shift"],
        )

        return df

    # NOTE: функция оформления таблицы
    def __line_green(self, val):
        """Окрашивает выпуск линий больше 100% в зеленый"""

        return [
            "color: green; font-weight:bold" if v > LINE_OUTPUT[val.name] else ""
            for v in val
        ]

    # NOTE: функция оформления таблицы
    def __line_red(self, val):
        """Окрашивает выпуск линий меньше 25% в красный"""

        return [
            "color: red; font-weight:bold"
            if v < LINE_OUTPUT[val.name] / 4 and v > 0
            else ""
            for v in val
        ]

    # NOTE: функция оформления таблицы
    def __line_max(self, val):
        """Выделяет смену с максимальным выпуском"""

        # Сначала создается массив значений, совпадающих с максимальным,
        # затем выделяются ненулевые значения, чтобы линии в начале месяца
        # не светили желтым. Далее эти значения сравниваются
        is_max = val == val.max()
        is_null = [v for v in val]

        real_max = is_max & is_null

        return [
            "background-color: yellow; font-weight:bold; color: blue;" if v else ""
            for v in real_max
        ]

    def get_month_table(self):
        """Возвращает DataFrame с датами, номерами и буквами смен. На основе этого фрема\n
        формируются все остальные таблицы и графики.

        Пример возвращаемого фрейма:\n
             date_stop  shift letter  LL-01  LL-02   LN-01  LN-03  LP-01   LZ-01  LZ-02   LZ-03   LZ-04
        0   01.03.2021      1      A      0  44872  418170      0  14952  170351      0  460491       0
        1   01.03.2021      2      D      0   3767  419534      0      0  240088      0  470987  472896
        2   02.03.2021      1      A      0      0  241987      0  14939  197841      0  151382  193350



        """

        # переопределение даты для запроса в df_lvl_0
        dates = self.__parsedata()

        # получение df размеченных дней смерживания с датами выпуска
        date_df = self.__month_range(dates["date_start"], dates["date_end"])

        df_list, line_list = [], []

        # создание таблицы с указанными линими
        for line in self.lines:

            df = self.__get_df_lvl_0(line)

            if not df.empty:

                df[line] = df["sheets"]

                del df["sheets"]

                df_list.append(df)

                df2 = pd.concat(df_list)

                line_list.append(line)

            else:
                df2 = pd.DataFrame(
                    [],
                    columns=[
                        "line",
                        "order",
                        "counter_start",
                        "counter_end",
                        "shift",
                        "puco_code",
                        "date_stop",
                        "minutes",
                        "status",
                        "date",
                        "sheets",
                    ],
                )

        if not df2.empty:
            # превращение подробной таблицы в таблицу с суммарным выпуском по датам
            df2 = pd.pivot_table(
                df2,
                index=[df2["date"], "shift"],
                values=line_list,
                aggfunc="sum",
            ).reset_index()

            df2["date"] = df2["date"].astype(str)

            # добавление букв смены
            df3 = pd.merge(
                date_df,
                df2,
                how="left",
                left_on=["date_stop", "shift"],
                right_on=["date", "shift"],
            )

            df3.fillna(0, inplace=True)

            del df3["date"]

            # Преобразование показателей выпуска линий в int из float
            for line in line_list:
                df3[line] = df3[line].astype(int)

            # даты из формата 2021/01/02 в 02.01.2021
            df3["date_stop"] = df3["date_stop"].apply(
                lambda x: datetime.strftime(
                    datetime.strptime(x, "%Y-%m-%d"), "%d.%m.%Y"
                )
            )

            return df3

        else:

            return date_df

    def subplots(self, df2):

        df3 = df2.copy()

        line_list = list(df3.columns.values)[3:]

        df3 = df3.sort_index().sort_values("letter", kind="mergesort")

        if len(line_list) >= 5:
            cols = 5
        elif len(line_list) == 0:
            cols = 1
        else:
            cols = len(line_list)

        fig2 = make_subplots(
            cols=cols,
            rows=math.ceil(math.ceil(len(line_list) / 5)) if len(line_list) > 0 else 1,
            start_cell="bottom-left",
            subplot_titles=line_list,
            vertical_spacing=0.15,
            x_title="Смена",
            y_title="Выпуск",
        )

        for i in range(len(line_list)):

            color_list = []

            color_list = df3[line_list[i]].apply(
                lambda x: "green"
                if x > LINE_OUTPUT[line_list[i]]
                else "firebrick"
                if x < LINE_OUTPUT[line_list[i]] / 25
                else "#003882"
            )

            fig2.add_trace(
                go.Bar(
                    x=df3["letter"],
                    y=df3[line_list[i]],
                    name=line_list[i],
                    marker_color=color_list,
                    hoverinfo="text",
                    hovertext="Дата: "
                    + df3["date_stop"].astype(str)
                    + "<br>Смена: "
                    + df3["shift"].astype(str)
                    + "<br>Выпуск: "
                    + df3[line_list[i]].astype(str),
                ),
                row=math.ceil((i + 1) / 5),
                col=math.ceil(i - 5 * (i // 5) + 1),
            )

        fig2.update_layout(
            margin=dict(t=70, l=70, b=70, r=30),
            title_text="<b>Выпуск линий по сменам</b>",
            title_font_size=16,
            title_x=0.5,
            title_y=0.98,
            showlegend=False,
            font={
                "size": 10,
            },
        )

        plot_json = json.dumps(fig2, cls=PlotlyJSONEncoder)

        return plot_json

    def date_table_average(self, df2):

        df3 = df2.copy()

        line_list = list(df3.columns.values)[3:]

        for line in line_list:

            df3[line + " shift"] = df3[line].apply(
                lambda x: 1 if x > LINE_OUTPUT[line] / 4 else 0
            )

        pivot_dict = dict()
        pivot_dict.update({line: "sum" for line in line_list})
        pivot_dict.update({line + " shift": "sum" for line in line_list})

        df3 = pd.pivot_table(
            df3, index=[df3["letter"]], values=pivot_dict, aggfunc=pivot_dict
        ).reset_index()

        line_list_av = []

        for line in line_list:

            df3[line + " average"] = df3[line] / df3[line + " shift"]

            df3.replace([np.inf, -np.inf], np.nan, inplace=True)

            df3[line + " average"].fillna(0, inplace=True)

            # print(df3)

            # df3[line + " average"] = df3[line + " average"].astype(int)

            line_list_av.append(line + " average")

        df3 = df3.reindex(sorted(df3.columns, reverse=True), axis=1)

        df_list = []
        line_dict = dict()

        for line in line_list:

            df4 = df3[["letter", f"{line} shift", f"{line} average", line]]

            df4 = df4.append(
                pd.DataFrame(
                    [
                        [
                            "ИТОГО",
                            df4[f"{line} shift"].sum(),
                            df4[f"{line} average"].mean(),
                            df4[line].sum(),
                        ]
                    ],
                    columns=list(df4.columns.values),
                ),
                ignore_index=True,
            )

            df4[line + " average"] = df4[line + " average"].astype(int)

            # df4.iloc[-1] = ["ИТОГО", df4[f"{line} shift"].sum(), "-", df4[line].sum()]

            df4 = df4.rename(
                columns={
                    "letter": "Буква",
                    f"{line} shift": "Смена",
                    f"{line} average": "Средний",
                    line: "Абс.",
                }
            )

            # print(df4)
            html = (
                df4.style.format({"Абс.": "{:,}"})
                .format({"Средний": "{:,}"})
                .apply(
                    self.__line_max, subset=pd.IndexSlice[df3.index[0:-1], ["Средний"]]
                )
                .set_properties(
                    **{"text-align": "right", "border-right": "1px solid #e0e0e0"},
                    subset="Средний",
                )
                .set_properties(
                    **{"text-align": "right"},
                    subset="Абс.",
                )
                .set_properties(
                    **{"font-weight": "600"}, subset=pd.IndexSlice[df4.index[-1]]
                )
                .set_properties(
                    **{"text-align": "center"},
                    subset=["Смена", "Буква"],
                )
                .set_properties(
                    **{
                        "padding": "0 5px 0 5px",
                        "border-bottom": "1px solid #e0e0e0",
                    }
                )
                .hide_index()
                .render()
            )

            line_dict[line] = html

        return line_dict

    def date_table(self, df2):

        df3 = df2.copy()

        df3.rename(
            columns={"date_stop": "Дата", "shift": "Cмена", "letter": "Буква"},
            inplace=True,
        )

        line_list = list(df3.columns.values)[3:]

        df3 = df3.append(
            pd.DataFrame(
                [
                    [
                        "",
                        "",
                        "ИТОГО",
                        *[df3[tot].sum() for tot in line_list],
                    ]
                ],
                columns=list(df3.columns.values),
            ),
            ignore_index=True,
        )

        # df3.iloc[-1] = ["", "", "ИТОГО:", *[df3[tot].sum() for tot in line_list]]

        html = (
            df3.style.format({line: "{:,}" for line in line_list})
            .apply(self.__line_green, subset=pd.IndexSlice[df3.index[0:-1], line_list])
            .apply(self.__line_red, subset=pd.IndexSlice[df3.index[0:-1], line_list])
            .apply(self.__line_max, subset=pd.IndexSlice[df3.index[0:-1], line_list])
            .bar(subset=pd.IndexSlice[df3.index[0:-1], line_list], color="#d4d4d4")
            .set_properties(**{"text-align": "right"}, subset=line_list)
            .set_properties(
                **{"padding": "0 5px 0 5px", "border-bottom": "1px solid #e0e0e0"}
            )
            .set_properties(
                **{"font-weight": "600"}, subset=pd.IndexSlice[df3.index[-1]]
            )
            .hide_index()
            .render()
        )

        html = html

        return html


if __name__ == "__main__":

    rep = up_puco_table()

    print(rep.__parsedata())
    print(rep.get_month_table())
