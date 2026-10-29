from config import ARM_PORT, ARM_ID
from core.arm import Arm
from routines.teach import teach_pose, teach_turn, teach_rotation, load_poses
from routines.rotations import rotate_cube

arm = Arm(ARM_PORT, ARM_ID)

TEACH_TURNS = False
TEACH_ROT = True
ROTATION = "x"
TEACH_ROTATIONS = ["x", "x'", "z", "z'"]

try:
    if TEACH_TURNS:
        teach_pose(arm, "pre_grasp")
        teach_pose(arm, "grasp")
        teach_pose(arm, "grasp_closed")
        teach_turn(arm, direction=1)
        teach_turn(arm, direction=-1)

    if TEACH_ROT:
        teach_rotation(arm, ROTATION)

finally:
    input("support the arm, then press enter to disconnect")
    arm.disconnect()