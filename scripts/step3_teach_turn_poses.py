from config import ARM_PORT, ARM_ID
from core.arm import Arm
from routines.teach import teach_pose, teach_turn

arm = Arm(ARM_PORT, ARM_ID)

try:
    teach_pose(arm, "pre_grasp")
    teach_pose(arm, "grasp")
    teach_pose(arm, "grasp_closed")
    teach_turn(arm, direction=1)
    teach_turn(arm, direction=-1)
finally:
    input("support the arm, then press enter to disconnect")
    arm.disconnect()