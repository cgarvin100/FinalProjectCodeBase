import logging
import ssl
from flask import Flask, request, jsonify
from pymodm import connect
from PatientModel import Patient
from pymodm import errors as pymodm_errors

username = "cgg18"
password = "Nd9vw6k6"

app = Flask(__name__)


def init_server():
    """ Performs set-up functions before starting server
    This functions performs any needed set-up steps required for server
    operation.  The logging system is configured.  A connection is created
    to the MongoDB database.
    """
    connect("mongodb+srv://{}:{}@cluster0.hdzs3eb."
            "mongodb.net/final?retryWrites=true&w=majority"
            .format(username, password), ssl_cert_reqs=ssl.CERT_NONE)
    return


def change_patient_cpap_pressure(mrn, new_value):
    """ Changes a patient's CPAP pressure.
    Changes the CPAP pressure for the patient with the given MRN
    to the specified new value.
    Args:
    mrn (int): the MRN of the patient whose CPAP pressure is to be
    changed.
    new_value (int): the new CPAP pressure value to be set.
    """
    this_patient = Patient.objects.raw({"_id": mrn}).first()
    this_patient.cpapPressure = new_value
    this_patient.save()
    return


def get_all_data_dicts():
    """ Returns a list of all CPAP data dictionaries for all patients.
    Returns a list of all CPAP data dictionaries for
    all patients in the database.
    """
    data_list = []

    for patient in Patient.objects.raw({}):
        data_list.extend(patient.cpapData)
    return data_list


def add_patient_to_db(mrn, name, cpapPressure, date, room, cpapData):
    """ Adds a new patient dictionary to the database
    This function receives basic information on a new patient,
    creates aninstance of the Patient "MongoModel" class to
    contain that information,
    and saves this patient information to MongoDB.  The "mrn" is used
    as the primary key.
    The database is being stored externally to the server in an on-line
    MongoDB database.
    Args:
        mrn (int): The medical record number of the patient
        name (str): Full name of patient
        cpapPressure (int): CPAP pressure in cmH2O entered in
        patient gui
        date (str): Timestamp of push from gui to server
        room (int): Room number patient is in from patient gui
        cpapData (dict): Dict of cpap analysis results
    Returns:
        Patient: A copy of what was saved to the MongoDB database
    """
    dates = [date]
    rooms = [room]
    cpapData = [cpapData]
    new_patient = Patient(mrn=mrn,
                          name=name,
                          cpapPressure=cpapPressure,
                          dates=dates,
                          rooms=rooms,
                          cpapData=cpapData)
    saved_patient = new_patient.save()
    return saved_patient


def add_results_to_patient(mrn, name, cpapPressure, date, room, cpapData):
    """Adds analysis result for a specific patient
    This function adds a test result to the specified patient.  First, the
    appropriate patient record is found and downloaded from the MongoDB
    database using the "mrn" as the primary key for the search.  Next,
    the rest of the fields of the Patient class is updated by appending the new
    results from the patient gui. The updated Patient record is then saved
    back to MongoDB.
    Args:
        mrn (int): The medical record number of the patient
        name (str): Full name of patient
        cpapPressure (int): CPAP pressure in cmH2O entered in patient gui
        date (str): Timestamp of push from gui to server
        room (int): Room number patient is in from patient gui
        cpapData (dict): Dict of cpap analysis results
    Returns:
        None
    """
    x = Patient.objects.raw({"_id": mrn}).first()
    x.name = name
    x.cpapPressure = cpapPressure
    x.cpapData.append(cpapData)
    x.rooms.append(room)
    x.dates.append(date)
    x.save()


@app.route("/new_patient", methods=["POST"])
def post_new_patient():
    """POST route to receive information about a new patient and add the
       patient to the database
    This "Flask handler" function receives a POST request to add a new patient
    to the database.  The POST request should receive a dictionary encoded as
    a JSON string in the following format:
        {"patient_name": str,
         "patient_mrn": int,
         "room_num": int,
         "cpap_pressure": int,
         "results": dict,
         "dates": str}
    The value of "mrn" is an integer that is the medical record number for the
    patient. The function first receives the dictionary sent with the POST
    request.  It then calls a worker function to act on the data. It finally
    returns the resulting message and status code.
    """
    in_data = request.get_json()
    answer, status_code = new_patient_driver(in_data)
    return jsonify(answer), status_code


def new_patient_driver(in_data):
    """Implements the '/new_patient' route
    This function performs the data validation and implementation for the
    `/new_patient` route which adds a new patient to the database.  It first
    calls a function that validates that the input data to the route is a
    dictionary that has the necessary keys and value data types.  If the
    necessary information does not exist, the function returns an error message
    and a status code of 400.  Otherwise, another function is called and sent
    the necessary information to add a new patient to the database.  A success
    message and a 200 status code is then returned.
    Args:
        in_data (dict): Data received from the POST request.  Should be a
        dictionary with the format found in the docstring of the
        "post_new_patient" function, but that needs to be verified
    Returns:
        str, int: a message with information about the success or failure of
            the operation and a status code
    """
    expected_keys = ["patient_name", "patient_mrn", "room_num",
                     "cpap_pressure", "results", "dates"]
    expected_types = [str, int, int, int, dict, str]
    validation = validate_input_data_generic(in_data, expected_keys,
                                             expected_types)
    if validation is not True:
        return validation, 400
    mrn_list = get_mrn_list()
    if in_data["patient_mrn"] in mrn_list:
        add_results_to_patient(in_data["patient_mrn"], in_data["patient_name"],
                               in_data["cpap_pressure"], in_data["dates"],
                               in_data["room_num"], in_data["results"])
        return "Patient successfully added", 200
    add_patient_to_db(in_data["patient_mrn"], in_data["patient_name"],
                      in_data["cpap_pressure"], in_data["dates"],
                      in_data["room_num"], in_data["results"])
    return "Patient successfully added", 200


def get_mrn_list():
    """ MRN List Retriever
    Returns a list of all MRNs (Medical Record Numbers) in the Patient
    collection.

    Args:
        None

    Returns:
        mrn_list (list): A list of integers representing the MRNs of
        all patients in the database.
    """
    mrn_list = []
    for x in Patient.objects.raw({}):
        mrn_list.append(x.mrn)
    print(mrn_list)
    return mrn_list


def validate_input_data_generic(in_data, expected_keys, expected_types):
    """Validates that input data is a dictionary with correct information
    This function receives the data that was sent with a POST request.  It
    also receives lists of the keys and value data types that are expected to
    be in this dictionary.  The function first verifies that the data sent to
    the post request is a dictionary.  Then, it verifies that the expected keys
    are found in the dictionary and that the corresponding value data types
    are of the correct type.  An error message is returned if the data is not
    a dictionary, a key is missing or there is an invalid data type.  If keys
    and data types are correct, a value of True is returned.
    Args:
        in_data (dict): object received by the POST request
        expected_keys (list): keys that should be found in the POST request
            dictionary
        expected_types (list): the value data types that should be found in the
            POST request dictionary
    Returns:
        str: error message if there is a problem with the input data, or
        bool: True if input data is valid.
    """
    if type(in_data) is not dict:
        return "Input is not a dictionary"
    for key, value_type in zip(expected_keys, expected_types):
        if key not in in_data:
            return "Key {} is missing from input".format(key)
        if type(in_data[key]) is not value_type:
            return "Key {} has the incorrect value type".format(key)
    return True


@app.route("/get_rooms", methods=["GET"])
def get_rooms_driver():
    """ Returns a list of all rooms.
    Returns a list of all rooms that have been recorded in the database.
    """
    room_list = []
    for patient in Patient.objects.raw({}):
        room_list.extend(patient.rooms)

    response = sorted(list(set(room_list)))

    return jsonify(response, 200)


@app.route("/get_cpap_pressure/<mrn>", methods=["GET"])
def get_cpap_pressure_driver(mrn):
    """
    Returns the CPAP pressure of the patient with the given MRN.
    Args:
    mrn (int): the MRN of the patient whose CPAP pressure is to be returned.
    """
    this_patient = Patient.objects.raw({"_id": int(mrn)}).first()
    response = this_patient.cpapPressure
    return jsonify(response), 200


@app.route("/update_pressure", methods=["POST"])
def update_pressure_driver():
    """ Updates a patient's CPAP pressure.
    Receives a JSON object containing the MRN of the patient
    whose CPAP pressure is to be changed and the new pressure
    value to be set, then updates the patient's CPAP pressure.
    """
    in_data = request.get_json()
    change_patient_cpap_pressure(in_data["mrn"], in_data["newValue"])
    return jsonify("Successful", 200)


@app.route("/room_most_recent/<room>", methods=["GET"])
def room_most_recent_driver(room):
    """ Returns the most recent CPAP data dictionary for a given room.
    Returns the most recent CPAP data dictionary for the given room,
    based on the date field.
    Args:
    room (int): the room number of the desired data.
    """
    data_list = []
    for data_dict in get_all_data_dicts():
        print(data_dict["room"])
        if data_dict["room"] == int(room):
            data_list.append(data_dict)

    most_recent = sorted(data_list, key=lambda x: x['date'])[-1]
    return jsonify(most_recent, 200)


@app.route("/get_patient_dates/<mrn>", methods=["GET"])
def get_patient_dates_driver(mrn):
    """ Returns a list of dates for a given patient.
    Returns a list of dates that have been recorded
    for the patient with the given MRN.
    Args:
    mrn (int): the MRN of the patient whose dates are to be returned.
    """
    this_patient = Patient.objects.raw({"_id": int(mrn)}).first()
    dates = this_patient.dates
    return jsonify(dates, 200)


@app.route("/get_data_by_date/<date>/<mrn>", methods=["GET"])
def get_data_by_date_driver(date, mrn):
    """ Returns CPAP data for a given patient on a given date.
    Returns the CPAP data dictionary for the patient with the
    given MRN on the specified date.
    Args:
    date (str): the date to look up data for.
    mrn (int): the MRN of the patient whose data is to be returned.
    """
    this_patient = Patient.objects.raw({"_id": int(mrn)}).first()
    for data_dict in this_patient.cpapData:
        if data_dict["date"] == date:
            return jsonify(data_dict, 200)

    return jsonify("Date not found", 400)


@app.route("/get_image_string/<date>/<mrn>", methods=["GET"])
def get_image_string(date, mrn):
    """
    Returns image string data for a given patient on a given date.
    Args:
    date (str): the date to extract the image
    mrn (int): the MRN of the patient whose data is to be returned.

        """
    this_patient = Patient.objects.raw({"_id": int(mrn)}).first()
    for data_dict in this_patient.cpapData:
        if data_dict["date"] == date:
            return jsonify(data_dict["image"], 200)
    return jsonify("Date not found", 400)


if __name__ == '__main__':
    init_server()
    app.run(host="0.0.0.0")
