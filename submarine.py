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

    qual = 70

    a_down = False
    basic_movement = False

    while True:
        conn.send(seamoth.Camera.encode(seamoth.Camera.resize(camera.readCameraData(), 1248, 702), qual))

        if conn.output[0] == 12:
            controllerValues = seamoth.ControllerValues.fromString(conn.output[1].decode('utf-8'))

        if conn.output[0] == 13:
            qual = int(conn.output[1].decode('utf-8'))

        if controllerValues.A > 0.5:
            if not a_down:
                a_down = True
                basic_movement = not basic_movement
        else:
            a_down = False

        if basic_movement:
            left = controllerValues.LeftJoystickY
            right = controllerValues.LeftJoystickY

            if controllerValues.LeftJoystickX > 0.5:
                right = -right

            if controllerValues.LeftJoystickX < -0.5:
                left = -left

            LF.setSpeed(left)
            RF.setSpeed(right)
        else:
            X = -controllerValues.LeftJoystickX * 100
            Y = controllerValues.LeftJoystickY * 100
            V = (100 - abs(X)) * (Y / 100) + Y
            W = (100 - abs(Y)) * (X / 100) + X
            R = (V + W) / 2
            L = (V - W) / 2

            LF.setSpeed(L / 100)
            RF.setSpeed(R / 100)

        LU.setSpeed(controllerValues.RightJoystickY)
        RU.setSpeed(controllerValues.RightJoystickY)
        Claw.setPosition(controllerValues.LeftTrigger)


if __name__ == "__main__":
    main()
