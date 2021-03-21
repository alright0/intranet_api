from Statistics.app import db, sessionmaker, Base_cam, Base_fc, fc_engine


class Camera(Base_cam):
    """Класс описывает таблицу ``ibea_agregate`` в ``EN-VM01``\n
    Таблица хранит данные с камер\n
    доступные поля таблицы:\n
    ``id`` - int - порядковый номер строки\n
    ``line`` - str(10) - название линии(прим.: LZ-1)\n
    ``line_side`` - str(10) - название камеры(прим.: LZ-1 A)\n
    ``date_now`` - datetime - системное время камеря\n
    ``date_now_sys`` - datetime - системное время системы\n
    ``job`` - str(50) - номер заказа(прим.: 10132)\n
    ``start_time`` - datetime - дата и время открытия смены на камере\n
    ``last_part`` - datetime - дата и время последнего прохождения крышки через камеру\n
    ``total`` - int - всего проконтролировано\n
    ``rejected`` - int - всего выброшено
    """

    __bind_key__ = "cam_engine"
    __tablename__ = "ibea_agregate"

    id = db.Column(
        db.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True
    )
    line = db.Column(db.String(10))
    line_side = db.Column(db.String(10))
    date_now = db.Column(db.DateTime)
    date_now_sys = db.Column(db.DateTime)
    job = db.Column(db.String(50))
    start_time = db.Column(db.DateTime)
    last_part = db.Column(db.DateTime)
    total = db.Column(db.Integer)
    rejected = db.Column(db.Integer)


class up_puco_export(Base_fc):
    """Класс описывает таблицу ``up_puco_export`` на ``EN-DB05``\n
    Таблица хранит все остановки всех линий\n
    Список доступных параметров:\n
    ``line`` - str - линия (прим.: ``LN-01``)\n
    ``start_date`` - str - дата начала остановки\n
    ``start_time`` - str - время начала остановки\n
    ``last_run_time`` - str - время работы между текущей остановкой и предыдущей\n
    ``end_date`` - str - дата конца остановки\n
    ``end_time`` - str - время конца остановки\n
    ``order`` - str - номер заказа\n
    ``shift`` - str - смена\n
    ``puco_code`` - str - код остановки\n
    ``counter_start`` - str - счетчик входа\n
    ``counter_end`` - str - счетчик выхода\n
    """

    __bind_key__ = "fc_engine"
    __tablename__ = "up_puco_export"

    line = db.Column("a1", db.String)
    not_used_0 = db.Column("a2", db.String, unique=True, primary_key=True)
    not_used_1 = db.Column("a3", db.String)
    start_date = db.Column("a4", db.String)
    start_time = db.Column("a5", db.String)
    last_run_time = db.Column("a6", db.String)
    end_date = db.Column("a7", db.String)
    end_time = db.Column("a8", db.String)
    order = db.Column("a9", db.String)
    not_used_2 = db.Column("a10", db.String)
    not_used_3 = db.Column("a11", db.String)
    shift = db.Column("a12", db.String)
    not_used_4 = db.Column("a13", db.String)
    puco_code = db.Column("a14", db.String)
    not_used_5 = db.Column("a15", db.String)
    counter_start = db.Column("a16", db.String)
    counter_end = db.Column("a17", db.String)
    not_used_6 = db.Column("a18", db.String)


class LineStatus(Base_fc):
    """Класс описывает таблицу ``up_line_def`` на ``EN-DB05``\n
    Таблица хранит текущее состояние линий\n
    Список доступных параметров:\n
    ``line_name`` - str - название линии(прим.: LZ-01)\n
    ``order`` - str - номер заказа(прим.: 11012)\n
    ``shift`` - str/int - номер смены. Может быть ``0``,``1`` или ``2``.
        0 - линия не работает
        1 - дневная смена
        2 - ночная смена
    ``line_status`` - bool - запущена ли сейчас подача\n
    ``counter_start`` - int - счетчик входа\n
    ``counter_end`` - int - счетчик выхода\n
    ``stop_time`` - int - время простоя в минутах. Макс 1440\n
    ``puco_code`` - str - код PUCO(прим.: 000OGE04)\n
    Доступные методы:\n
    ``get_line_param`` - принимает название линию и возвращает список доступных параметров по ней
    """

    __bind_key__ = "fc_engine"
    __tablename__ = "up_line_def"

    not_used_0 = db.Column("nr_line", db.Text)
    line_name = db.Column("fc_line", db.Text, unique=True, primary_key=True)
    order = db.Column("prod_order", db.Text)
    shift = db.Column(db.Text)
    line_status = db.Column("starus_line", db.Integer)
    not_used_1 = db.Column("puco_need", db.Integer)
    not_used_2 = db.Column("puco_code", db.Integer)
    counter_start = db.Column(db.Integer)
    counter_end = db.Column(db.Integer)
    stop_time = db.Column(db.Integer)
    puco_code = db.Column("puco_string", db.Text)
    not_used_3 = db.Column("qv_name", db.Text)
    not_used_4 = db.Column("id_worker", db.Integer)
    not_used_5 = db.Column("id_master_plc", db.VARCHAR(8))
    not_used_6 = db.Column("local_name", db.VARCHAR)

    @classmethod
    def get_line_param(self, line):

        return LineStatus.query.filter(self.line_name == line).first()

    # TODO: Заменить на join.
    @classmethod
    def get_status(self, line):
        """Этот метод возвращает статус линии: работает ли она, стоит с кодом остановки или не работает"""

        line_status = LineStatus.get_line_param(line)

        status = line_status.puco_code[3:]
        feed = line_status.stop_time

        if status == "00000" and not feed:
            description = "RUN"
        elif status == "00000" and feed:
            description = f"Причина не определена. {feed} минут(ы)"
        else:
            description = f"""{(
                up_puco_code.query.with_entities(up_puco_code.name_ru)
                .filter(up_puco_code.code == status)
                .first()[0]
            )}. {feed} минут(ы)"""

        return description


class as_line_speed(Base_fc):

    __bind_key__ = "fc_engine"
    __tablename__ = "as_line_speed"

    order = db.Column("po_id", db.Text, unique=True, primary_key=True)
    index = db.Column("product_id", db.VARCHAR)
    line = db.Column("line_id", db.VARCHAR)
    not_used_0 = ("line_speed", db.Integer)
    not_used_1 = ("usage", db.Integer)


class as_material_data(Base_fc):
    """Класс описывает таблицу ``as_material_data`` на ``EN-DB05``\n
    таблица хранит информацию о материалах, находящихся или находившихся на складе\n
    Список доступных полей:\n
    ``code`` - str - уникальный код 1С (прим:. 000004517)\n
    ``index`` - str - Внутренний артикул компании (прим:. 5-05-0-354-0-00002).
        Хорошо работает для жести и выпускаемых продуктов\n
    ``full_name`` - str - международное название (прим.: HFCP  BLK/White).
        Хорошо работает для жести и выпускаемых продуктов\n
    ``unit_ru`` - единицы измерения на русском языке(прим:. кг, шт)\n
    ``name`` - название продукта на русском языке(прим:. Стопорная шайба)\n
    ``name2`` - то же самое, что и name\n
    ``unit_en`` - единицы измерения на английском языке\n
    ``quantity`` - количество на складе
    """

    __bind_key__ = "fc_engine"
    __tablename__ = "as_material_data"

    code = db.Column(db.VARCHAR, unique=True, primary_key=True)
    index = db.Column("article", db.VARCHAR)
    full_name = db.Column("the_name_of_the_holding_company", db.VARCHAR)
    unit_ru = db.Column("unit", db.VARCHAR)
    name = db.Column(db.VARCHAR)
    not_used_0 = db.Column("full_name", db.VARCHAR)
    unit_en = db.Column("international_name_of_the_unit", db.VARCHAR)
    quantity = db.Column("on_stock", db.NUMERIC)
    not_used_1 = db.Column("libra_of_unit", db.VARCHAR)
    not_used_2 = db.Column("volume_of_unit", db.VARCHAR)
    not_used_3 = db.Column("material_type", db.VARCHAR)
    not_used_4 = db.Column("valuation_class", db.VARCHAR)
    not_used_5 = db.Column("material_format", db.VARCHAR)
    not_used_6 = db.Column("qv_product_code", db.Integer)
    not_used_7 = db.Column("plate_add_info", db.VARCHAR)
    not_used_8 = db.Column("source_material", db.Integer)


class up_puco_code(Base_fc):
    """Класс описывает таблицу ``up_puco_code`` на ``EN-DB05``\n
    таблица хранит описание кодов пуко\n
    Список доступных параметров:\n
    ``code`` - str - код остановки(прим.: OGE04)\n
    ``name_eng`` - str - описание на английском\n
    ``name_ru`` - str - описание на русском\n
    ``group_eng`` - str - Название узла на англисйком(прим:. general, parter etc.)\n
    ``group_ru`` - str - название узла на русском(прим.: основные, партер и т.д.)\n
    ``id_line`` - str - список подходящих к этому коду линий\n
    """

    __bind_key__ = "fc_engine"
    __tablename__ = "up_puco_code"

    code = db.Column("id_code", db.String, primary_key=True)
    name_eng = db.Column(db.String)
    name_ru = db.Column(db.String)
    group_eng = db.Column(db.String)
    group_ru = db.Column(db.String)
    id_line = db.Column(db.String)


class fc_produkcja(Base_fc):
    """Класс описывает таблицу ``fc_produkcja`` на ``EN-DB05``\n
    таблица хранит список заказов, даты начала и конца заказа,\n
    код исполняющего оператора, выпуск по заказу и т.п.\n
    смотреть в этой таблице нечего, она нужна как промежуточная для\n
    получения имени текущего оператора на линии
    Список доступных параметров:\n
    ``order`` - str - номер заказа\n
    ``operator_id`` - str - код оператора\n
    ``order_start`` - timestamp - дата начала выполнения заказа\n
    ``order_end`` - timestamp - дата конца выполнения заказа\n
    ``line_name`` - str - название линии(прим:. LN-01)\n
    ``finished`` - float - выпуск по заказу(прим.: 2342,000)\n
    ``active_order`` - активен ли заказ(``1`` - на линии, ``0`` - нет)\n
    """

    __bind_key__ = "fc_engine"
    __tablename__ = "fc_produkcja"

    order = db.Column("kod_rejestr", db.VARCHAR)
    not_used_0 = db.Column("aktyw_produkcja", db.Integer)
    operator_id = db.Column("id_brygadz", db.VARCHAR)
    order_start = db.Column("data_uruch_zmiana", db.DateTime)
    order_end = db.Column("data_zakoncz_zmiana", db.DateTime)
    line_name = db.Column("kod_maszyny", db.VARCHAR, primary_key=True)
    not_used_1 = db.Column("nr_opakowania", db.Integer)
    finished = db.Column("ilosc_na_zmianie", db.NUMERIC)
    not_used_2 = db.Column("aktywna_linia", db.Integer)
    active_order = db.Column("status_aktywnosci_zmiany", db.Integer)
    not_used_3 = db.Column("ilosc_paczek", db.Integer)
    not_used_4 = db.Column("ilosc_w_paczce", db.NUMERIC)
    not_used_5 = db.Column("nr_paczki", db.Integer)
    not_used_6 = db.Column("paczki_niepelne", db.Integer)
    not_used_7 = db.Column("rejestr_dla_paczek", db.VARCHAR)
    not_used_8 = db.Column("kod_kreskowy_zbiorczy", db.VARCHAR)


class fc_users(Base_fc):
    """Класс описывает таблицу ``fc_users`` на ``EN-DB05``\n
    Таблица хранит список пользователей(операторов)\n
    Список доступных параметров:\n
    ``user_id`` - str - код оператора (прим.: ``065``)\n
    ``first_name`` - str - имя оператора \n
    ``last_name`` - str - фамилия оператора\n
    ``password_user`` - str - пароль к 4CAN\n
    ``hired`` - str - работает ли человек в настоящий момент\n
    ``admin_user`` - str - является ли админом\n
    """

    __bind_key__ = "fc_engine"
    __tablename__ = "fc_users"

    not_used_0 = db.Column("id_user", db.Integer)
    user_id = db.Column("login_user", db.VARCHAR, primary_key=True)
    first_name = db.Column("imie_user", db.VARCHAR)
    last_name = db.Column("nazwisko_user", db.VARCHAR)
    password_user = db.Column(db.VARCHAR)
    not_used_1 = db.Column("stanowisko_user", db.VARCHAR)
    not_used_2 = db.Column("adres_user", db.VARCHAR)
    not_used_3 = db.Column("tel_user", db.VARCHAR)
    not_used_4 = db.Column("tel_kom_user", db.VARCHAR)
    not_used_5 = db.Column("email_user", db.VARCHAR)
    hired = db.Column("aktywny_user", db.VARCHAR)
    admin_user = db.Column("admin_user", db.VARCHAR)
    not_used_6 = db.Column("mos_user", db.VARCHAR)
    not_used_7 = db.Column("pay_user", db.VARCHAR)
    not_used_8 = db.Column("pay_gr_user", db.VARCHAR)
    not_used_9 = db.Column("pay_mpk_user", db.VARCHAR)
    not_used_10 = db.Column("for_gr_user", db.VARCHAR)

    # TODO: заменить на join
    @classmethod
    def get_operator_name(self, line):
        """Этот метод принимает линию и возвращает строку с именем и фамилией оператора
        соответствует запросам:\n
        ``SELECT id_brygadz
        FROM fc_produkcja
        WHERE kod_maszyny='{line}' AND data_zakoncz_zmiana IS NOT NULL
        ORDER BY data_zakoncz_zmiana DESC
        LIMIT 1``

        ``SELECT imie_user, nazwisko_user
        FROM fc_users
        WHERE login_user = PREV``
        """

        # получение id оператора на основании линии
        operator_id = (
            fc_produkcja.query.with_entities(fc_produkcja.operator_id)
            .filter(fc_produkcja.line_name == line)
            .filter(fc_produkcja.order_end != None)
            .order_by(fc_produkcja.order_end.desc())
            .first()[0]
        )

        # получение имени оператора на основании его id
        operator_name = (
            fc_users.query.with_entities(self.first_name, self.last_name)
            .filter(fc_users.user_id == operator_id)
            .first()
        )

        return f"{operator_name[0]} {operator_name[1]}"
