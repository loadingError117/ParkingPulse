from ultralytics import YOLO
import cv2
import math 
import numpy
import time


# Checks to see if Rectangles are intersecting
def is_intersecting(rect1, rect2) :
    x1_A, y1_A, x2_A, y2_A = rect1
    x1_B, y1_B, x2_B, y2_B = rect2
    if x1_A < x2_B and x2_A > x1_B and y1_A < y2_B and y2_A > y1_B:
        # Rectangles intersect
        return True
    return False

# Timer Variables
start_time = None
INTERSECT_DURATION = 1

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
    #========= Rectangle =======================
    top_left = (100,100)
    bot_right = (400, 400)
    cv2.rectangle(img, top_left, bot_right, (0, 255, 0), 3)
    # ======== Coordinates =====================
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

            # Rectangle Stuff
            if is_intersecting((100,100,400,400), (x1, y1, x2, y2)) and classNames[cls] == "person" and confidence > 0.70:
                # Start the timer
                if start_time is None :
                    start_time = time.time()
                elapsed_time = time.time() - start_time
                if elapsed_time >= INTERSECT_DURATION :
                    cv2.putText(img, 'INTERSECT', (50, 50), font, fontScale, (0, 255, 0))
            else :
                start_time = None


    cv2.imshow('Webcam', img)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
