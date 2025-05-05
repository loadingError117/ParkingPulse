# 🚗 ParkingPulse

**AI-Based Parking Lot Security and Vehicle Tracking System**

ParkingPulse is a real-time intelligent vehicle monitoring system designed for parking lot management and security. It uses computer vision and ReID (Re-Identification) techniques to track vehicles across camera zones, identify potential theft, and generate activity reports — all in a unified GUI application.

---

## 📌 Features

- 📷 **Live Camera Feed Monitoring**
  - Supports RTSP/MJPEG streams
  - Dynamic zone selection via dropdown

- 🧠 **YOLO-Based Vehicle Detection**
  - Optimized inference with adjustable resolution and frame skipping
  - Configurable confidence thresholds

- 🔁 **FastReID for Vehicle Re-Identification**
  - Uses cosine similarity for matching
  - Adjustable similarity threshold via GUI

- 📬 **Summary Email Reporting**
  - Automatic hourly email summaries
  - Manual email trigger with top 10 detections
  - Configurable notification recipients via Firestore

- 🔒 **User Authentication**
  - Firebase-based login with role-based access (admin/user)

- 🧾 **Vehicle Logging & History**
  - Logs each detected vehicle with timestamp
  - Daily log rotation
  - View and export logs from the interface

---

## 🖥️ Tech Stack

| Layer         | Technology              |
|---------------|--------------------------|
| Frontend GUI  | [customtkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Detection     | [YOLOv8](https://github.com/ultralytics/ultralytics)             |
| ReID Model    | [FastReID](https://github.com/JDAI-CV/fast-reid)                |
| Backend API   | Flask (Python REST API) |
| Database      | Firebase Firestore       |
| Auth          | Firebase Auth            |
| Email         | Python `smtplib` + `.env` |

---

## ⚙️ Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/loadingError117/ParkingPulse.git
cd ParkingPulse
