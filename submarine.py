import seamoth


def main():
    camera = seamoth.Camera()
    conn = seamoth.DataConnection()
    controllerValues = seamoth.ControllerValues()

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

    forward_speed = .75
    qual = 70

    basic_movement = False

    while True:
        conn.send(seamoth.Camera.encode(camera.readCameraData()), qual)

        if conn.output[0] == 12:
            controllerValues = seamoth.ControllerValues.fromString(conn.output[1].decode('utf-8'))

        if conn.output[0] == 13:
            qual = int(conn.output[1].decode('utf-8'))

        if controllerValues.A > 0.5:
            basic_movement = False

        if basic_movement:
            left = controllerValues.LeftJoystickY
            right = controllerValues.LeftJoystickY

            if controllerValues.LeftJoystickX > 0.5:
                right = -right

            if controllerValues.LeftJoystickX < -0.5:
                left = -left

            LF.setSpeed(left * forward_speed)
            RF.setSpeed(right * forward_speed)
        else:
            X = -controllerValues.LeftJoystickX * 100
            Y = controllerValues.LeftJoystickY * 100
            V = (100 - abs(X)) * (Y / 100) + Y
            W = (100 - abs(Y)) * (X / 100) + X
            R = (V + W) / 2
            L = (V - W) / 2

            LF.setSpeed(L / 100 * forward_speed)
            RF.setSpeed(R / 100 * forward_speed)

        LU.setSpeed(controllerValues.RightJoystickY)
        RU.setSpeed(controllerValues.RightJoystickY)
        Claw.setPosition(controllerValues.LeftTrigger)
        conn.sendTelemetry("claw", controllerValues.LeftTrigger)


if __name__ == "__main__":
    main()
