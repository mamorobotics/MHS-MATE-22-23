import seamoth
import zlib


def main():
    camera = seamoth.Camera()
    conn = seamoth.DataConnection()

    conn.clientStart("10.11.105.62", 1951)

    qual = 100

    while True:
        conn.send(zlib.compress(seamoth.Camera.encode(seamoth.Camera.resize(camera.readCameraData(), 1248, 702), qual)))

        conn.sendTelemetry("qual", str(qual))

        if (conn.output[0] == 13):
            qual = int(conn.output[1].decode('utf-8'))



if __name__ == "__main__":
    main()
