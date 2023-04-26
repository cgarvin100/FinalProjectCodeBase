import flask
import tkinter as tk
import requests

server = "http://127.0.0.1:5000"


def set_up_window():
    root = tk.Tk()
    root.title("Monitor-Station GUI")
    root.geometry("1500x1200")

    select_room_number_view(root)

    root.mainloop()
    return


def select_room_number_view(root):
    select_room_number_frame = tk.LabelFrame(root, width=375,
                                             height=150, padx=87.5,
                                             borderwidth=5)
    select_room_number_frame.grid(row=0, column=0)
    select_room_number_frame.grid_propagate(False)

    title_label = tk.Label(select_room_number_frame,
                           text="Select Room Number",
                           font="Helvetica 18 underline")
    title_label.place(relx=0.5, rely=0, anchor="n")

    selected_room = tk.StringVar()
    room_numbers = get_rooms()

    selected_room.set("Select Room")
    picker_menu = tk.OptionMenu(select_room_number_frame,
                                selected_room,
                                *room_numbers,
                                command=lambda x: room_selected())
    picker_menu.place(relx=0.5, rely=0.5, anchor="center")
    picker_menu.config(font=("Helvetica", 25))

    def room_selected():
        refresh_root(root)
        patient_info_view(root, selected_room.get())
        sleep_data_view(root, selected_room.get())
        previous_sleep_data_view(root, selected_room.get())
        CPAP_flow_image_view(root)
        return

    return


def get_rooms():
    # API call goes HERE
    rooms, status_code = requests.get(server + "/get_rooms").json()
    return rooms


def patient_info_view(root, room):
    patient_info_frame = tk.LabelFrame(root, width=375,
                                       height=150, padx=87.5,
                                       borderwidth=5)
    patient_info_frame.grid(row=0, column=1)
    patient_info_frame.grid_propagate(False)

    title_label = tk.Label(patient_info_frame,
                           text="Patient Info",
                           font="Helvetica 18 underline")
    title_label.place(relx=0.5, rely=0, anchor="n")

    recent_patient_data = get_room_most_recent_data(int(room))

    tk.Label(patient_info_frame, text="Patient Name:  " + recent_patient_data['name']) \
        .place(relx=0.5, rely=.3, anchor="center")
    tk.Label(patient_info_frame, text="Patient MRN:  " + str(recent_patient_data['mrn'])) \
        .place(relx=0.5, rely=.5, anchor="center")

    cpap_label = tk.Label(patient_info_frame, text="CPAP Pressure:")
    cpap_label.place(relx=.1, rely=.7, anchor="center")

    CPAP_var = tk.StringVar()
    CPAP_var.set(get_patient_CPAP_Pressure(recent_patient_data["mrn"]))
    cpap_entry = tk.Entry(patient_info_frame, textvariable=CPAP_var,
                          width=2)
    cpap_entry.place(relx=0.5, rely=.7, anchor="center")

    update_button = tk.Button(patient_info_frame,
                              text="Update",
                              command=
                              lambda entry=CPAP_var,
                                     frame=patient_info_frame,
                                     mrn=recent_patient_data['mrn']:
                              update_CPAP_Pressure(entry, frame, mrn))

    def show_button(event):
        update_button.place(relx=0.9, rely=.7, anchor="center")

    cpap_entry.bind("<Key>", show_button)
    return


def get_patient_CPAP_Pressure(mrn):
    # API call goes HERE
    cpap_pressure, status_code = requests.get(server + "/get_cpap_pressure/" + str(mrn)).json()
    return cpap_pressure


def update_CPAP_Pressure(entry, frame, mrn):
    value = entry.get()
    validation_result = validate_CPAP_entry(value)

    if validation_result == "":
        result_label = tk.Label(frame, text="Successful Update", fg="green")
        result_label.place(relx=0.5, rely=.8, anchor="n")
        result_label.after(2000, result_label.destroy)
        value = int(value)
        update_dict = {"mrn": int(mrn), "newValue": value}
        # API push Goes HERE
        r = requests.post(server + "/update_pressure", json=update_dict)
        print(r.json()[1])
    else:
        result_label = tk.Label(frame, text=validation_result, fg="red")
        result_label.place(relx=0.5, rely=.8, anchor="n")
        result_label.after(2000, result_label.destroy)

    return


def validate_CPAP_entry(value):
    try:
        num_value = int(value)
        if num_value < 4:
            return "Value is too small"
        elif num_value > 25:
            return "Value is too large"
        else:
            return ""
    except ValueError:
        return "Value is not an integer"


def get_room_most_recent_data(room):
    # API call goes here
    most_recent, status_code = requests.get(server + "/room_most_recent/" + str(room)).json()
    print(status_code)
    return most_recent


def sleep_data_view(root, room):
    sleep_data_frame = tk.LabelFrame(root, width=375,
                                     height=300, padx=87.5,
                                     borderwidth=5)
    sleep_data_frame.grid(row=1, column=0)
    sleep_data_frame.grid_propagate(False)

    title_label = tk.Label(sleep_data_frame,
                           text="Sleep Data",
                           font="Helvetica 18 underline")
    title_label.place(relx=0.5, rely=0, anchor="n")

    recent_patient_data = get_room_most_recent_data(int(room))

    apnea_count = recent_patient_data['apneaCount']

    if apnea_count >= 2:
        color = "red"
    else:
        color = None

    tk.Label(sleep_data_frame,
             text="Apnea Count:  " + str(apnea_count),
             font=("Helvetica", 16),
             fg=color) \
        .place(relx=0.5, rely=.2, anchor="center")

    tk.Label(sleep_data_frame,
             text="Breathing Rate:  " + str(recent_patient_data["breathingRate"]),
             font=("Helvetica", 16)) \
        .place(relx=0.5, rely=.5, anchor="center")

    tk.Label(sleep_data_frame,
             text="Test Date:  " + str(recent_patient_data["date"]),
             font=("Helvetica", 16)) \
        .place(relx=0.5, rely=.8, anchor="center")

    return


def CPAP_flow_image_view(root):
    CPAP_flow_image_frame = tk.LabelFrame(root, width=375,
                                          height=300, padx=87.5,
                                          borderwidth=5)
    CPAP_flow_image_frame.grid(row=1, column=1)
    CPAP_flow_image_frame.grid_propagate(False)

    title_label = tk.Label(CPAP_flow_image_frame,
                           text="Volumetric Flow PLot",
                           font="Helvetica 12 underline")
    title_label.place(relx=0.5, rely=0, anchor="n")

    return


def previous_sleep_data_view(root, room):
    previous_sleep_data_frame = tk.LabelFrame(root, width=375,
                                              height=300, padx=87.5,
                                              borderwidth=5)
    previous_sleep_data_frame.grid(row=2, column=0)
    previous_sleep_data_frame.grid_propagate(False)

    title_label = tk.Label(previous_sleep_data_frame,
                           text="Compare Sleep Data",
                           font="Helvetica 18 underline")
    title_label.place(relx=0.5, rely=0, anchor="n")

    this_patient = get_room_most_recent_data(int(room))

    dates = get_patient_dates(this_patient["mrn"])

    dates.remove(this_patient["date"])

    selected_date = tk.StringVar()
    selected_date.set("Select Date")
    picker_menu = tk.OptionMenu(previous_sleep_data_frame,
                                selected_date,
                                *dates,
                                command=lambda x: date_selected())
    picker_menu.place(relx=0.5, rely=0.2, anchor="center")

    def date_selected():
        patient_data = get_patient_data_by_date(int(selected_date.get()),
                                                this_patient["mrn"])

        apnea_count = patient_data['apneaCount']

        if apnea_count >= 2:
            color = "red"
        else:
            color = None

        tk.Label(previous_sleep_data_frame,
                 text="Apnea Count:  " + str(apnea_count),
                 font=("Helvetica", 16),
                 fg=color) \
            .place(relx=0.5, rely=.5, anchor="center")

        tk.Label(previous_sleep_data_frame,
                 text="Breathing Rate:  " + str(patient_data["breathingRate"]),
                 font=("Helvetica", 16)) \
            .place(relx=0.5, rely=.8, anchor="center")

        previous_CPAP_flow_image_view(root)
        return

    return


def get_patient_dates(mrn):
    # API call HERE
    dates, status_code = requests.get(server + "/get_patient_dates/" + str(mrn)).json()

    return dates


def get_patient_data_by_date(date, mrn):
    # API call HERE
    data, status_code = requests.get(server +
                                     "/get_data_by_date/" + str(date) +
                                     "/" + str(mrn)).json()
    print(status_code)
    return data


def previous_CPAP_flow_image_view(root):
    previous_CPAP_flow_image_frame = tk.LabelFrame(root, width=375,
                                                   height=300, padx=87.5,
                                                   borderwidth=5)
    previous_CPAP_flow_image_frame.grid(row=2, column=1)
    previous_CPAP_flow_image_frame.grid_propagate(False)

    title_label = tk.Label(previous_CPAP_flow_image_frame,
                           text="Comparison Volumetric Flow PLot",
                           font="Helvetica 12 underline")
    title_label.place(relx=0.5, rely=0, anchor="n")


def refresh_root(root):
    for frame in root.winfo_children()[1:]:
        frame.destroy()


if __name__ == '__main__':
    set_up_window()
