from ultralytics import YOLO
import cv2
import time

# Time
def current_time() :
    t = time.localtime()
    return time.strftime("%H:%M:%S", t)  

# Files
rtsp_url = "rtsp://pradogolf:PradoGolf9551!@47.176.3.242/unicast/c15/s1/live" 
txt = 'detections.txt'

# Model 
model = YOLO('yolo11n.pt')
cap = cv2.VideoCapture(rtsp_url)

# Start time
with open(txt, 'w') as file :
    file.write(f'-- Started at : {current_time()} --\n')

# Id Number Tracking
seen_ids = set()

# Tracking
while cap.isOpened() :
    success, frame = cap.read()
    if success :
        # Tracker
        results = model.track(
            frame,                  # Source
            persist = True,         # Does it track the same thing through to the next frame
            classes = [0, 2],       # What it is tracking (0 = person, 2 = cars)
            conf = 0.5,             # Confidence level before tracking
            line_width = 1          # Width of Bounding Box
            )
        
        # Get the boxes and track IDs, printing them to the doc
        for frane_number, result in enumerate(results, start=1) :
            for box in result.boxes :
                if box.id is not None :
                    id = int(box.id)
                    class_id = int(box.cls)
                    name = model.names[class_id]
                    if id not in seen_ids :
                        seen_ids.add(id)
                        with open(txt, 'a') as file :
                            file.write(f'ID: {id}  {name} at : {current_time()}\n')

        # Show the frame
        annoted_frame = results[0].plot()
        cv2.imshow("Tracking", annoted_frame)
        
        # Break loop and record end time
        if cv2.waitKey(1) & 0xFF == ord('q') :
            with open(txt, 'a') as file :
                file.write(f'-- Ended at : {current_time()} --\n')
            break
    else :
        break

cap.release()
cv2.destroyAllWindows()