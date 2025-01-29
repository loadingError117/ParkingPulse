from ultralytics import YOLO
import cv2
import math 
from tkinter import *
#================================================================================================
#login validation function
#current login is "admin" and password is "password"
#================================================================================================   
def login_validation():
    global login_app
    global homePage
    # get login and password
    userID = username.get()
    passwordAttempt = password.get()

    # check if login and password are correct
    if userID == "admin" and passwordAttempt == "password":
        print("Login Successful")
        # destroy login page
        login_app.destroy()
        # run home page
        home_page()
    else:
        # remove previous login failed message if it exists
        global login_failed_label
        try:
            login_failed_label.destroy()
        except NameError:
            pass
        # display login failed message
        login_failed_label = Label(login_app, text="Login Failed", font=("Arial", 12), fg="red", bg="grey")
        login_failed_label.pack(pady=10)

#================================================================================================
#launch webcam function with YOLO model for object detection
#DELETE THIS FUNCTION AFTER TESTING
#================================================================================================
def launch_webcam():

    # start webcam
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    
    # model
    model = YOLO('yolo11n.pt')

    # object classes
    classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck"]

    while True:
        success, img = cap.read()
        results = model(img)[0]

        # coordinates
        for box in results.boxes:
            # class name
            cls = int(box.cls[0])
            if cls in [classNames.index(obj) for obj in ["car", "bus", "truck", "person"]]:  # Only process if the object is a car, bus, or truck
                # bounding box
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # convert to int values

                # put box in cam
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                # confidence
                confidence = math.ceil((box.conf[0] * 100)) / 100
                print("Confidence --->", confidence)

                # object details
                org = (x1, y1)
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 1
                color = (255, 0, 0)
                thickness = 2

                cv2.putText(img, f"{classNames[cls]} {confidence:.2f}", org, font, fontScale, color, thickness)

        cv2.imshow('Webcam', img)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

#================================================================================================
#launch IPcamera function with YOLO model for object detection
#================================================================================================
def launch_IPcamera():

    # Starting the IP Camera
    rtsp_url = "rtsp://admin:password111@192.168.1.108:554/live" 
    cap = cv2.VideoCapture(rtsp_url)

    cap.set(3, 640)
    cap.set(4, 480)

    # model
    model = YOLO('yolo11n.pt')

    # object classes
    classNames = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck"]

    while True:
        success, img = cap.read()
        results = model(img)[0]

        # coordinates
        for box in results.boxes:
            # class name
            cls = int(box.cls[0])
            if cls in [classNames.index(obj) for obj in ["car", "bus", "truck", "person"]]:  # Only process if the object is a car, bus, or truck
                # bounding box
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)  # convert to int values

                # put box in cam
                cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                # confidence
                confidence = math.ceil((box.conf[0] * 100)) / 100
                print("Confidence --->", confidence)

                # object details
                org = (x1, y1)
                font = cv2.FONT_HERSHEY_SIMPLEX
                fontScale = 1
                color = (255, 0, 0)
                thickness = 2

                cv2.putText(img, f"{classNames[cls]} {confidence:.2f}", org, font, fontScale, color, thickness)

        cv2.imshow('Webcam', img)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

#================================================================================================
#Home Page Window
#================================================================================================
def home_page():
    homePage = Tk()
    homePage.title("Parking Pulse Home Page")
    homePage.geometry("1080x720")
    homePage.configure(bg="grey")

    # create a label for the title
    label = Label(homePage, text="Home", font=("Arial", 48), bg="grey")
    label.pack(padx=20, pady=(50, 0))

    # create a frame to hold the buttons
    button_frame = Frame(homePage, bg="grey")
    button_frame.pack(pady=20)

    # create a button to launch the IPcamera
    IPcamera_button = Button(button_frame, text="Launch IPCamera", width=20, height=10, command=launch_IPcamera)
    IPcamera_button.grid(row=0, column=0, padx=10, pady=10)

    # create a button to launch the webcam
    # DELETE THIS BUTTON AFTER TESTING
    webcam_button = Button(button_frame, text="Launch WebCam", width=20, height=10, command=launch_webcam)
    webcam_button.grid(row=0, column=1, padx=10, pady=10)

    # create a settings button
    settings_button = Button(button_frame, text="Settings", width=20, height=10)
    settings_button.grid(row=0, column=2, padx=10, pady=10)

    # create additional buttons to fill the 2x3 grid
    button4 = Button(button_frame, text="Button 4", width=20, height=10)
    button4.grid(row=1, column=0, padx=10, pady=10)

    button5 = Button(button_frame, text="Button 5", width=20, height=10)
    button5.grid(row=1, column=1, padx=10, pady=10)

    button6 = Button(button_frame, text="Button 6", width=20, height=10)
    button6.grid(row=1, column=2, padx=10, pady=10)

    

#================================================================================================
#Login Page Window
#================================================================================================
# login page window
login_app = Tk()
login_app.title("Parking Pulse Login Page")
login_app.geometry("1080x720")
login_app.configure(bg="grey")
# create a label for the title
label = Label(login_app, text="Welcome To Parking Pulse", font=("Arial", 48), bg="grey")
label.pack(padx=20, pady=(225, 0))

# create a login and password entry
username = Entry(login_app, width=40)
username.insert(0, "Username")
username.pack(pady=10)
password = Entry(login_app, width=40, show='*')
password.insert(0, "Password")
password.pack(pady=10)

# create a login button
login_button = Button(login_app, text="Login", width=20, height=2, command=login_validation)
login_button.pack(pady=10)

# run home page
login_app.mainloop()
