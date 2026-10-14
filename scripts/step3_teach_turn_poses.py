from config import ARM_PORT, ARM_ID
from core.arm import Arm
from routines.teach import teach_pose

arm = Arm(ARM_PORT, ARM_ID)

try:
    teach_pose(arm, "pre_grasp")
    teach_pose(arm, "grasp")
    teach_pose(arm, "grasp_closed")

    teach_pose(arm, "retreat_pos")
    teach_pose(arm, "retreat_neg")
finally:
    input("support the arm, then press enter to disconnect")
    arm.disconnect()