import seamoth


def main():
    camera = seamoth.Camera()
    conn = seamoth.DataConnection()
    controllerValues = seamoth.ControllerValues()

    ForwardSpeed = 1
    TurnSpeed = 0.25

    LU = seamoth.Motor()
    LF = seamoth.Motor()
    RU = seamoth.Motor()
    RF = seamoth.Motor()

    Claw = seamoth.Servo()

    LU.setMotor("LU")
    LF.setMotor("LF")
    RU.setMotor("RU")
    RF.setMotor("RF")

    Claw.setServo("Claw")

    conn.clientStart("0.0.0.0", 1951)

    while True:
        conn.send(seamoth.Camera.encode(seamoth.Camera.resize(camera.readCameraData(), 1248, 702), 90))

        if conn.output[0] == 12:
            controllerValues = seamoth.ControllerValues.fromString(conn.output[1].decode('utf-8'))

        left = controllerValues.LeftJoystickY
        right = controllerValues.LeftJoystickY

        if (controllerValues.LeftJoystickX > 0.5):
            right = -right

        if (controllerValues.LeftJoystickX < -0.5):
            left = -left

        LF.setSpeed(left)
        RF.setSpeed(right)

        LU.setSpeed(controllerValues.RightJoystickY)
        RU.setSpeed(controllerValues.RightJoystickY)

        Claw.setPosition(controllerValues.A)


if __name__ == "__main__":
    main()
