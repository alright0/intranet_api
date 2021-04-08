# TODO: удалить лишние импорты
import calendar
import json
import math
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dateutil.relativedelta import relativedelta
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder

from config import LINE_OUTPUT, LINES, IBEA_CAMERA_MAP
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

        dates = self.__parsedata()

        self.date_start = dates['date_start'] # 01.01.2021 00:00:00
        self.date_end = dates['date_end'] # 31.01.2021 00:00:00
        self.date_start_with_hours = dates['date_start_with_hours'] # 01.01.2021 00:80:00
        self.date_end_with_hours = dates['date_end_with_hours'] # 31.01.2021 00:80:00
        self.date_start_sql = dates['date_start_sql'] # 20210101
        self.date_end_sql = dates['date_end_sql'] # 20210131


    


        
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
        # Начальная дата, но день или 1(если peroid=месяц) или начальный(если peroid=день)
        dt_start = datetime(
            self.date.year,
            self.date.month,
            1 if self.period == "month" else self.date.day,
        )

        if self.period == "month":

            # Начальная дата + количество месяцев из переменной delta. Это временная переменная
            dt_end = (
                datetime(
                    dt_start.year,
                    dt_start.month,
                    1,
                )
                + relativedelta(months=self.delta - 1)
            )

            # конечная дата + последний день последнего месяца
            dt_end = datetime(
                dt_end.year,
                dt_end.month,
                calendar.monthrange(dt_end.year, dt_end.month)[1],
            )

        elif self.period == "day":

            # конечная дата + количество дней из переменной delta.
            dt_end = dt_start + relativedelta(days=self.delta - 1)

        # начальная и конечная даты с указанием часов
        date_start_with_hours = dt_start + timedelta(hours=8)
        date_end_with_hours = dt_end + timedelta(days=1, hours=8)
        
        
        # превращение даты из формата 2021-03-01 00:00:00 в 20210301
        date_start_sql = f"{str(dt_start)[:4]}{str(dt_start)[5:7]}{str(dt_start)[8:10]}"

        date_end_sql = (
            f"{str(date_end_with_hours)[:4]}{str(date_end_with_hours)[5:7]}{str(date_end_with_hours)[8:10]}"
        )

        return {
            "date_start": dt_start,
            "date_end": dt_end,
            "date_start_sql": date_start_sql,
            "date_end_sql": date_end_sql,
            "date_start_with_hours":date_start_with_hours,
            "date_end_with_hours":date_end_with_hours,
        }

    def __repr__(self):

        return (f"Информация за период с {datetime.strftime(self.date_start, '%Y-%m-%d')} " +
        f"по {datetime.strftime(self.date_end, '%Y-%m-%d')} по работе линий:\n{self.lines}")

    # NOTE: на основе этого фрейма строятся все остальные
    def __get_raw_df_by_line(self, line):
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
        

        raw_df_by_line = pd.DataFrame(
            up_puco_export.get_production_info(
               self.date_start_sql, self.date_end_sql, line
            )
        )

        if not raw_df_by_line.empty:

            # преобразование дата финиша из текста в дату
            raw_df_by_line["end_date"] = pd.to_datetime(raw_df_by_line["end_date"], format="%Y%m%d")

            # Преобразование даты старта из текста в дату
            raw_df_by_line["start_date"] = pd.to_datetime(
                raw_df_by_line["start_date"], format="%Y%m%d"
            )

            # Смена
            raw_df_by_line["shift"] = pd.to_numeric(raw_df_by_line["shift"])

            # преобразование значения датчика входа в цифровой вид
            raw_df_by_line["counter_start"] = pd.to_numeric(raw_df_by_line["counter_start"])

            # преобразование значения датчика выхода в цифровой вид
            raw_df_by_line["counter_end"] = pd.to_numeric(raw_df_by_line["counter_end"])

            # форматирование кода остановки. Отрезание первых трех нулей
            raw_df_by_line["puco_code"] = raw_df_by_line["puco_code"].str[3:]

            # форматирование номера заказа. отрезание первых трех нулей
            raw_df_by_line["order"] = raw_df_by_line["order"].str[3:]

            # форматирование времени старта простоя
            raw_df_by_line["start_time"] = raw_df_by_line["start_time"].str[2:]
            raw_df_by_line["start_time"] = (
                raw_df_by_line["start_time"].str[:2]
                + ":"
                + raw_df_by_line["start_time"].str[2:4]
                + ":"
                + raw_df_by_line["start_time"].str[4:].replace("60", "59")
            )

            # форматирование времени финиша простоя
            raw_df_by_line["end_time"] = raw_df_by_line["end_time"].str[2:]
            raw_df_by_line["end_time"] = (
                raw_df_by_line["end_time"].str[:2]
                + ":"
                + raw_df_by_line["end_time"].str[2:4]
                + ":"
                + raw_df_by_line["end_time"].str[4:].replace("60", "59")
            )

            # конкатенция даты и времени начала остановки
            raw_df_by_line["date_start_time"] = pd.to_datetime(
                raw_df_by_line["start_date"].astype(str) + " " + raw_df_by_line["start_time"]
            )

            # конкатенация даты и времени конца остановки
            raw_df_by_line["date_end_time"] = pd.to_datetime(
                raw_df_by_line["end_date"].astype(str) + " " + raw_df_by_line["end_time"]
            )

            # получение времени простоя из разницы дат начала и конца
            raw_df_by_line["stop_minutes"] = (
                (raw_df_by_line["date_end_time"] - raw_df_by_line["date_start_time"])
                .astype("timedelta64[s]")
                .astype(int)
            )

            # отрезание отрицетельных остановок(время начала меньше времени окончания)
            raw_df_by_line = raw_df_by_line.loc[(raw_df_by_line["stop_minutes"] > 1)]

            del raw_df_by_line["start_date"]
            del raw_df_by_line["start_time"]
            del raw_df_by_line["end_date"]
            del raw_df_by_line["end_time"]

            raw_df_by_line.sort_values(by=["date_start_time"], inplace=True)

            raw_df_by_line = raw_df_by_line.loc[
                (raw_df_by_line["date_start_time"] < raw_df_by_line["date_end_time"])
            ]

            # разделение на коды выпуска и остановки
            temp_df = raw_df_by_line.copy()

            raw_df_by_line["date_stop"] = raw_df_by_line["date_start_time"]
            temp_df["date_stop"] = temp_df["date_end_time"]

            final_df_by_line = [raw_df_by_line, temp_df]
            final_df_by_line = pd.concat(final_df_by_line)

            del final_df_by_line["date_start_time"]
            del final_df_by_line["date_end_time"]
            del final_df_by_line["stop_minutes"]

            final_df_by_line = final_df_by_line.sort_values(by=["date_stop", "counter_end"])

            # время события
            final_df_by_line["minutes"] = (
                final_df_by_line["date_stop"].diff().fillna(pd.Timedelta(days=0))
            )

            final_df_by_line = final_df_by_line.loc[(final_df_by_line["minutes"].dt.seconds > 1)]

            final_df_by_line["sheets"] = (
                final_df_by_line["counter_end"].diff().fillna(0).clip(lower=0).astype(int)
            )

            # фильтрация значений стопов. В данной базе стоп может быть нуленвым или
            # отрицательным если остановка короткая. Это стоит фильтровать.
            final_df_by_line = final_df_by_line.loc[(final_df_by_line["minutes"].dt.seconds > 0)].reset_index(
                drop=True
            )

            final_df_by_line["status"] = (
                final_df_by_line["counter_start"].diff().fillna(0).clip(lower=0).astype(int)
            )

            final_df_by_line["status"] = final_df_by_line["status"].apply(
                lambda x: "RUN" if x else "STOP"
            )
            final_df_by_line["puco_code"] = final_df_by_line[["puco_code", "status"]].apply(
                lambda x: "RUN" if x[1] == "RUN" else x, axis=1
            )

            # переразметка дат под соответствие сменам. Если смена переходит из одного
            # дня в другой, то дату необходимо сместить на 8 часов, иначе ничего не менять
            final_df_by_line["shift"] = final_df_by_line[["shift", "date_stop"]].apply(
                lambda x: 1 if x[1].hour >= 8 and x[1].hour < 20 else 2 if x[0] !=0 else 0,
                axis=1,
            )

            final_df_by_line["date"] = (
                final_df_by_line[["date_stop", "shift"]]
                .apply(
                    lambda x: x[0]
                    if x[0] > datetime(x[0].year, x[0].month, x[0].day, 8) or x[1] == 1 or x[1]==0
                    else x[0] - timedelta(hours=8),
                    axis=1,
                )
                .astype(str)
                .str[:10]
            )

            return final_df_by_line
        else:

            return pd.DataFrame([])

    # NOTE: эта функция размечает даты буквами смен
    def __month_range(self):
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

        def make_list_of_dates(start_of_period, end_of_period, letter_pattern="None"):
            """Эта функция возвращает df с расчитанным периодом дат, смен и букв смены"""

            period_pattern = pd.date_range(start=start_of_period, end=end_of_period)
            period_pattern = [str(day)[:10] for day in period_pattern for _ in (0, 1)]
            
            shift_pattern = [1 if shift % 2 == 0 else 2 for shift in range(len(period_pattern))]
            
            letter_pattern = letter_pattern*(len(period_pattern)//len(letter_pattern)+1)

            return pd.DataFrame(
            list(zip(period_pattern, shift_pattern, letter_pattern)),
            columns=["date_stop", "shift", "letter"],
        )

        #посчитать смены за весь период
        period_2020 = make_list_of_dates(date(2020, 1, 1),date(2020, 12, 31),"DADACDCDBCBCABAB")
        period_2021 = make_list_of_dates(date(2021, 1, 1),date(2022, 1, 1),"CBDCDCADADBABACB")

        # Сюда добавляются все периоды смен, в хронологическом порядке
        full_date_df = pd.concat([period_2020, period_2021])

        period_now = make_list_of_dates(self.date_start,self.date_end)

        # смерживание выбранного актуального периода с паттернами смен
        result_dates_df = pd.merge(
            period_now,
            full_date_df,
            how="inner",
            left_on=["date_stop", "shift"],
            right_on=["date_stop", "shift"],
            suffixes=("_delete","")
        )

        del result_dates_df['letter_delete']

        return result_dates_df

    # NOTE: функция оформления таблицы
    @staticmethod
    def line_green(val):
        """Окрашивает выпуск линий больше 100% в зеленый"""

        return [
            "color: green; font-weight:bold" if v > LINE_OUTPUT[val.name] else ""
            for v in val
        ]

    # NOTE: функция оформления таблицы
    @staticmethod
    def line_red(val):
        """Окрашивает выпуск линий меньше 25% в красный"""

        return [
            "color: red; font-weight:bold"
            if v < LINE_OUTPUT[val.name] / 4 and v > 0
            else ""
            for v in val
        ]

    # NOTE: функция оформления таблицы
    @staticmethod
    def line_max(val):
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

    # NOTE: Эта функция создает таблицу со списком дат и линий
    def get_month_table(self):
        """Возвращает DataFrame с датами, номерами и буквами смен. На основе этого фрема\n
        формируются все остальные таблицы и графики.\n
        Пример возвращаемого фрейма(линии опциональны):\n
             date_stop  shift letter  LL-01  LL-02   LN-01  LN-03  LP-01   LZ-01  LZ-02   LZ-03   LZ-04
        0   01.03.2021      1      A      0  44872  418170      0  14952  170351      0  460491       0
        1   01.03.2021      2      D      0   3767  419534      0      0  240088      0  470987  472896
        2   02.03.2021      1      A      0      0  241987      0  14939  197841      0  151382  193350
        """


        # получение df размеченных дней смерживания с датами выпуска
        date_df = self.__month_range()

        df_list, line_list = [], []

        # Фреймы здесь необходимо создать, на случай, если список линий будет пустым
        # и они не будут добавлены в цикле
        df, df2 = pd.DataFrame([]), pd.DataFrame([])

        # создание таблицы с указанными линими
        for line in self.lines:

            """Поскольку начальный фрейм построен так, что каждое обращение в базу касается
            только одной линии, то запросы, находящиеся в __get_raw_df_by_line должны выполняться в цикле"""
            df = self.__get_raw_df_by_line(line)

            if not df.empty:

                df[line] = df["sheets"]
                del df["sheets"]

                df_list.append(df)
                df2 = pd.concat(df_list)

                line_list.append(line)

        # если пришел пустой список линий, то назад вернется только список дат, смен и букв
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
            ).fillna(0)

            del df3["date"]

            # Преобразование показателей выпуска линий в int из float
            df3[line_list] = df3[line_list].astype(int)

            # даты из формата 2021/01/02 в 02.01.2021
            df3["date_stop"] = df3["date_stop"].apply(
                lambda x: datetime.strftime(
                    datetime.strptime(x, "%Y-%m-%d"), "%d.%m.%Y"
                )
            )

            return df3

        else:
            return date_df

    # NOTE: функция возвращает список линий, находящихся в экземпляре
    @staticmethod
    def __get_line_list(df):
        """Принимает фрейм из get_month_table и возвращает список линий, который в нем находится"""

        line_list = []

        for line in LINES:
            if line in list(df.columns.values):
                line_list.append(line)

        line_list.sort()

        return line_list

    # NOTE: Строит bar график линий c подсветкой выработки
    def subplots(self, df2, style='original'):
        """Эту функцию можно вызвать, чтобы построить график линий за даты,
        указанные в экземпляре классa. Функция принимает на вход фрейм экземпляра и
        возвращает json для построения в plotly.js
        """

        df3 = df2.copy()

        line_list = self.__get_line_list(df3)

        # первая и последняя даты для заголовка графика
        date_start_str = df3['date_stop'].iloc[0]
        date_end_str = df3['date_stop'].iloc[-1]

        df3 = df3.sort_index().sort_values("letter", kind="mergesort")

        # расчет количества столбцов графиков, по умолчанию, если графиков больше 5, то
        # перейти на следующую строку
        if len(line_list) >= 5:
            cols = 5
        elif len(line_list) == 0:
            cols = 1
        else:
            cols = len(line_list)

        # создание тела графика.
        fig2 = make_subplots(
            cols=cols,
            rows=math.ceil(math.ceil(len(line_list) / 5)) if len(line_list) > 0 else 1,
            start_cell="bottom-left",
            subplot_titles=line_list,
            vertical_spacing=0.15,
            x_title="Смена",
            y_title="Выпуск",
        )

        # наполнение тела графиками.
        for i in range(len(line_list)):

            # позиционирование графика в subplots
            row=math.ceil((i + 1) / 5)
            col=math.ceil(i - 5 * (i // 5) + 1)


            # раскрашивание в зависимости от выработки
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
                    x=df3['letter'],
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
                row=row,
                col=col,
                )
        
            
            # обновление осей - добавление количества смен
            xaxis_tick_df = df3.loc[df3[line_list[i]]>0]
            xaxis_tick_df = pd.pivot_table(xaxis_tick_df,index=[xaxis_tick_df["letter"]],values=[line_list[i]],aggfunc=lambda x:len(x>0),).reset_index()

            if not xaxis_tick_df.empty:
                fig2.update_xaxes(
                    ticktext=xaxis_tick_df['letter'] + ' (' + xaxis_tick_df[line_list[i]].astype(str) + ")", 
                    tickvals=xaxis_tick_df['letter'],
                    row=row,
                    col=col,)


        # дополнительное оформление
        fig2.update_layout(
            margin=dict(t=70, l=70, b=70, r=30),
            title_text="<b>Выпуск линий по сменам за период " + date_start_str + " - " + date_end_str + "</b>",
            title_font_size=16,
            title_x=0.5,
            title_y=0.98,
            showlegend=False,
            font={
                "size": 9 if style=='original' else 13,
            },
        )

        # преобразование графика в json и последующее его построение в plotly.js в templates
        plot_json = json.dumps(fig2, cls=PlotlyJSONEncoder)

        return plot_json

    # NOTE: таблица с итогами по буквам смен
    def date_table_average(self, df2):
        """ Функция принимает фрейм из ``get_line_list`` и возвращает словарь, где ключ - название линии,
        а значение - отрендеренный html, содержащий таблицу информацию по линии: буквы смены, 
        количество смен, среднюю выработку и абсолютную выработку.
        Имеет следующий вид:
            Буква	Смена	Средний	      Абс.
            A	    11	     39,945	   439,401
            B	    12	     37,569	   450,829
            C	    13	     35,426	   460,548
            D	    11	     38,363	   422,003
            ИТОГО	47	     37,826	 1,772,781 
        """

        df3 = pd.DataFrame([], columns=['date_stop','shift', 'letter', 'absolute'])

        line_list = self.__get_line_list(df2)

        line_dict = dict()

        for line in line_list:

            df3 = pd.DataFrame([])

            df3[['date_stop', 'shift', 'letter', 'absolute']] = df2[['date_stop', 'shift', 'letter', line]]

            # посчитать смену, если выпуск по ней больше 25% от нормы выработки
            df3["shift"] = df3['absolute'].apply(
                lambda x: 1 if x > LINE_OUTPUT[line] / 4 else 0
            )

            # здесь формируется основная таблица
            df3 = pd.pivot_table(
                df3, index=[df3["letter"]], values=['shift', 'absolute'], aggfunc='sum'
                ).reset_index()

            # расчет среднего
            df3["average"] = df3['absolute'] / df3["shift"]

            df3.replace([np.inf, -np.inf], np.nan, inplace=True)

            df3["average"].fillna(0, inplace=True)

            df3=df3[['letter', 'shift', 'average', 'absolute']]

            # добавление строки итогов
            df3 = df3.append(
                pd.DataFrame(
                    [
                        [
                            "TOTAL",
                            df3["shift"].sum(),
                            df3["average"].mean(),
                            df3['absolute'].sum(),
                        ]
                    ],
                    columns=list(df3.columns.values),
                ),
                ignore_index=True,
            )

            df3[['absolute', "average"]] = df3[['absolute', "average"]].astype(int)
            
            # стили
            html = (
                df3.style.format({"absolute": "{:,}"})
                .format({"average": "{:,}"})
                .apply(
                    self.line_max, subset=pd.IndexSlice[df3.index[:-1], ["average"]]
                )
                .set_properties(
                    **{"text-align": "right", "border-right": "1px solid #e0e0e0"},
                    subset="average",
                )
                .set_properties(
                    **{"text-align": "right"},
                    subset="absolute",
                )
                .set_properties(
                    **{
                        "padding": "0 10px",
                        "border-bottom": "1px solid #e0e0e0",
                    }
                )
                .set_properties(
                    **{"font-weight": "600", "border-bottom": "none"},
                    subset=pd.IndexSlice[df3.index[-1]],
                )
                .set_properties(
                    **{"text-align": "center"},
                    subset=["shift", "letter"],
                )
                .hide_index()
                .render()
            )

            line_dict[line] = html

        return line_dict

    # NOTE: таблица с деталицацией по датам и сменам. С итогами
    def date_table(self, df2):
        """Эта функция принимает фрейм из ``get_month_table`` и возвращает таблицу\n
        в виде отрендеренного html, который необходимо встроить в страницу\n 
        сформированную по датам и сменам, с буквами смен и выпуском линий.\n
        Имеет следующий вид:\n
              Дата  Cмена	Буква	LL-01	LL-02	LN-01   ...	LN-03	
        01.03.2021	    1	    A	    0  44,872 418,170   ...	    0	
        01.03.2021	    2	    D	    0   3,767 419,534   ...	    0	
        02.03.2021	    1	    A	    0	    0 241,987   ...	    0	
        02.03.2021	    2	    D	    0	    0 377,041   ...	    0	 

        """

        df3 = df2.copy()

        line_list = self.__get_line_list(df3)
        
        # переименование для заголовков на русском
        df3.rename(
            columns={"date_stop": "date"},
            inplace=True,
        )

        # строка итогов
        df3 = df3.append(
            pd.DataFrame(
                [
                    [
                        "",
                        "",
                        "TOTAL",
                        *[df3[tot].sum() for tot in line_list],
                    ]
                ],
                columns=list(df3.columns.values),
            ),
            ignore_index=True,
        )

        # создание html и стилизация.
        html = (
            df3.style.format({line: "{:,}" for line in line_list})
            .apply(self.line_green, subset=pd.IndexSlice[df3.index[0:-1], line_list])
            .apply(self.line_red, subset=pd.IndexSlice[df3.index[0:-1], line_list])
            .apply(self.line_max, subset=pd.IndexSlice[df3.index[0:-1], line_list])
            .bar(subset=pd.IndexSlice[df3.index[0:-1], line_list], color="#d4d4d4")
            .set_properties(
                **{"padding": "0 5px 0 5px", "border-bottom": "1px solid #e0e0e0", "text-align":"center"}
            )
            .set_properties(**{"text-align": "right"}, subset=line_list)
            .set_properties(
                **{"font-weight": "600", "border-bottom": "none"},
                subset=pd.IndexSlice[df3.index[-1]],
            )
            .hide_index()
            .render()
        )

        return html

    def camera_table(self):
        

        for line in self.lines:
    

            df_camera_lvl_0=pd.DataFrame(Camera.get_camera_info(self.date_start,self.date_end,line))

            df_camera_lvl_0['defect_rate'] = df_camera_lvl_0['rejected'] /df_camera_lvl_0['total']
            df_camera_lvl_0.fillna(0, inplace=True)

        print(df_camera_lvl_0)

        fig = fig = go.Figure()

        for line_side in IBEA_CAMERA_MAP['LZ-01']:
            df_camera_side = df_camera_lvl_0.loc[(df_camera_lvl_0['line_side'] == line_side)]
            df_camera_side['defect_rate']=df_camera_side['defect_rate'].apply(lambda x: 0.1 if x>0.1 else x)
            df_camera_side.sort_values(by='date_now_sys', inplace=True)
            fig.add_trace(go.Scatter(x=df_camera_side['date_now_sys'], y=df_camera_side['defect_rate']))


        fig.show()

    def camera_plot(self):
        pass

    def line_shift_report(self):


        codes_df = up_puco_code.get_puco_codes_description()


        for line in self.lines:
            df3 = self.__get_raw_df_by_line(line)
            df3['seconds'] = df3['minutes'].dt.seconds//60
            df3 = df3.loc[(df3['date_stop']>=self.date_start_with_hours) & (df3['date_stop']<=self.date_end_with_hours)]


            df3_pivot_table = pd.pivot_table(df3,index=[ 'date','shift','puco_code'], values = ['seconds'],  aggfunc='sum').reset_index()

            df3_with_description = pd.merge(
                df3_pivot_table,
                codes_df,
                how='left',
                left_on = 'puco_code',
                right_on = 'puco_code',
            )

            print(df3_with_description)
            fig = go.Figure()
            fig.add_trace(go.Pie(labels=df3_with_description['name_ru'], values=df3_with_description['seconds'], hole=.3))
            fig.update_traces(textinfo='label+value')
            fig.update_layout(annotations=[
                dict(text=line, x=0.5, y=0.5, font_size=20, showarrow=False),
            ])
        fig.show()
        

if __name__ == "__main__":

    rep = up_puco_table(lines=['LZ-1'])

    rep.camera_table()

    #print(rep.__parsedata())
    #print(rep.get_month_table())
