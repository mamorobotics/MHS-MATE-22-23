import seamoth
import sys
import zlib

camera = seamoth.Camera()

while True:
    frame = camera.readCameraData()
    compressedFrame = zlib.compress(seamoth.Camera.encode(frame, 10))
    print(sys.getsizeof(frame) / sys.getsizeof(compressedFrame))

