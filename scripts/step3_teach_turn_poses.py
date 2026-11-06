from config import ARM_PORT, ARM_ID, LEADER_PORT, LEADER_ID
from core.arm import Arm
from core.leader import Leader, Mirror
from routines.teach_leader import teach_shared, teach_turn, teach_rotation

TEACH_SHARED = False         # hover, turn_grasp, grip_closed
TEACH_TURNS = False         # turned + retreat, both directions
TEACH_ROT = True
ROTATION = "y'"             # one of: "x'", "y", "y'"

arm = Arm(ARM_PORT, ARM_ID)
leader = Leader(LEADER_PORT, LEADER_ID)
mirror = Mirror(arm, leader)

try:
    input("hold the leader roughly in the follower's pose, then press enter to start mirroring")
    mirror.start()

    if TEACH_SHARED:
        teach_shared(mirror)

    if TEACH_TURNS:
        teach_turn(mirror, direction=1)
        teach_turn(mirror, direction=-1)

    if TEACH_ROT:
        teach_rotation(mirror, ROTATION)

finally:
    mirror.stop()
    leader.disconnect()
    input("support the follower, then press enter to disconnect")
    arm.disconnect()