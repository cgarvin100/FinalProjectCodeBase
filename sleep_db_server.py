from flask import Flask, request, jsonify
from pymodm import connect
import ssl
from PatientModel import Patient
from pymodm import errors as pymodm_errors
from mySecrets import username, password

db = {
    1:
        {"mrn": 1, "name": "Garv", "CPAPPressure": 20,
         "cpap_data": [
             {"mrn": 1, "name": "Garv", "room": 1, "apneaCount": 1, "breathingRate": 30, "date": 1},
             {"mrn": 1, "name": "Garv", "room": 2, "apneaCount": 0, "breathingRate": 35,
              "date": 2},
             {"mrn": 1, "name": "Garv", "room": 3, "apneaCount": 2, "breathingRate": 35, "date": 3}
         ]},
    2:
        {"mrn": 2, "name": "mike", "CPAPPressure": 25,
         "cpap_data": [
             {"mrn": 2, "name": "Mike", "room": 1, "apneaCount": 2, "breathingRate": 30,
              "date": 2},
             {"mrn": 2, "name": "Mike", "room": 2, "apneaCount": 0, "breathingRate": 35, "date": 4}
         ]}
}

app = Flask(__name__)


def init_server():
    """ Performs set-up functions before starting server
    This functions performs any needed set-up steps required for server
    operation.  The logging system is configured.  A connection is created
    to the MongoDB database.
    """
    connect("mongodb+srv://{}:{}@cluster0.hdzs3eb.mongodb.net/final?retryWrites=true&w=majority"
            .format(username, password), ssl_cert_reqs=ssl.CERT_NONE)

    p1 = Patient(mrn=1, name="Garv",
                 cpapPressure=20,
                 dates=[1, 2, 3],
                 rooms=[1, 2, 3],
                 cpapData=[
                     {"mrn": 1, "name": "Garv", "room": 1, "apneaCount": 1, "breathingRate": 30, "date": 1},
                     {"mrn": 1, "name": "Garv", "room": 2, "apneaCount": 0, "breathingRate": 35,
                      "date": 2},
                     {"mrn": 1, "name": "Garv", "room": 3, "apneaCount": 2, "breathingRate": 35, "date": 3}
                 ])
    p2 = Patient(mrn=2, name="Mike",
                 cpapPressure=25,
                 dates=[2, 4],
                 rooms=[1, 2],
                 cpapData=[
                     {"mrn": 2, "name": "Mike", "room": 1, "apneaCount": 2, "breathingRate": 30,
                      "date": 2},
                     {"mrn": 2, "name": "Mike", "room": 2, "apneaCount": 0, "breathingRate": 35, "date": 4}
                 ])
    p1.save()
    p2.save()
    for patient in Patient.objects.raw({}):
        print(patient.mrn)
        print(patient.name)
        print(patient.cpapPressure)
        print(patient.rooms)
        print(patient.cpapData)
        print("____________________________")

    return


def change_patient_cpap_pressure(mrn, new_value):
    db[mrn]["CPAPPressure"] = new_value
    return


@app.route("/get_rooms", methods=["GET"])
def get_rooms_driver():
    room_list = []
    for patient in Patient.objects.raw({}):
        room_list.extend(patient.rooms)

    response = sorted(list(set(room_list)))

    return jsonify(response, 200)


@app.route("/get_cpap_pressure/<mrn>", methods=["GET"])
def get_cpap_pressure_driver(mrn):
    this_patient = Patient.objects.raw({"_id": int(mrn)}).first()
    response = this_patient.cpapPressure
    return jsonify(response, 200)


@app.route("/update_pressure", methods=["POST"])
def update_pressure_driver():
    in_data = request.get_json()
    change_patient_cpap_pressure(in_data["mrn"], in_data["newValue"])
    return jsonify("Successful", 200)


@app.route("/room_most_recent/<room>", methods=["GET"])
def room_most_recent_driver(room):
    data_list = []
    for mrn in db:
        for cpapData in db[mrn]["cpap_data"]:
            if cpapData["room"] == int(room):
                data_list.append(cpapData)

    most_recent = max(data_list, key=lambda x: x['date'])
    return jsonify(most_recent, 200)


@app.route("/get_patient_dates/<mrn>", methods=["GET"])
def get_patient_dates_driver(mrn):
    dates = []
    for data in db[int(mrn)]["cpap_data"]:
        dates.append(data["date"])
    return jsonify(dates, 200)


@app.route("/get_data_by_date/<date>/<mrn>", methods=["GET"])
def get_data_by_date_driver(date, mrn):
    for data in db[int(mrn)]["cpap_data"]:
        if data["date"] == int(date):
            return jsonify(data, 200)
    return jsonify("Date not found", 400)


if __name__ == '__main__':
    init_server()
    app.run()
