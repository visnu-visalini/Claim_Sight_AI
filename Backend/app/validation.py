from marshmallow import Schema, fields, validate, ValidationError

class AuthSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

class VehicleSchema(Schema):
    make = fields.Str(required=True)
    model = fields.Str(required=True)
    year = fields.Int(required=True, validate=validate.Range(min=1900, max=2100))
    chassis_number = fields.Str(required=False, allow_none=True)

class InsuranceSchema(Schema):
    provider = fields.Str(required=True)
    policy_number = fields.Str(required=True)
    expiry_date = fields.Date(required=True)

class ClaimCreateSchema(Schema):
    # Fields required for creating a new claim
    user_id = fields.Int(required=True)
    description = fields.Str(required=True)
    vehicle_id = fields.Int(required=True)
    accident_date = fields.Date(required=True)
    accident_location = fields.Str(required=True)
    accident_description = fields.Str(required=False)


class ClaimUpdateSchema(Schema):
    user_id = fields.Int(required=True)
    description = fields.Str(required=False)
    vehicle_id = fields.Int(required=False, allow_none=True)
    # optional fields for vehicle details (if client wants to update directly)
    vehicle_number = fields.Str(required=False, allow_none=True)
    vehicle_make = fields.Str(required=False, allow_none=True)
    vehicle_model = fields.Str(required=False, allow_none=True)
    vehicle_year = fields.Int(required=False, allow_none=True)
    accident_date = fields.Date(required=False, allow_none=True)
    accident_location = fields.Str(required=False, allow_none=True)
    accident_description = fields.Str(required=False, allow_none=True)
