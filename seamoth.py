import datetime
import PIL
import cv2
import json
import numpy
import socket
import os
import time
from PIL import ImageTk, Image, ImageOps
from inputs import devices
from threading import Thread
from tkinter import *

ResourcesPath = "resources"

logs = []

telemetryLog = {}

try:
    from ctypes import windll

    windll.shcore.SetProcessDpiAwareness(1)
except ImportError or ImportWarning:
    logs.append("[ERROR] ctypes not found; window sharpening not possible\n")
    print('[ERROR] ctypes not found; window sharpening not possible')

try:
    os.system("sudo pigpiod")
    time.sleep(1)
    import pigpio

    global PI
    PI = pigpio.pi()
except:
    logs.append('[ERROR] RPi.GPIO not found; hardware control not possible\n')
    print('[ERROR] RPi.GPIO not found; hardware control not possible')


class ControllerValues:
    """
    A class primarily used to store the values of the controller. It is returned by the controller class when you try to access its values.

    To send it over a data connection you can access its value in a dictionary format with:

    ``dict = values.getDict()``

    and you can turn this dict back into a Controller values object using from dict as such:

    ``values = ControllerValues.fromDict(dict)``
    """

    LeftJoystickY = 0
    LeftJoystickX = 0
    RightJoystickY = 0
    RightJoystickX = 0
    LeftTrigger = 0
    RightTrigger = 0
    LeftBumper = 0
    RightBumper = 0
    A = 0
    X = 0
    Y = 0
    B = 0
    LeftThumb = 0
    RightThumb = 0
    Back = 0
    Start = 0
    DpadY = 0
    DpadX = 0

    @staticmethod
    def fromString(controllerValueString: str):
        """
        Turns a dictionary into a ControllerValue object.

        :param controllerValueDict: dictionary of controller values
        :return: ControllerValues object
        """

        controllerValueList = json.loads(controllerValueString)

        controllerValues = ControllerValues()
        controllerValues.LeftJoystickY = controllerValueList[0]
        controllerValues.LeftJoystickX = controllerValueList[1]
        controllerValues.RightJoystickY = controllerValueList[2]
        controllerValues.RightJoystickX = controllerValueList[3]
        controllerValues.LeftTrigger = controllerValueList[4]
        controllerValues.RightTrigger = controllerValueList[5]
        controllerValues.LeftBumper = controllerValueList[6]
        controllerValues.RightBumper = controllerValueList[7]
        controllerValues.A = controllerValueList[8]
        controllerValues.X = controllerValueList[9]
        controllerValues.Y = controllerValueList[10]
        controllerValues.B = controllerValueList[11]
        controllerValues.LeftThumb = controllerValueList[12]
        controllerValues.RightThumb = controllerValueList[13]
        controllerValues.Back = controllerValueList[14]
        controllerValues.Start = controllerValueList[15]
        controllerValues.DpadY = controllerValueList[16]
        controllerValues.DpadX = controllerValueList[17]
        return controllerValues

    def toString(self) -> str:
        """
        Turns a ControllerValue object into a string for easy network sending.

        :return: string containing the controller values
        """
        return json.dumps(
            [self.LeftJoystickY, self.LeftJoystickX, self.RightJoystickY, self.RightJoystickX, self.LeftTrigger,
             self.RightTrigger, self.LeftBumper, self.RightBumper, self.A, self.X, self.Y, self.B, self.LeftThumb,
             self.RightThumb, self.Back, self.Start, self.DpadY, self.DpadX])


class Controller:
    """
    `Note: Some code in this class is a modified version of the tensorkart project's implementation of controller
    input detection by kevinhughes27 on GitHub.`

    Controllers are currently tested to work with XInput designed controllers,
    however controls should be relatively normalized for other types of controllers.
    The class runs in a separate thread to read controller input and assigns read values to an internal
    buffer in the object.

    Reading the controllers in your main loop is as simple as creating a controller object:
    ``controller = Controller()``

    and then gabbing the controllerValue buffer:
    ``values = controller.controllerValues``

    These values are returned as a ControllerValue object.

    :param controllerPort: controller identifier number
    """

    MAX_TRIG_VAL = float(256)
    MAX_JOY_VAL = float(32768)

    controllerValues = ControllerValues()

    def __init__(self, controllerPort: int):
        self.controllerPort = controllerPort

        # checking to make sure that controllers exist before initiated
        if len(devices.gamepads) < 1:
            logs.append("[ERROR] unable to find a connected controller\n")

        else:
            # controller value monitor thread start
            self.thread = Thread(target=self._monitor_controller, args=())
            self.thread.daemon = True
            self.thread.start()

    #
    def _monitor_controller(self):
        gamepad = devices.gamepads[self.controllerPort]

        while True:
            events = gamepad.read()
            for event in events:
                if event.code == 'ABS_Y':
                    self.controllerValues.LeftJoystickY = event.state / Controller.MAX_JOY_VAL  # normalize between -1 and 1
                elif event.code == 'ABS_X':
                    self.controllerValues.LeftJoystickX = event.state / Controller.MAX_JOY_VAL  # normalize between -1 and 1
                elif event.code == 'ABS_RY':
                    self.controllerValues.RightJoystickY = event.state / Controller.MAX_JOY_VAL  # normalize between -1 and 1
                elif event.code == 'ABS_RX':
                    self.controllerValues.RightJoystickX = event.state / Controller.MAX_JOY_VAL  # normalize between -1 and 1
                elif event.code == 'ABS_Z':
                    self.controllerValues.LeftTrigger = event.state / Controller.MAX_TRIG_VAL  # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.controllerValues.RightTrigger = event.state / Controller.MAX_TRIG_VAL  # normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.controllerValues.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.controllerValues.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.controllerValues.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.controllerValues.X = event.state
                elif event.code == 'BTN_WEST':
                    self.controllerValues.Y = event.state
                elif event.code == 'BTN_EAST':
                    self.controllerValues.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.controllerValues.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.controllerValues.RightThumb = event.state
                elif event.code == 'BTN_SELECT':
                    self.controllerValues.Back = event.state
                elif event.code == 'BTN_START':
                    self.controllerValues.Start = event.state
                elif event.code == 'ABS_HAT0Y':
                    self.controllerValues.DpadY = -event.state
                elif event.code == 'ABS_HAT0X':
                    self.controllerValues.DpadX = event.state


class Motor:
    """
    **Motor is not multithreaded, expect some lag on initialization as we set up stuff**

    The motor class represents a motor. It takes no inputs and has three functions, ``setMotor()``, ``setSpeed()``, ``calibrateMotor()``.
    It is designed to be used with the Blue Robotics ESC but theoretically can work with any esc.

    To set a motor you need to have a file within the resources directory called hardwareMap.txt,
    which specifies the names and ports of all connected servos and motors. This file should follow the format of:

    ``{ "name": port }``

    the file should also have a config of the pwm values used by your esc as such:

    ``"PWMConfig": [lowestValue, zeroValue, highestValue],``
    """

    def __init__(self):
        self.hardwareMap = json.loads(open(f"{ResourcesPath}/hardwareMap.txt", "r").read())
        self.port = 0

    def setMotor(self, name: str):
        """
        Assigns the motor to ports specified in the hardware map.

        :param name: the name of the motor in the hardware map
        """

        if name in self.hardwareMap:
            self.port = int(self.hardwareMap[name])
            PI.set_mode(self.port, pigpio.OUTPUT)
            PI.set_servo_pulsewidth(self.port, self.hardwareMap["MotorPWMConfig"][1])
            self.calibrateMotor()
        else:
            logs.append("[ERROR] Cannot find motor \"" + name + "\" on hardware map.\n")

    def calibrateMotor(self):
        """
        Calibrates/initializes the esc. In most cases this shouldn't really be used.
        """
        PI.set_servo_pulsewidth(self.port, self.hardwareMap["MotorPWMConfig"][1])
        time.sleep(3)

    def setSpeed(self, speed: float):
        """
        Sets the speed of the motor the function is called on.

        :param speed: speed of motor (-1 - 1)
        """
        pwmSignal = ((speed + 1) / 2) * (self.hardwareMap["MotorPWMConfig"][2] - self.hardwareMap["MotorPWMConfig"][0]) + self.hardwareMap["MotorPWMConfig"][0]

        PI.set_servo_pulsewidth(self.port, pwmSignal)


class Servo:
    """
    **Servo is not multithreaded, expect some lag on initialization as we set up stuff.**

    The servo class represents a servo. It takes no inputs and has three functions, ``setServo()``, ``setPosition()``, ``calibrateServo()``.
    It is designed to be used with the Blue Robotics ESC but theoretically can work with any esc.

    To set a servo you need to have a file within the resources directory called hardwareMap.txt,
    which specifies the names and ports of all connected servos and motors. This file should follow the format of:

    ``{ "name": port }``

    the file should also have a config of the pwm values used by your esc as such:

    ``"ServoPWMConfig": [lowestValue, highestValue],``
    """

    def __init__(self):
        self.hardwareMap = json.loads(open(f"{ResourcesPath}/hardwareMap.txt", "r").read())
        self.port = 0

    def setServo(self, name: str):
        """
        Assigns the servo to ports specified in the hardware map.

        :param name: the name of the servo in the hardware map
        """

        if name in self.hardwareMap:
            self.port = int(self.hardwareMap[name])
            PI.set_mode(self.port, pigpio.OUTPUT)
            PI.set_servo_pulsewidth(self.port, self.hardwareMap["ServoPWMConfig"][0])
            self.calibrateServo()
        else:
            logs.append("[ERROR] Cannot find servo \"" + name + "\" on hardware map.\n")

    def calibrateServo(self):
        """
        Calibrates/initializes the esc. In most cases this shouldn't really be used.
        """
        PI.set_servo_pulsewidth(self.port, self.hardwareMap["ServoPWMConfig"][0])
        time.sleep(3)

    def setPosition(self, position: float):
        """
        Sets the position of the servo the function is called on.

        :param position: position of servo (0 - 1)
        """
        pwmSignal = position * (self.hardwareMap["ServoPWMConfig"][1] - self.hardwareMap["ServoPWMConfig"][0]) + self.hardwareMap["ServoPWMConfig"][0]

        PI.set_servo_pulsewidth(self.port, pwmSignal)


class Camera:
    """
    The controller class takes in no inputs, and instead reads from the first camera that it finds.
    The class stores the active camera connection and reads on a function call.
    Reading the camera data in your main loop is as simple as calling the read function such as:

    ``image = camera.readCameraData()``

    Which returns a Cv2 image array

    The class also includes two functions for encoding and decoding the above image for transmission,
    aptly named ``encode()`` and ``decode()``, and a function for resizing an image, named ``resize()``.
    """

    _calls = 0
    _bufferframe = ""

    def _queryCamera(self):
        while True:
            ret, frame = self.capture.read()
            while not ret:
                ret, frame = self.capture.read()
            self.frame = frame

    def readCameraData(self):
        """
        Reads the current camera image.

        :return: Cv2 image object
        """
        return self.frame

    @staticmethod
    def encode(image, quality: int):
        """
        Encodes and compressed a Cv2 image to make it possible to send over the internet.

        :param image: Cv2 image object
        :param quality: quality of Jpeg compression

        :return: Compressed byte array representation of input image
        """

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
        return cv2.imencode('.jpg', image, encode_param)[1].tobytes()

    @staticmethod
    def decode(image):
        """
        Decodes and decompresses an image encoded with *encode()*.

        :param image: compressed byte array representation of image

        :return: Cv2 image object
        """

        npimg = numpy.frombuffer(image, numpy.uint8)
        return cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    @staticmethod
    def resize(image, x: int, y: int):
        """
        Resizes an image.

        :param image: Cv2 image object
        :param x: image X
        :param y: image Y

        :return: resized Cv2 image object
        """
        return cv2.resize(image, (x, y), interpolation=cv2.INTER_AREA)

    def __init__(self, size: tuple = (1248, 702)):
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])

        ret, frame = self.capture.read()
        while not ret:
            ret, frame = self.capture.read()
        self.frame = frame

        Thread(target=self._queryCamera, args=()).start()


# all the GUI stuff
class UI:
    """
    The class is currently uses tkinter and is meant to be used as your viewport to the submarine.
    The class runs entirely in a separate thread and shows the video from an internal buffer.
    You can write to the ui by referencing the internal buffer such as:

    ``ui.frame = frame``

    Which is expected to be the frame data from the camera class.
    Camera and UI are separate to allow data connections through an
    internet connection or other similar connections without impeding functionality.

    You can specify which menus should be active or inactive with the menus input with the following possible menus:

    * connDetails
    * connStatus
    * input
    * output
    * custom
    * video
    * telemetry

    The ui class can later be referenced to access or set:

    * **Video Frame** : ``ui.frame`` = most recent frame of video, the ui class reads this every 20ms
    * **Connection Status** : ``ui.connectionStatus`` = status where status is a string representing the current status
    * **Connection Info** : ``ui.connInfo`` = (ip, port) where the tuple of ip and port represents the ip and port you
    are listening from (these can be retrieved from the DataConnection class with conn.IP and conn.PORT respectively.)
    * **Input Data** : ``ui.controllerValues`` = controllerValues where controllerValues is the dictionary outputted
    by the Controller class

    :param videoSize: default video viewport size
    :param menus: dictionary of which menus to keep active. All are on by default.
    :param accentColor: accent color of the ui
    :param backgroundColor: background color of the ui
    """

    fullscreen = False

    controllerValues = ControllerValues()

    menus = {}

    customOne = 0
    customTwo = 0
    customThree = 0
    customFour = 0
    customFive = 0

    fps = 60
    frameTimeLast = datetime.datetime.now()

    def _fullscreen(self):
        winFull = Tk()
        winFull.title(f"Seamoth Fullscreen ({self.teamName})")

        videoFull = Label(winFull)
        videoFull.pack()

        # main loop
        def updateFrame():
            cv2image = cv2.cvtColor(Camera.resize(self.frame, 1920, 1080), cv2.COLOR_BGR2RGB)
            img = PIL.Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img, master=winFull)
            videoFull.imgtk = imgtk
            videoFull.configure(image=imgtk)

            if self.fullscreen:
                videoFull.after(10, updateFrame)
            else:
                winFull.destroy()

        updateFrame()
        winFull.mainloop()

    def openFullscreen(self):
        self.fullscreenthread = Thread(target=self._fullscreen, args=())
        self.fullscreenthread.start()

    def closeFullscreen(self):
        self.fullscreenthread.join()

    def setFrame(self, frame):
        """
        Sets a frame

        :param frame: an image from the camera class
        :return:
        """

        self.frame = frame
        diff = datetime.datetime.now() - self.frameTimeLast
        self.fps = round((1000 / (diff.microseconds / 1000 + .01) + (self.fps * 10)) / 11)
        self.frameTimeLast = datetime.datetime.now()

    def setTelemetry(self, index, value):
        telemetryLog[index] = value

    def _ui(self):
        win = Tk()
        win.title(f"Seamoth Homebase ({self.teamName})")
        win.config(bg=self.backgroundColor)
        win.iconbitmap(f'{ResourcesPath}/favicon.ico')

        if self.connInfo[1] == 1951:
            logs.append("Good luck MHS! \n")

        video = Label(win, background=self.accentColor)
        video.grid(row=0, column=0)

        # details
        details = Frame(win, bg=self.backgroundColor)
        details.grid(row=0, column=1, sticky=N, rowspan=2)

        def fullscreenChange(value):
            if fullscreenSlider.get() == 1:
                self.fullscreen = True
                self.openFullscreen()
            else:
                self.fullscreen = False
                self.closeFullscreen()

        # conn details settings
        if self.menus.get("connDetails", True):
            connDetailsFrame = Frame(details, bg=self.backgroundColor)
            connDetailsFrame.grid(row=0, column=0, sticky=W, ipadx=10, pady=5, padx=5)
            Label(connDetailsFrame, text="CONNECTION DETAILS:", bg=self.backgroundColor, foreground=self.accentColor).pack(side=TOP, anchor=W)
            connDetailsIP = Label(connDetailsFrame, text="1.1.1.1", bg=self.backgroundColor, foreground=self.accentColor)
            connDetailsIP.pack(side=TOP, anchor=W)
            connDetailsPORT = Label(connDetailsFrame, text="1111", bg=self.backgroundColor, foreground=self.accentColor)
            connDetailsPORT.pack(side=TOP, anchor=W)
            fpsLabel = Label(connDetailsFrame, text="0", bg=self.backgroundColor, foreground=self.accentColor)
            fpsLabel.pack(side=TOP, anchor=W)

        # conn status settings
        if self.menus.get("connStatus", True):
            connStatusFrame = Frame(details, bg=self.backgroundColor)
            connStatusFrame.grid(row=1, column=0, sticky=W, ipadx=10, pady=5, padx=5)
            Label(connStatusFrame, text="CONNECTION STATUS:", bg=self.backgroundColor, foreground=self.accentColor).pack(side=TOP, anchor=W)
            connStatus = Label(connStatusFrame, text=self.connectionStatus, bg=self.backgroundColor, foreground=self.accentColor)
            connStatus.pack(side=TOP, anchor=W)

        # input settings
        if self.menus.get("input", True):
            inputDetailsFrame = Frame(details, bg=self.backgroundColor)
            inputDetailsFrame.grid(row=2, column=0, sticky=W, ipadx=10, pady=5, padx=5)
            Label(inputDetailsFrame, text="INPUT DETAILS:", bg=self.backgroundColor, foreground=self.accentColor).grid(row=0, column=0, sticky=W)

            inputDetailsJoyFrame = Frame(inputDetailsFrame, bg=self.backgroundColor)
            inputDetailsJoyFrame.grid(row=1, column=0, sticky=W, ipadx=10, pady=5, padx=5)
            inputJoyLeftX = Scale(inputDetailsJoyFrame, from_=-1, to=1, resolution=0.01, orient=HORIZONTAL,
                                  label="Left Joy X", showvalue=False, bg=self.backgroundColor, foreground=self.accentColor,
                                  highlightthickness=0)
            inputJoyLeftX.pack(side=TOP, anchor=W)
            inputJoyLeftY = Scale(inputDetailsJoyFrame, from_=-1, to=1, resolution=0.01, orient=HORIZONTAL,
                                  label="Left Joy Y", showvalue=False, bg=self.backgroundColor, foreground=self.accentColor,
                                  highlightthickness=0)
            inputJoyLeftY.pack(side=TOP, anchor=W)
            inputJoyRightX = Scale(inputDetailsJoyFrame, from_=-1, to=1, resolution=0.01, orient=HORIZONTAL,
                                   label="Right Joy X", showvalue=False, bg=self.backgroundColor, foreground=self.accentColor,
                                   highlightthickness=0)
            inputJoyRightX.pack(side=TOP, anchor=W)
            inputJoyRightY = Scale(inputDetailsJoyFrame, from_=-1, to=1, resolution=0.01, orient=HORIZONTAL,
                                   label="Right Joy Y", showvalue=False, bg=self.backgroundColor, foreground=self.accentColor,
                                   highlightthickness=0)
            inputJoyRightY.pack(side=TOP, anchor=W)

            inputDetailsTrigFrame = Frame(inputDetailsFrame, bg=self.backgroundColor)
            inputDetailsTrigFrame.grid(row=1, column=1, sticky=NW, ipadx=10, pady=5, padx=5)
            inputTrigRight = Scale(inputDetailsTrigFrame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL,
                                   label="Right Trigger", showvalue=False, bg=self.backgroundColor, foreground=self.accentColor,
                                   highlightthickness=0)
            inputTrigRight.pack(side=TOP, anchor=W)
            inputTrigLeft = Scale(inputDetailsTrigFrame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL,
                                  label="Left Trigger", showvalue=False, bg=self.backgroundColor, foreground=self.accentColor,
                                  highlightthickness=0)
            inputTrigLeft.pack(side=TOP, anchor=W)

        # log
        if self.menus.get("output", True):
            logDetailsFrame = Frame(details, bg=self.backgroundColor, bd=1)
            logDetailsFrame.grid(row=3, column=0, sticky=W, pady=5, padx=5)
            Label(logDetailsFrame, text="OUTPUT:", bg=self.backgroundColor, foreground=self.accentColor).grid(row=0, column=0, sticky=W)
            logBox = Text(logDetailsFrame, bg=self.backgroundColor, foreground=self.accentColor, height=15, width=60)
            logBox.grid(row=1, column=0, sticky=W)

        # image
        if self.menus.get("image", True):
            image = Label(details, bg=self.backgroundColor)
            image.grid(row=4, column=0)

            img = PIL.Image.open(os.getcwd().replace("\\", "/") + f"/{ResourcesPath}/logo.png")

            r, g, b, alpha = img.split()
            img = ImageOps.colorize(PIL.ImageOps.grayscale(img), (0, 0, 0, 0), self.accentColor)
            img.putalpha(alpha)

            imgratio = img.height / img.width
            img = img.resize((int(135 / imgratio), 135))
            uiImage = ImageTk.PhotoImage(img)
            image.imgtk = uiImage
            image.configure(image=uiImage)

        # settings
        settings = Frame(win, bg=self.backgroundColor)
        settings.grid(row=1, column=0, sticky=W)

        # custom values
        if self.menus.get("custom", True):
            customSettingsFrame = Frame(settings, bg=self.backgroundColor)
            customSettingsFrame.grid(row=0, column=0, sticky=W, pady=5, padx=5)

            Label(customSettingsFrame, text="CUSTOMIZABLE VALUES:", bg=self.backgroundColor, foreground=self.accentColor).grid(row=0, column=0, sticky=W)

            customSettingsSlidersFrame = Frame(customSettingsFrame, bg=self.backgroundColor)
            customSettingsSlidersFrame.grid(row=1, column=0, sticky=W, pady=5, padx=5)

            customOne = Scale(customSettingsSlidersFrame, from_=0, to=100, resolution=1, orient=VERTICAL, label="1",
                              bg=self.backgroundColor, foreground=self.accentColor, highlightthickness=0)
            customOne.pack(side=LEFT, anchor=W)
            customTwo = Scale(customSettingsSlidersFrame, from_=0, to=100, resolution=1, orient=VERTICAL, label="2",
                              bg=self.backgroundColor, foreground=self.accentColor, highlightthickness=0)
            customTwo.pack(side=LEFT, anchor=W)
            customThree = Scale(customSettingsSlidersFrame, from_=0, to=100, resolution=1, orient=VERTICAL, label="3",
                                bg=self.backgroundColor, foreground=self.accentColor, highlightthickness=0)
            customThree.pack(side=LEFT, anchor=W)
            customFour = Scale(customSettingsSlidersFrame, from_=0, to=100, resolution=1, orient=VERTICAL, label="4",
                               bg=self.backgroundColor, foreground=self.accentColor, highlightthickness=0)
            customFour.pack(side=LEFT, anchor=W)
            customFive = Scale(customSettingsSlidersFrame, from_=0, to=100, resolution=1, orient=VERTICAL, label="5",
                               bg=self.backgroundColor, foreground=self.accentColor, highlightthickness=0)
            customFive.pack(side=LEFT, anchor=W)

        # video settings
        if self.menus.get("video", True):
            videoSettingsFrame = Frame(settings, bg=self.backgroundColor)
            videoSettingsFrame.grid(row=0, column=1, sticky=N, pady=5, padx=5)

            Label(videoSettingsFrame, text="VIDEO SETTINGS:", bg=self.backgroundColor, foreground=self.accentColor).grid(row=0, column=0, sticky=W)

            Label(videoSettingsFrame, text="Open fullscreen window:", bg=self.backgroundColor, foreground=self.accentColor).grid(row=1, column=0, sticky=W)
            fullscreenSlider = Scale(videoSettingsFrame, from_=0, to=1, resolution=1, orient=HORIZONTAL, bg=self.backgroundColor, foreground=self.accentColor, highlightthickness=0, command=fullscreenChange)
            fullscreenSlider.grid(row=1, column=1, sticky=W)

            Label(videoSettingsFrame, text="Pause video feed:", bg=self.backgroundColor, foreground=self.accentColor).grid(row=2, column=0, sticky=W)
            pauseSlider = Scale(videoSettingsFrame, from_=0, to=1, resolution=1, orient=HORIZONTAL, bg=self.backgroundColor, foreground=self.accentColor, highlightthickness=0)
            pauseSlider.grid(row=2, column=1, sticky=W)

        # telemetry
        if self.menus.get("telemetry", True):
            telemetryFrame = Frame(settings, bg=self.backgroundColor)
            telemetryFrame.grid(row=0, column=2, sticky=N, pady=5, padx=5)
            Label(telemetryFrame, text="TELEMETRY:", bg=self.backgroundColor, foreground=self.accentColor).grid(row=0, column=0, sticky=W)
            telemetryBox = Text(telemetryFrame, bg=self.backgroundColor, foreground=self.accentColor, height=4, width=32)
            telemetryBox.grid(row=1, column=0, sticky=W)

        # main loop
        def updateFrame():
            if len(logs) > 15:
                logs.pop(0)
            if len(telemetryLog) > 4:
                telemetryLog.pop(0)

            # conn details/status managers
            if self.menus.get("connDetails", True):
                connDetailsIP.configure(text=f"IP: {self.connInfo[0]}")
                connDetailsPORT.configure(text=f"PORT: {self.connInfo[1]}")
                fpsLabel.configure(text=f"FPS: {self.fps}")

            if self.menus.get("connStatus", True):
                connStatus.configure(text=self.connectionStatus)

            # custom values manager
            if self.menus.get("custom", True):
                self.customOne = customOne.get()
                self.customTwo = customTwo.get()
                self.customThree = customThree.get()
                self.customFour = customFour.get()
                self.customFive = customFive.get()

            # input display manager
            if self.menus.get("input", True):
                inputJoyLeftX.set(float(self.controllerValues.LeftJoystickX))
                inputJoyLeftY.set(float(self.controllerValues.LeftJoystickY))
                inputJoyRightX.set(float(self.controllerValues.RightJoystickX))
                inputJoyRightY.set(float(self.controllerValues.RightJoystickY))
                inputTrigLeft.set(float(self.controllerValues.LeftTrigger))
                inputTrigRight.set(float(self.controllerValues.RightTrigger))

            # log manager
            if self.menus.get("output", True):
                logBox.delete("1.0", "end")
                for log in logs:
                    logBox.insert(INSERT, log)

            # telemetry manager
            if self.menus.get("telemetry", True):
                telemetryBox.delete("1.0", "end")
                for key in telemetryLog:
                    telemetryBox.insert(INSERT, f"{key}: {telemetryLog[key]}\n")

            # video manager
            if pauseSlider.get() == 0:
                cv2image = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                img = PIL.Image.fromarray(cv2image)
                imgtk = ImageTk.PhotoImage(image=img)
                video.imgtk = imgtk
                video.configure(image=imgtk)

            if self.running:
                video.after(10, updateFrame)

        updateFrame()
        win.mainloop()

    def __init__(self, videoSize: tuple = (1248, 702), menus=None, accentColor: str = "#187082", backgroundColor: str = "#eeeeee", teamName: str = "MHS Tiger Sharks"):
        if menus is None:
            menus = {}
        self.running = True
        self.menus = menus
        self.frame = numpy.array(PIL.Image.new(mode="RGB", size=videoSize, color=rgbFromHex(backgroundColor)))
        self.connectionStatus = "Starting"
        self.connInfo = ("1.1.1.1", "1111")
        self.mainthread = Thread(target=self._ui, args=())
        self.mainthread.start()

        self.backgroundColor = backgroundColor

        self.accentColor = accentColor

        self.videoFullscreen = False
        self.videoPaused = False
        self.teamName = teamName


# black magic voodoo, don't really feel like commenting all of it
class DataConnection:
    """
    The controller class is separated into two types, server and client, and is built on a UDP based architecture.
    All data received by the server is stored within its internal ``output`` buffer for asynchronous reading.
    This buffer stores the main message and the specified header as ``(header, message)``.

    You can send messages with the ``send()`` function.

    **header values 0-10 are reserved for system functions**
    """

    output = (0, b'')
    connected = False
    recvFunctions = []

    def __init__(self):
        self.IP = socket.gethostbyname(socket.gethostname())

    def _listen(self):
        while True:
            msg_len = None
            while not msg_len:
                try:
                    msg_len = self.connection.recv(64).decode('utf-8')
                except:
                    pass

            if int(msg_len) > 100:
                telemetryLog["Size"] = int(msg_len)

            header = int(self.connection.recv(16).decode('utf-8'))

            message = bytearray()
            while len(message) < int(msg_len):
                packet = self.connection.recv(int(msg_len) - len(message))
                message.extend(packet)

            if header == 1:
                logs.append("[ERROR]" + message.decode('utf-8') + "\n")
            if header == 2:
                logs.append("[WARNING]" + message.decode('utf-8') + "\n")
            if header == 3:
                msgParts = message.decode('utf-8').split("!")
                telemetryLog[msgParts[0]] = msgParts[1]
            if header > 10:
                self.output = (header, message)

                for func in self.recvFunctions:
                    func((header, message))

    def onReceive(self, func):
        """
        Calls function ``func`` whenever a message is received. The message is passed into the function.
        This can be done as such:

        ``conn.onRecieve(setFrame)``
        Where ``setFrane`` is a function that handles your frame.

        :param func: function to be called. must contain a input for a message value
        :return:
        """
        self.recvFunctions.append(func)

    def clientStart(self, ip: str, port: int):
        """
        Starts a client to connect to a server and will send received messages to the objects ``output`` buffer.

        :param ip: ip of the server
        :param port: port of the server
        """

        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((ip, port))

        self.thread = Thread(target=self._listen, args=())
        self.thread.start()

    def serverStart(self, port: int):
        """
        Starts a server and will send received messages to the objects ``output`` buffer.

        :param port: port of the server
        """

        self.PORT = int(port)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.IP, self.PORT))

        self.server.listen()
        self.connection, self.connectionAddress = self.server.accept()

        self.connected = True

        self.thread = Thread(target=self._listen, args=())
        self.thread.start()

        return self.IP

    def sendError(self, msg: str):
        """
        Sends an error message directly to the log.

        :param msg: error msg
        """
        self.send(msg.encode('utf-8'), 1)

    def sendWarning(self, msg: str):
        """
        Sends a warning message data directly to the log.

        :param msg: warning msg
        """
        self.send(msg.encode('utf-8'), 2)

    def sendTelemetry(self, name: str, value):
        """
        Sends telemetry directly to the ui.

        :param name: name of the telemetry
        :param value: value of the telemetry
        """
        msg = name + "!" + str(value)
        if msg.count('!') == 1:
            msg = msg.encode('utf-8')
            self.send(msg, 3)
        else:
            self.sendWarning(f"Telemetry message {msg} cannot be sent")

    def send(self, msg: bytes, header: int = 11):
        """
        Sends a message to all servers or clients connected to the program.

        :param msg: message that you want to send in a byte form
        :param header: message header value **header values 0-10 are reserved for system functions**
        """

        send_length = str(len(msg)).encode('utf-8')
        send_length += b' ' * (64 - len(send_length))

        header = str(header).encode('utf-8')
        header += b' ' * (16 - len(header))

        self.connection.send(send_length)
        self.connection.send(header)
        self.connection.send(msg)


def rgbFromHex(hex_string):
    r = int(hex_string[1:3], 16)
    g = int(hex_string[3:5], 16)
    b = int(hex_string[5:7], 16)

    return r, g, b
