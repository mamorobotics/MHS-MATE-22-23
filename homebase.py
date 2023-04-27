import seamoth


def main():
    conn = seamoth.DataConnection()
    controller = seamoth.ControllerValues()

    ui = seamoth.UI(backgroundColor="#333333", accentColor="#ff6a00")

    ui.connInfo = (conn.IP, 1951)
    ui.connectionStatus = "Waiting for Connection"
    conn.serverStart(1951)

    while True:
        ui.connectionStatus = f"Connected with {conn.connectionAddress[0]} on port {conn.PORT}"

        controller.A = ui.customOne / 100
        conn.send(controller.toString().encode('utf-8'), 12)


if __name__ == "__main__":
    main()
