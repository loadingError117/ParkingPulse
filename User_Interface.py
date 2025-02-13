# Description: This file contains the code for the user interface of the Parking Pulse project.
from tkinter import *
import temp
from tkinter import filedialog

#================================================================================================
#login validation function
#current login is "admin" and password is "password"
#================================================================================================   
def login_validation():
    global login_window
    global home_page
    # get login and password
    userID = username.get()
    passwordAttempt = password.get()

    # check if login and password are correct
    if userID == "admin" and passwordAttempt == "password":
        print("Login Successful")
        # destroy login page
        login_window.destroy()
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
        login_failed_label = Label(login_window, text="Login Failed", font=("Arial", 12), fg="red", bg="grey")
        login_failed_label.pack(pady=10)

#================================================================================================
#Add Device Window
#================================================================================================
# device add window
def add_device_window():
    add_device = Tk()
    add_device.title("Add Device")
    add_device.geometry("1080x720")
    add_device.configure(bg="grey")

    # create a label for the title
    label = Label(add_device, text="Add Device", font=("Arial", 48), bg="grey")
    label.pack(padx=20, pady=(50, 0))

    # create a frame to hold the buttons
    button_frame = Frame(add_device, bg="grey")
    button_frame.pack(pady=20)

    # create a label for the device name
    device_name_label = Label(add_device, text="Device Name", font=("Arial", 24), bg="grey")
    device_name_label.pack(pady=10)

    # create a device name entry
    device_name = Entry(add_device, width=40)
    device_name.pack(pady=10)

    # create a label for the device IP
    device_IP_label = Label(add_device, text="Device IP", font=("Arial", 24), bg="grey")
    device_IP_label.pack(pady=10)

    # create a device IP entry
    device_IP = Entry(add_device, width=40)
    device_IP.pack(pady=10)

    # create a label for the device username
    device_username_label = Label(add_device, text="Device Username", font=("Arial", 24), bg="grey")
    device_username_label.pack(pady=10)

    # create a device username entry
    device_username = Entry(add_device, width=40)
    device_username.pack(pady=10)

    # create a label for the device password
    device_password_label = Label(add_device, text="Device Password", font=("Arial", 24), bg="grey")
    device_password_label.pack(pady=10)

    # create a device password entry
    device_password = Entry(add_device, width=40)
    device_password.pack(pady=10)

    # create a button to add the device
    add_device_button = Button(add_device, text="Add Device", width=20, height=2)
    add_device_button.pack(pady=10)

    # create a button to go back to the home page
    back_button = Button(add_device, text="Back", width=20, height=2, command=add_device.destroy)
    back_button.pack(pady=10)

    device_url= "rtsp://"+device_username.get()+":"+device_password.get()+"@"+device_IP+":554/live"
    #save the device information to a file for future use
    
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

    # create a button to launch the IPcamera(s)
    IPcamera_button = Button(button_frame, text="Launch IPCamera", width=20, height=10, command=temp.launch_IPcamera)
    IPcamera_button.grid(row=0, column=0, padx=10, pady=10)

    # create a button to launch the webcam
    ##### DELETE THIS BUTTON AFTER TESTING#####
    webcam_button = Button(button_frame, text="Launch WebCam", width=20, height=10, command=temp.launch_webcam)
    webcam_button.grid(row=0, column=1, padx=10, pady=10)

    # create a settings button
    settings_button = Button(button_frame, text="Settings", width=20, height=10)
    settings_button.grid(row=0, column=2, padx=10, pady=10)

    # create add device button
    button4 = Button(button_frame, text="Add Device", width=20, height=10, command=add_device_window)
    button4.grid(row=1, column=0, padx=10, pady=10)
    
    # create a view data button
    button5 = Button(button_frame, text="View Data", width=20, height=10, command=view_data_window)
    button5.grid(row=1, column=1, padx=10, pady=10)
    
    # create a button 6
    button6 = Button(button_frame, text="Button 6", width=20, height=10, command=print("Button 6 pressed"))
    button6.grid(row=1, column=2, padx=10, pady=10)

    
#================================================================================================
#View Data Window
#================================================================================================
def view_data_window():
    view_data_window = Tk()
    view_data_window.title("View Data")
    view_data_window.geometry("1080x720")
    view_data_window.configure(bg="grey")

    # create a label for the title
    label = Label(view_data_window, text="View Data", font=("Arial", 48), bg="grey")
    label.pack(padx=20, pady=(50, 0))

    #function that asks for a file
    def choose_file():
        file_path = filedialog.askopenfilename()
        if file_path:
            #save the file path to a file for future use
            with open("file_path.txt", "w") as file:
                file.write(file_path)

    file_button = Button(view_data_window, text="Choose File", width=20, height=2, command=choose_file)
    file_button.pack(pady=10)

    # create a button to go back to the home page
    back_button = Button(view_data_window, text="Back", width=20, height=2, command=view_data_window.destroy)
    back_button.pack(pady=10)

#================================================================================================
#Login Page Window
#================================================================================================
# login page window
login_window = Tk()
login_window.title("Parking Pulse Login Page")
login_window.geometry("1080x720")
login_window.configure(bg="grey")
# create a label for the title
label = Label(login_window, text="Welcome To Parking Pulse", font=("Arial", 48), bg="grey")
label.pack(padx=20, pady=(225, 0))

# create a login and password entry
username = Entry(login_window, width=40)
username.insert(0, "Username")
username.pack(pady=10)
password = Entry(login_window, width=40, show='*')
password.insert(0, "Password")
password.pack(pady=10)

# create a login button
login_button = Button(login_window, text="Login", width=20, height=2, command=login_validation)
login_button.pack(pady=10)

# run home page
login_window.mainloop()

