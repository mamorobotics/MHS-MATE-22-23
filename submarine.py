import seamoth


def main():
    camera = seamoth.Camera()
    conn = seamoth.DataConnection()

    testMotor = seamoth.Motor()
    testServo = seamoth.Servo()

    controllerValues = seamoth.ControllerValues()

    testMotor.setMotor("testMotor")
    testServo.setServo("testServo")

    conn.clientStart("0.0.0.0", 1951)

    while True:
        conn.send(seamoth.Camera.encode(seamoth.Camera.resize(camera.readCameraData(), 1248, 702), 90))

        if conn.output[0] == 12:
            controllerValues = seamoth.ControllerValues.fromString(conn.output[1].decode('utf-8'))

        testServo.setPosition(controllerValues.RightTrigger)

        testMotor.setSpeed(controllerValues.LeftJoystickY)


if __name__ == "__main__":
    main()
