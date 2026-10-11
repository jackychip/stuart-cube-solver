import time
from core.arm import Arm
from routines.wiggle import wiggle

arm = Arm("/dev/tty.usbmodem5B415336751", "stuart_follower")

try:
    wiggle(arm)
finally:
    input("support the arm, then press enter to disconnect")
    arm.disconnect()