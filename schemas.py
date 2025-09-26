from marshmallow import Schema, fields, validate

class EmployeeSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    role = fields.Str(required=True)
    status = fields.Str()

class AttendanceSchema(Schema):
    id = fields.Int(dump_only=True)
    employee_id = fields.Int(required=True)
    date = fields.Date(required=True)
    check_in = fields.DateTime()
    check_out = fields.DateTime()
    status = fields.Str()

# Add more schemas for other models as needed
