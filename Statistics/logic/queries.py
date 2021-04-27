from __future__ import annotations

from Statistics.models import as_line_speed, as_material_data


def get_order_description(orders: set, cut: int = 40) -> dict:
    """Функция принимает множество(список уникальных значений) заказов и возвращает словарь"""

    description = {}

    for order in orders:
        try:
            if order != "00000":

                # индекс заказа
                index = (
                    as_line_speed.query.filter(as_line_speed.order == order)
                    .first()
                    .index
                )

                # описание заказа
                description_str = (
                    as_material_data.query.filter(as_material_data.index == index)
                    .first()
                    .full_name
                )

                # если длина описания больше cut, то обрезать его
                description[order] = (
                    description_str
                    if len(description_str) <= cut
                    else f"{description_str[:cut]}..."
                )

        except:
            description[order] = "Описание не найдено"

    return description