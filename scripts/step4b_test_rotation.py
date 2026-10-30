from config import ARM_PORT, ARM_ID
from core.arm import Arm
from routines.teach import load_poses
from routines.rotations import rotate_cube

ROTATION = "y'"          # which rotation to test

arm = Arm(ARM_PORT, ARM_ID)

try:
    poses = load_poses()
    rotate_cube(arm, poses, ROTATION)
finally:
    input("support the arm, then press enter to disconnect")
    arm.disconnect()