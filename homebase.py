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

    def setFrame(output):
        if output[0] == 11:
            ui.setFrame(seamoth.Camera.decode(zlib.decompress(output[1])))

    conn.onReceive(setFrame)

    while True:
        ui.connectionStatus = f"Connected with {conn.connectionAddress[0]} on port {conn.PORT}"

        ui.controllerValues = controller.controllerValues

        conn.send(controller.controllerValues.toString().encode('utf-8'), 12)
        conn.send(str(ui.customOne).encode('utf-8'), 13)

if __name__ == "__main__":
    main()
