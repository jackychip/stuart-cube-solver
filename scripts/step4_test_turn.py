from config import ARM_PORT, ARM_ID
from core.arm import Arm
from routines.teach import load_poses
from routines.turns import turn_u

arm = Arm(ARM_PORT, ARM_ID)

try:
    poses = load_poses()
    turn_u(arm, poses, direction=1)
    turn_u(arm, poses, direction=-1)
finally:
    input("support the arm, then press enter to disconnect")
    arm.disconnect()