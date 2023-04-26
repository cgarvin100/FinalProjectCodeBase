from pymodm import MongoModel, fields


class Patient(MongoModel):
    mrn = fields.IntegerField(primary_key=True)
    name = fields.CharField()
    cpapPressure = fields.IntegerField()
    dates = fields.ListField()
    rooms = fields.ListField()
    cpapData = fields.ListField()
