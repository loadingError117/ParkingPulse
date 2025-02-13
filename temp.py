from ultralytics import YOLO
import cv2
import time
import numpy as np

#================================================================================================
#launch webcam function with YOLO model for object detection
#DELETE THIS FUNCTION AFTER TESTING
#================================================================================================
def launch_webcam():

    # Model 
    model = YOLO('yolo11n.pt')
    cap = cv2.VideoCapture(0)

    # Time
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    with open('detections.txt', 'a') as file :
        file.write(f'-- Started at : {current_time} --\n')

    # Tracking
    previous_ids = 0
    while cap.isOpened() :
        success, frame = cap.read()
        if success :
            results = model.track(
                frame,              # Source
                persist = True,     # Does it track the same thing through to the next frame
                classes = [0,1,2,3,4,5,6,7],      # What it is tracking (0 = person, 2 = cars)
                conf = 0.5          # Confidence level before tracking
                )
            
            # Get the boxes and track IDs, printing them to the doc
            boxes = results[0].boxes.xywh.cpu()
            track_ids = results[0].boxes.id.int().cpu().tolist()                # Returns AttributeError when nothing is being displayed on the camera
            if len(track_ids) > previous_ids :                                  # AttributeError: 'NoneType' object has no attribute 'int'
                for id in track_ids[previous_ids:] :
                    with open('detections.txt', 'a') as file :
                        file.write(f'{id} at : {current_time}\n')
            previous_ids = len(track_ids)

            # Show the frame
            annoted_frame = results[0].plot()
            cv2.imshow("Tracking", annoted_frame)
            
            # Break loop
            if cv2.waitKey(1) & 0xFF == ord('q') :
                break
        else :
            break

    cap.release()
    cv2.destroyAllWindows()

#================================================================================================
#launch IPcamera function with YOLO model for object detection
#================================================================================================
def launch_IPcamera():

    rtsp_url = "rtsp://pradogolf:PradoGolf9551!@47.176.3.242/unicast/c15/s1/live"
    cap = cv2.VideoCapture(rtsp_url)

    # Model
    model = YOLO('yolo11n.pt')

    # Time
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    with open('detections.txt', 'a') as file :
        file.write(f'-- Started at : {current_time} --\n')

    # Tracking
    previous_ids = 0
    while cap.isOpened() :
        success, frame = cap.read()
        if success :
            results = model.track(
                frame,              # Source
                persist = True,     # Does it track the same thing through to the next frame
                classes = [0,1,2,3,4,5,6,7],      # What it is tracking (0 = person, 2 = cars)
                conf = 0.5          # Confidence level before tracking
                )

            # Show the frame
            annoted_frame = results[0].plot()
            cv2.imshow("Tracking", annoted_frame)
            
            # Break loop
            if cv2.waitKey(1) & 0xFF == ord('q') :
                break
        else :
            break

    cap.release()
    cv2.destroyAllWindows()

