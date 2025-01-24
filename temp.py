from ultralytics import YOLO
import cv2
import math 
from tkinter import *

def launch_camera():
    # destroy home page
    home_app.destroy()

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


# home page window
home_app = Tk()
home_app.title("Parking Pulse Home Page")
home_app.geometry("1080x720")
home_app.configure(bg="grey")

# create a label for the title
label = Label(home_app, text="Welcome To Parking Pulse", font=("Arial", 48), bg="grey")
label.pack(padx=20, pady=(225, 0))

# create a login and password entry
login = Entry(home_app, width=40)
login.insert(0, "Login")
login.pack(pady=10)
password = Entry(home_app, width=40, show='*')
password.insert(0, "Password")
password.pack(pady=10)

# create a login button
login_button = Button(home_app, text="Login", width=20, height=2, command=launch_camera)
login_button.pack(pady=10)

# run home page
home_app.mainloop()

