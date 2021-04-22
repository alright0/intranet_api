from marshmallow import Schema, validate, fields


class CameraSchema(Schema):
    id = fields.Integer(dump_only=True, required=True)
    line = fields.String(dump_only=True)
    line_side = fields.String(dump_only=True)
    date_now = fields.DateTime(dump_only=True)
    job = fields.String(dump_only=True)
    start_time = fields.DateTime(dump_only=True)
    last_part = fields.DateTime(dump_only=True)
    total = fields.Integer(dump_only=True, required=True)
    rejected = fields.Integer(dump_only=True, required=True)
