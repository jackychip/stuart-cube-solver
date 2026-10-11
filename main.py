import time
import cv2

from core.camera import Camera, list_cameras
from core.markers import MarkerDetector
from core.arm import Arm
from routines.observe import teach_observe, check_observe
from routines.wiggle import wiggle

list_cameras()

arm = Arm("/dev/tty.usbmodem5B415336751", "stuart_follower")
cam = Camera("icspring")
detector = MarkerDetector()

try:
    print("start:", arm.read())
    check_observe(arm, cam, detector, duration=1)
finally:
    cam.close()
    input("support the arm, then press enter to disconnect")
    arm.disconnect()