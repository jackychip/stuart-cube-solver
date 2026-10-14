from config import ARM_PORT, ARM_ID, CAMERA_NAME
from core.arm import Arm
from core.camera import Camera
from core.markers import MarkerDetector
from routines.observe import check_observe

arm = Arm(ARM_PORT, ARM_ID)
cam = Camera(CAMERA_NAME)
detector = MarkerDetector()

try:
    check_observe(arm, cam, detector, duration=1.5)
finally:
    cam.close()
    input("support the arm, then press enter to disconnect")
    arm.disconnect()