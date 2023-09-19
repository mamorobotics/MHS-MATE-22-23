import seamoth
import time


def main():
    camera = seamoth.Camera()
    conn = seamoth.DataConnection()

    conn.clientStart("10.11.105.135", 1951)

    qual = 100

    while True:
        conn.send(str(time.perf_counter_ns()).encode('utf-8'), 15)

        conn.send(seamoth.Camera.encode(seamoth.Camera.resize(camera.readCameraData(), 1248, 702), qual), 11)

        conn.sendTelemetry("qual", str(qual))

        if conn.output[0] == 13:
            qual = int(conn.output[1].decode('utf-8'))



if __name__ == "__main__":
    main()
