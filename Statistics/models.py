from Statistics.app import db, sessionmaker, Base_cam, Base_fc


class Camera(Base_cam):

    __bind_key__ = "cam_engine"
    __tablename__ = "ibea_agregate"

    id = db.Column(
        db.Integer, nullable=False, unique=True, primary_key=True, autoincrement=True
    )

    line = db.Column(db.String(10))
    line_side = db.Column(db.String(10))
    date_now = db.Column(db.DateTime)
    job = db.Column(db.String(50))
    start_time = db.Column(db.DateTime)
    last_part = db.Column(db.DateTime)
    total = db.Column(db.Integer)
    rejected = db.Column(db.Integer)


class LineStatus(Base_fc):
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
    def get_status(self, line):
        return int(
            LineStatus.query.with_entities(self.shift)
            .filter(self.line_name == line)
            .first()[0]
        )


class fc_produkcja(Base_fc):
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

    @classmethod
    def get_operator_id(self, line):
        return (
            fc_produkcja.query.with_entities(self.operator_id)
            .filter(self.line_name == line)
            .filter(self.order_end != None)
            .order_by(self.order_end.desc())
            .first()[0]
        )


class fc_users(Base_fc):
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

    @classmethod
    def get_operator_name(self, line, operator_id):
        operator_name = (
            fc_users.query.with_entities(self.first_name, self.last_name)
            .filter(fc_users.user_id == operator_id)
            .first()
        )

        return f"{operator_name[0]} {operator_name[1]}"
