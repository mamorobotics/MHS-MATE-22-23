import seamoth
import zlib
import cv2


def main():
    conn = seamoth.DataConnection()
    controller = seamoth.Controller(0)

    ui = seamoth.UI(backgroundColor="#333333", accentColor="#ff6a00")

    ui.connInfo = (conn.IP, 1951)
    ui.connectionStatus = "Waiting for Connection"
    conn.serverStart(1951)

    while True:
        ui.connectionStatus = f"Connected with {conn.connectionAddress[0]} on port {conn.PORT}"

        ui.controllerValues = controller.controllerValues
        ui.controllerValues.A = ui.customOne
        ui.controllerValues.B = ui.customTwo
        ui.controllerValues.X = ui.customThree
        ui.controllerValues.Y = ui.customFour

        conn.send(controller.controllerValues.toString().encode('utf-8'), 12)

        if conn.output[0] == 11:
            ui.frame = cv2.rotate(seamoth.Camera.decode(zlib.decompress(conn.output[1])), cv2.ROTATE_180)

if __name__ == "__main__":
    main()
