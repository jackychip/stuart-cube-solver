from config import ARM_PORT, ARM_ID, CAMERA_NAME
from core.arm import Arm
from core.camera import Camera
from core.markers import MarkerDetector
from routines.observe import teach_observe

arm = Arm(ARM_PORT, ARM_ID)
cam = Camera(CAMERA_NAME)
detector = MarkerDetector()

try:
    teach_observe(arm, cam, detector)
finally:
    cam.close()
    input("support the arm, then press enter to disconnect")
    arm.disconnect()