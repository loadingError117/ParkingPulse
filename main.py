import customtkinter as ctk
from tkinter import messagebox
from firebase_config import db
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
from fastreid.engine import DefaultPredictor
from fastreid.config import get_cfg
import torch
import time
from datetime import datetime, timedelta
import os
from email.mime.text import MIMEText
import smtplib
import logging
import numpy as np
from firebase_config import db
from threading import Thread, Lock
import requests
from dotenv import load_dotenv
import ssl
from email.utils import formataddr



logging.basicConfig(level=logging.INFO)
STREAM_URL = "http://67.61.139.162:8080/mjpg/video.mjpg"
API_BASE = "http://127.0.0.1:5000/api"
load_dotenv()
sender = os.getenv("EMAIL_USER")
password = os.getenv("EMAIL_PASS")

class ParkingPulseApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Parking Pulse")
        self.geometry("1080x720")
        self.attributes("-fullscreen", True)  # <- Fullscreen
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.current_user = None
        self.current_role = None

        self.yolo_model = YOLO("yolo11n.pt")
        cfg = get_cfg()
        cfg.merge_from_file("fastreid_config.yaml")
        self.reid_predictor = DefaultPredictor(cfg)
        self.initialize_notification_emails()

        self.frames = {}
        for F in (LoginPage, UserHomePage, AdminHomePage, CreateAccountPage, ManageUsersPage, CameraPage, VehicleViewer, SettingsPage):
            frame = F(parent=self, controller=self)
            self.frames[F.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("LoginPage")
        


    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()
        if name == "CameraPage":
            frame.start_camera()
        elif hasattr(frame, "stop_camera"):
            frame.stop_camera()

    def destroy(self):
        if "CameraPage" in self.frames:
            self.frames["CameraPage"].stop_camera()
        super().destroy()

    def back_to_home(self):
        role = self.controller.current_role
        if role == "Admin":
            self.controller.show_frame("AdminHomePage")
        else:
            self.controller.show_frame("UserHomePage")
    
    def initialize_notification_emails(self):
        try:
            # Add a default recipient
            default_email = "Admin@email.com"
            db.collection("notification_emails").document(default_email).set({
                "enabled": True
            })
            print(f"Collection 'notification_emails' created with {default_email}.")
        except Exception as e:
            print(f"Failed to initialize notification_emails: {e}")

# Changes below: each frame now receives shared models from controller

class LoginPage(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ctk.CTkLabel(self, text="Welcome To Parking Pulse", font=("Arial", 48))
        label.pack(pady=(150, 20))

        self.username_entry = ctk.CTkEntry(self, width=300, placeholder_text="Username")
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, width=300, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        login_button = ctk.CTkButton(self, text="Login", width=200, command=self.login)
        login_button.pack(pady=10)

        exit_button = ctk.CTkButton(self, text="Exit", width=200, fg_color="red", command=self.controller.destroy)
        exit_button.pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        try:
            response = requests.post(f"{API_BASE}/login", json={
                "username": username,
                "password": password
            })

            if response.ok:
                user_data = response.json()
                self.controller.current_user = user_data.get("username")
                self.controller.current_role = user_data.get("role", "User").capitalize()

                logging.info(f"Logged in as: {username}, Role: {self.controller.current_role}")

                if self.controller.current_role == "Admin":
                    self.controller.show_frame("AdminHomePage")
                else:
                    self.controller.show_frame("UserHomePage")
            else:
                messagebox.showerror("Login Failed", "Invalid username or password")

        except requests.exceptions.RequestException as e:
            logging.error(f"Login API call failed: {e}")
            messagebox.showerror("Error", "Could not connect to server")



class AdminHomePage(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ctk.CTkLabel(self, text="Admin Home", font=("Arial", 48))
        label.pack(pady=(20, 10))

        self.cap = None
        self.yolo_model = controller.yolo_model
        self.reid_predictor = controller.reid_predictor

        self.seen_ids = set()
        self.last_email = datetime.now()
        self.opening_time = datetime.strptime("8:00", "%H:%M").time()
        self.closing_time = datetime.strptime("16:00", "%H:%M").time()

        frame = ctk.CTkFrame(self)
        frame.pack(pady=20)

        camera_button = ctk.CTkButton(frame, text="Launch Single Camera", width=250, command=lambda: controller.show_frame("CameraPage"))
        camera_button.grid(row=0, column=0, padx=20, pady=20)

        settings_button = ctk.CTkButton(frame, text="Settings", width=250, command=lambda: controller.show_frame("SettingsPage"))
        settings_button.grid(row=0, column=1, padx=20, pady=20)

        reports_button = ctk.CTkButton(frame, text="Reports", width=250, command=lambda: controller.show_frame("VehicleViewer"))
        reports_button.grid(row=1, column=0, padx=20, pady=20)

        manage_users_button = ctk.CTkButton(
            frame,
            text="Manage Users",
            width=250,
            command=lambda: [
                controller.frames["ManageUsersPage"].refresh_users(),
                controller.show_frame("ManageUsersPage")
            ]
        )
        manage_users_button.grid(row=1, column=1, padx=20, pady=20)

        create_account_button = ctk.CTkButton(
            frame,
            text="Create Account",
            width=250,
            command=lambda: controller.show_frame("CreateAccountPage")
        )
        create_account_button.grid(row=2, column=0, columnspan=2, pady=20)

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=30)

        logout_button = ctk.CTkButton(button_frame, text="Logout", width=200, command=lambda: controller.show_frame("LoginPage"))
        logout_button.grid(row=0, column=0, padx=10)

        exit_button = ctk.CTkButton(button_frame, text="Exit", width=200, fg_color="red", command=self.controller.destroy)
        exit_button.grid(row=0, column=1, padx=10)

    def launch_camera(self):
        if not self.cap:
            self.cap = cv2.VideoCapture("http://67.61.139.162:8080/mjpg/video.mjpg")
            self.update_frame()

    def update_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                results = self.yolo_model.track(
                frame, imgsz=(384, 640), persist=True, classes=[2], conf=0.5, line_width=1)
                annotated_frame = results[0].plot() if results else frame

                frame_rgb = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

        self.after(10, self.update_frame)
    


class UserHomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ctk.CTkLabel(self, text="User Home", font=("Arial", 48))
        label.pack(pady=(20, 10))

        self.video_label = ctk.CTkLabel(self)
        self.video_label.pack(pady=10)

        self.cap = None
        self.yolo_model = controller.yolo_model  
        self.reid_predictor = controller.reid_predictor  

        frame = ctk.CTkFrame(self)
        frame.pack(pady=20)

        camera_button = ctk.CTkButton(
            frame, text="Launch Single Camera", width=250,
            command=lambda: controller.show_frame("CameraPage")
        )
        camera_button.grid(row=0, column=0, padx=20, pady=20)

        settings_button = ctk.CTkButton(
            frame, text="Settings", width=250,
            command=lambda: controller.show_frame("SettingsPage")
        )
        settings_button.grid(row=0, column=1, padx=20, pady=20)

        reports_button = ctk.CTkButton(
            frame, text="Reports", width=250,
            command=lambda: controller.show_frame("VehicleViewer")
        )
        reports_button.grid(row=1, column=0, padx=20, pady=20)

        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=30)

        logout_button = ctk.CTkButton(
            button_frame, text="Logout", width=200,
            command=lambda: controller.show_frame("LoginPage")
        )
        logout_button.grid(row=0, column=0, padx=10)

        exit_button = ctk.CTkButton(
            button_frame, text="Exit", width=200, fg_color="red",
            command=self.controller.destroy
        )
        exit_button.grid(row=0, column=1, padx=10)

class CreateAccountPage(ctk.CTkFrame):

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ctk.CTkLabel(self, text="Create Account", font=("Arial", 32))
        label.pack(pady=20)

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(pady=10)

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        self.role_dropdown = ctk.CTkComboBox(self, values=["Admin", "User"])
        self.role_dropdown.pack(pady=10)


        submit_button = ctk.CTkButton(self, text="Create", command=self.create_account)
        submit_button.pack(pady=20)

        back_btn = ctk.CTkButton(self, text="Back", command=self.back_to_home)
        back_btn.pack(pady=10)

    def create_account(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        role = self.role_dropdown.get().capitalize()  # Ensures "admin" becomes "Admin"

        if not username or not password or role not in ["Admin", "User"]:
            messagebox.showerror("Error", "All fields are required and role must be Admin or User.")
            return

        try:
            response = requests.post(f"{API_BASE}/create-user", json={
                "username": username,
                "password": password,
                "role": role
            })

            if response.ok:
                messagebox.showinfo("Success", f"Account for {username} created.")
                self.controller.show_frame("AdminHomePage")
            else:
                messagebox.showerror("Error", f"Failed to create account: {response.json().get('error', 'Unknown error')}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create account: {e}")


    def back_to_home(self):
        role = self.controller.current_role
        if role == "Admin":
            self.controller.show_frame("AdminHomePage")
        else:
            self.controller.show_frame("UserHomePage")



class ManageUsersPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.user_widgets = []

        label = ctk.CTkLabel(self, text="Manage Users", font=("Arial", 32))
        label.pack(pady=20)

        self.user_list_frame = ctk.CTkScrollableFrame(self, width=800, height=450)
        self.user_list_frame.pack(pady=10)

        # Email Notification Section (moved here)
        separator = ctk.CTkLabel(self, text="Notification Emails", font=("Arial", 20))
        separator.pack(pady=(30, 10))

        self.email_entry = ctk.CTkEntry(self, placeholder_text="Enter email to add")
        self.email_entry.pack(pady=5)

        add_email_btn = ctk.CTkButton(self, text="Add Email", command=self.add_notification_email)
        add_email_btn.pack(pady=5)

        self.email_list_frame = ctk.CTkScrollableFrame(self, width=800, height=200)
        self.email_list_frame.pack(pady=10)

        self.refresh_users()
        self.refresh_notification_emails()

        back_btn = ctk.CTkButton(self, text="Back", command=self.back_to_home)
        back_btn.pack(pady=10)

    def refresh_users(self):
        for widget in self.user_widgets:
            widget.destroy()
        self.user_widgets.clear()

        users = db.collection("users").stream()

        for doc in users:
            user_data = doc.to_dict()
            user_id = doc.id
            username = user_data.get("username", "Unknown")
            role = user_data.get("role", "User")

            user_frame = ctk.CTkFrame(self.user_list_frame)
            user_frame.pack(fill="x", padx=10, pady=5)

            label = ctk.CTkLabel(user_frame, text=username, width=200)
            label.pack(side="left", padx=5)

            role_var = ctk.StringVar(value=role)
            dropdown = ctk.CTkComboBox(user_frame, values=["Admin", "User"], variable=role_var)
            dropdown.pack(side="left", padx=5)

            update_btn = ctk.CTkButton(
                user_frame, text="Update", width=80,
                command=lambda u=user_id, v=role_var: self.update_role(u, v))
            update_btn.pack(side="left", padx=5)

            delete_btn = ctk.CTkButton(
                user_frame, text="Delete", width=80,
                fg_color="red", command=lambda u=user_id, f=user_frame: self.delete_user(u, f))
            delete_btn.pack(side="right", padx=5)

            self.user_widgets.append(user_frame)

    def refresh_notification_emails(self):
        for widget in self.email_list_frame.winfo_children():
            widget.destroy()

        try:
            email_docs = db.collection("notification_emails").stream()
            for doc in email_docs:
                email = doc.id
                data = doc.to_dict()
                enabled = data.get("enabled", True)

                frame = ctk.CTkFrame(self.email_list_frame)
                frame.pack(fill="x", padx=10, pady=5)

                label = ctk.CTkLabel(frame, text=email, width=300)
                label.pack(side="left", padx=5)

                toggle_btn = ctk.CTkButton(
                    frame,
                    text="Disable" if enabled else "Enable",
                    command=lambda e=email, val=not enabled: self.toggle_email(e, val),
                    width=80
                )
                toggle_btn.pack(side="left", padx=5)

                del_btn = ctk.CTkButton(
                    frame,
                    text="Delete",
                    fg_color="red",
                    command=lambda e=email: self.delete_notification_email(e),
                    width=80
                )
                del_btn.pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load emails: {e}")

    def update_role(self, user_id, role_var):
        try:
            db.collection("users").document(user_id).update({"role": role_var.get()})
            messagebox.showinfo("Success", "Role updated.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not update: {e}")

    def delete_user(self, user_id, frame):
        try:
            db.collection("users").document(user_id).delete()
            frame.destroy()
            messagebox.showinfo("Success", "User deleted.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete: {e}")

    def tkraise(self, aboveThis=None):
        self.refresh_users()
        self.refresh_notification_emails()
        super().tkraise(aboveThis)

    def add_notification_email(self):
        email = self.email_entry.get().strip()
        if not email:
            messagebox.showwarning("Input Required", "Please enter a valid email address.")
            return

        import re
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showwarning("Invalid Email", "Please enter a valid email address format.")
            return

        try:
            db.collection("notification_emails").document(email).set({"enabled": True})
            self.email_entry.delete(0, "end")
            self.refresh_notification_emails()
            messagebox.showinfo("Success", f"{email} added to notifications.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add email: {e}")

    def toggle_email(self, email, enable):
        try:
            db.collection("notification_emails").document(email).update({"enabled": enable})
            self.refresh_notification_emails()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update email: {e}")

    def delete_notification_email(self, email):
        try:
            db.collection("notification_emails").document(email).delete()
            self.refresh_notification_emails()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete email: {e}")

    @staticmethod
    def initialize_notification_emails():
        try:
            default_email = "josephvelasquez99@gmail.com"
            db.collection("notification_emails").document(default_email).set({
                "enabled": True
            })
            print(f"Collection 'notification_emails' created with {default_email}.")
        except Exception as e:
            print(f"Failed to initialize notification_emails: {e}")

    def back_to_home(self):
        role = self.controller.current_role
        if role == "Admin":
            self.controller.show_frame("AdminHomePage")
        else:
            self.controller.show_frame("UserHomePage")



class CameraPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.camera_lock = Lock()
        self.frame_counter = 0
        self.match_history = []
        self.total_vehicle_detections = 0
        self.last_email = datetime.now()

        back_button = ctk.CTkButton(self, text="Back", command=self.back_to_home)
        back_button.pack(pady=10)

        video_frame = ctk.CTkFrame(self, corner_radius=10)
        video_frame.pack(padx=40, pady=30, expand=True, fill="both")

        # Video label inside padded frame
        self.video_label = ctk.CTkLabel(video_frame, text="")
        self.video_label.pack(expand=True)

        self.cap = None
        self.running = False
        self.yolo_model = controller.yolo_model
        self.reid_predictor = controller.reid_predictor

        self.vehicle_features = {}  # ReID feature database
        self.feature_cache = []     # (timestamp, feature_vector)
        self.last_email = datetime.now()
        self.last_day = datetime.now().date()
        self.opening_time = datetime.strptime("8:00", "%H:%M").time()
        self.closing_time = datetime.strptime("16:00", "%H:%M").time()

        self.log_directory = "logs"
        os.makedirs(self.log_directory, exist_ok=True)
        self.current_day = datetime.now().strftime("%d-%m-%y")
        self.log_path = f'{self.log_directory}/{self.current_day}-log.txt'
        with open(self.log_path, 'w') as file:
            file.write(f'-- {self.current_day} --\n')

    def current_time(self):
        t = time.localtime()
        return time.strftime('%H:%M:%S', t)
    
    def show_frame_on_main_thread(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)


    def screenshot(self, frame, id, top_left, bot_right):
        sc_dir = "screenshots"
        if not os.path.exists(sc_dir):
            os.makedirs(sc_dir)
        date_dir = datetime.now().strftime("%d-%m-%y")
        os.makedirs(f"{sc_dir}/{date_dir}", exist_ok=True)
        timestamp = datetime.now().strftime("date_%d-%m-%ytime_%H-%M-%S")
        filename = f"{sc_dir}/{date_dir}/car_{id}_screenshot_{timestamp}.jpg"
        cv2.rectangle(frame, top_left, bot_right, (0, 0, 255), 2)
        cv2.imwrite(filename, frame)

    def log_vehicle_to_firebase(self, vehicle_id, feature_vector):
        try:
            flat_vector = feature_vector.flatten().tolist()  
            try:
                flat_vector = feature_vector.flatten().tolist()
                response = requests.post(f"{API_BASE}/log-vehicle", json={
                    "vehicle_id": vehicle_id,
                    "features": flat_vector
                })
                if response.ok:
                    print(f"Logged vehicle {vehicle_id} to API.")
                else:
                    print(f"Failed to log vehicle {vehicle_id}: {response.text}")
            except Exception as e:
                print(f"Error logging vehicle {vehicle_id}: {e}")

            print(f"Logged vehicle {vehicle_id} to Firebase.")
        except Exception as e:
            print(f"Error logging vehicle {vehicle_id}: {e}")


    def start_camera(self):
        with self.camera_lock:
            if self.cap:
                self.cap.release()
            self.cap = cv2.VideoCapture(STREAM_URL)
            self.running = True
            Thread(target=self.update_frame, daemon=True).start()




    def stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

    def back_to_home(self):
        self.stop_camera()
        role = self.controller.current_role
        if role == "Admin":
            self.controller.show_frame("AdminHomePage")
        else:
            self.controller.show_frame("UserHomePage")
    
    def cosine_distance(self, a, b):
        # Normalize both vectors and compute cosine distance
        a_norm = a / np.linalg.norm(a)
        b_norm = b / np.linalg.norm(b)
        return 1 - np.dot(a_norm, b_norm.T)


    def update_frame(self):
        while self.running and self.cap:
            self.frame_counter += 1
            matched_count = 0

            if datetime.now().date() != self.last_day:
                self.last_day = datetime.now().date()
                self.vehicle_features.clear()
                self.feature_cache.clear()
                self.current_day = datetime.now().strftime("%d-%m-%y")
                self.log_path = f'{self.log_directory}/{self.current_day}-log.txt'
                with open(self.log_path, 'w') as file:
                    file.write(f'-- {self.current_day} --\n')

            # Skip every few frames to improve responsiveness
            process_this_frame = self.frame_counter % 5 == 0

            ret, frame = False, None
            for _ in range(2):
                if self.cap:
                    self.cap.grab()
                    ret, frame = self.cap.read()

            # Check after grabbing frames
            if not ret:
                print("Warning: Frame read failed. Attempting reconnect...")
                if self.cap:
                    try:
                        self.cap.release()
                    except Exception as e:
                        print(f"Failed to release cap: {e}")
                    self.cap = None

                time.sleep(2)
                self.cap = cv2.VideoCapture(STREAM_URL)
                continue


            results = self.yolo_model.track(frame, imgsz=(320, 480), persist=True, classes=[2], conf=0.5, line_width=1)

            if process_this_frame:
                now = time.time()
                self.feature_cache = [(t, f) for (t, f) in self.feature_cache if now - t < 3.0]
                all_crops, all_boxes = [], []

                for result in results:
                    if result.boxes:
                        for box in result.boxes:
                            x1, y1, x2, y2 = box.xyxy[0].numpy()
                            if box.id is None:
                                continue
                            crop = frame[int(y1):int(y2), int(x1):int(x2)]
                            if crop.size == 0:
                                continue
                            crop = cv2.resize(crop, (256, 256))
                            all_crops.append(crop)
                            all_boxes.append((box.id.item(), int(x1), int(y1), int(x2), int(y2)))

                if all_crops:
                    batch = torch.from_numpy(np.stack(all_crops)).permute(0, 3, 1, 2).float()
                    batch = batch.to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))
                    features_batch = self.reid_predictor(batch).cpu().detach().numpy()

                    for features, (box_id, x1, y1, x2, y2) in zip(features_batch, all_boxes):
                        min_dist = float("inf")
                        matched_id = None

                        for known_id, known_feat in self.vehicle_features.items():
                            dist = self.cosine_distance(features, known_feat)
                            if dist < min_dist:
                                min_dist = dist
                                matched_id = known_id

                        if matched_id is not None and min_dist < self.controller.match_threshold:
                            matched_count += 1
                            print(f"[MATCH] Vehicle ID: {matched_id}, Cosine Distance: {min_dist:.4f}")
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 2)
                            cv2.putText(frame, f"ID: {matched_id} ({min_dist:.2f})", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                        else:
                            if len(self.vehicle_features) >= self.controller.max_vehicle_limit:
                                print(f"[SKIPPED] Max {self.controller.max_vehicle_limit} reached.")
                                continue
                            new_id = max(self.vehicle_features.keys(), default=0) + 1
                            self.vehicle_features[new_id] = features
                            self.feature_cache.append((now, features))
                            self.log_vehicle_to_firebase(new_id, features)
                            self.total_vehicle_detections += 1
                            print(f"[NEW] Vehicle ID: {new_id} added (dist={min_dist:.4f})")
                            self.screenshot(frame, new_id, (x1, y1), (x2, y2))
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            cv2.putText(frame, f"ID: {new_id}", (x1, y1 - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Initialize match history if not already
            if not hasattr(self, "match_history"):
                self.match_history = []

            # Update history only when frame is processed
            if process_this_frame:
                self.match_history.append(matched_count)
                if len(self.match_history) > 10:
                    self.match_history.pop(0)

            # Calculate smooth count safely for display
            smooth_count = int(sum(self.match_history) / len(self.match_history)) if self.match_history else 0

            # Always show the latest frame
            image = results[0].plot() if results and len(results) > 0 else frame
            vehicle_count = sum(len(result.boxes) for result in results if result.boxes)

            # Overlay total and matched vehicle count
            cv2.putText(image, f"Matched Vehicles: {smooth_count}", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

            cv2.putText(image, f"Total Tracked: {len(self.vehicle_features)}", (10, 110),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 200, 200), 2)

            if image is not None and image.shape[0] > 0 and image.shape[1] > 0:
                frame_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.after(0, self.show_frame_on_main_thread, imgtk)

            time.sleep(0.01)  # Sleep briefly to allow GUI thread to breathe
            now = datetime.now()
            if now - self.last_email >= timedelta(hours=1):
                self.send_summary_email()
                self.last_email = now



    def show_frame_on_main_thread(self, imgtk):
        self.video_label.imgtk = imgtk  # Prevent garbage collection
        self.video_label.configure(image=imgtk)

    def send_summary_email(self):
        try:
            sender = os.getenv("EMAIL_USER")
            password = os.getenv("EMAIL_PASS")

            receiver = "josephvelasquez99@gmail.com"

            subject = "Hourly ParkingPulse Report"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            body = f"Date & Time: {now}\nTotal Vehicles Detected: {self.total_vehicle_detections}"

            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = receiver

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(sender, password)
                server.sendmail(sender, receiver, msg.as_string())

            print("Summary email sent.")
        except Exception as e:
            print(f"Failed to send summary email: {e}")



class VehicleViewer(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        label = ctk.CTkLabel(self, text="Logged Vehicles", font=("Arial", 24))
        label.pack(pady=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=600, height=500)
        self.scroll_frame.pack(pady=10)

        refresh_btn = ctk.CTkButton(self, text="Refresh", command=self.refresh_vehicle_list)
        refresh_btn.pack(pady=10)

        send_btn = ctk.CTkButton(self, text="Send Summary Email", command=self.send_summary_email)
        send_btn.pack(pady=10)

        back_btn = ctk.CTkButton(self, text="Back", command=self.back_to_home)
        back_btn.pack(pady=10)

        self.refresh_vehicle_list()

    def refresh_vehicle_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        try:
            response = requests.get(f"{API_BASE}/vehicles")
            vehicles = response.json() if response.ok else []

            for data in vehicles:
                    vehicle_id = data.get("vehicle_id", "N/A")
                    timestamp = data.get("timestamp", "N/A")
                    try:
                        timestamp_fmt = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        timestamp_fmt = timestamp

                    label = ctk.CTkLabel(self.scroll_frame, text=f"Vehicle {vehicle_id} at {timestamp_fmt}", anchor="w")
                    label.pack(fill="x", padx=10, pady=5)
        except Exception as e:
            err = ctk.CTkLabel(self.scroll_frame, text=f"Error fetching data: {e}", text_color="red")
            err.pack(pady=20)

    def find_best_match(self, feature, known_features, threshold=0.65):
        min_dist = float("inf")
        best_id = None
        for vid, known_feat in known_features.items():
            dist = np.linalg.norm(feature - known_feat)
            if dist < min_dist:
                min_dist = dist
                best_id = vid
        return (best_id, min_dist) if min_dist < threshold else (None, min_dist)

    def back_to_home(self):
        role = self.controller.current_role
        if role == "Admin":
            self.controller.show_frame("AdminHomePage")
        else:
            self.controller.show_frame("UserHomePage")

    def get_notification_emails(self):
        try:
            email_docs = db.collection("notification_emails").stream()
            recipients = [doc.id for doc in email_docs if doc.to_dict().get("enabled", True)]
            return recipients
        except Exception as e:
            print(f"Failed to fetch emails from Firestore: {e}")
            return []
        
    @staticmethod
    def format_timestamp(ts):
        try:
            return datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ts or "Unknown"

    def send_summary_email(self):
        recipients = self.get_notification_emails()
        if not recipients:
            messagebox.showwarning("No Recipients", "No email recipients found in Firestore.")
            return

        sender = os.getenv("EMAIL_USER")
        password = os.getenv("EMAIL_PASS")
        subject = "📊 ParkingPulse Vehicle Log Summary"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            response = requests.get(f"{API_BASE}/vehicles")
            vehicles = response.json() if response.ok else []
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch vehicle data: {e}")
            return

        if not vehicles:
            summary = "No vehicle records found in the system."
        else:
            summary = "\n".join(
                f"{idx + 1}. Car ID: {v.get('vehicle_id', 'N/A')} at {self.format_timestamp(v.get('timestamp'))}"
                for idx, v in enumerate(vehicles[-10:])
            )

        body = f"""Hello,

    📅 Date & Time: {now}

    🛻 Recently Logged Vehicles:
    {summary}

    Visit the dashboard for full details.

    Best,  
    ParkingPulse
    """

        success_count = 0
        context = ssl.create_default_context()

        for receiver in recipients:
            try:
                msg = MIMEText(body)
                msg["Subject"] = subject
                msg["From"] = formataddr(("ParkingPulse", sender))
                msg["To"] = receiver

                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                    server.login(sender, password)
                    server.sendmail(sender, receiver, msg.as_string())

                success_count += 1
            except Exception as e:
                print(f"Failed to send to {receiver}: {e}")

        messagebox.showinfo("Summary Email", f"Sent to {success_count} recipient(s).")






class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Ensure the controller has match_threshold and max_vehicle_limit
        if not hasattr(controller, "match_threshold"):
            self.controller.match_threshold = 0.05  # Start tight
        if not hasattr(controller, "max_vehicle_limit"):
            controller.max_vehicle_limit = 20

        label = ctk.CTkLabel(self, text="Settings", font=("Arial", 24))
        label.pack(pady=20)

        clear_btn = ctk.CTkButton(self, text="Clear All Vehicle Logs", fg_color="red", command=self.clear_vehicle_logs)
        clear_btn.pack(pady=10)

        refresh_btn = ctk.CTkButton(self, text="Refresh System Cache", command=self.refresh_cache)
        refresh_btn.pack(pady=10)

        threshold_label = ctk.CTkLabel(self, text="ReID Match Threshold")
        threshold_label.pack(pady=(20, 5))

        self.threshold_slider = ctk.CTkSlider(self, from_=0.001, to=0.1, number_of_steps=99, command=self.update_threshold)

        self.threshold_slider.set(controller.match_threshold)
        self.threshold_slider.pack(pady=5)

        self.threshold_value_label = ctk.CTkLabel(self, text=f"Current: {controller.match_threshold:.2f}")
        self.threshold_value_label.pack(pady=5)

        limit_label = ctk.CTkLabel(self, text="Max Vehicle Log Limit")
        limit_label.pack(pady=(20, 5))

        self.limit_slider = ctk.CTkSlider(self, from_=10, to=200, number_of_steps=19, command=self.update_limit)
        self.limit_slider.set(controller.max_vehicle_limit)
        self.limit_slider.pack(pady=5)

        self.limit_value_label = ctk.CTkLabel(self, text=f"Current: {controller.max_vehicle_limit}")
        self.limit_value_label.pack(pady=5)

        back_btn = ctk.CTkButton(self, text="Back", command=self.back_to_home)
        back_btn.pack(pady=10)

    def clear_vehicle_logs(self):
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete all vehicle logs?")
        if confirm:
            try:
                response = requests.delete(f"{API_BASE}/vehicles")
                if response.ok:
                    messagebox.showinfo("Success", "All vehicle logs cleared.")
                else:
                    messagebox.showerror("Error", "Failed to clear logs.")

                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clear logs: {e}")

    def refresh_cache(self):
        try:
            self.controller.frames["CameraPage"].vehicle_features.clear()
            self.controller.frames["CameraPage"].feature_cache.clear()
            messagebox.showinfo("Success", "Camera feature cache cleared.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh cache: {e}")

    def update_threshold(self, value):
        self.controller.match_threshold = float(value)
        self.threshold_value_label.configure(text=f"Current: {float(value):.2f}")

    def update_limit(self, value):
        self.controller.max_vehicle_limit = int(value)
        self.limit_value_label.configure(text=f"Current: {int(value)}")
    
    def back_to_home(self):
        role = self.controller.current_role
        if role == "Admin":
            self.controller.show_frame("AdminHomePage")
        else:
            self.controller.show_frame("UserHomePage")




if __name__ == "__main__":
    app = ParkingPulseApp()
    app.mainloop()
