from config import ARM_PORT, ARM_ID
from core.arm import Arm
from routines.wiggle import wiggle

arm = Arm(ARM_PORT, ARM_ID)

try:
    wiggle(arm)
finally:
    input("support the arm, then press enter to disconnect")
    arm.disconnect()