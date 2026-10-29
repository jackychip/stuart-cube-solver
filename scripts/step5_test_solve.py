from config import ARM_PORT, ARM_ID
from core.arm import Arm
from core.solver import solve_for_arm, check_plan
from routines.teach import load_poses
from routines.execute import run_actions

SCRAMBLE = "F2 U' L2 D B2 R2 U' F2 D2 R2 U B' L F' U2 R' D' B R2 F"
STATE = "ULDUULBDDRBLRRDLDDUBBUFBFRFRFUBDRUFFBFLLLRFUDBURLBFLDR"

moves, actions = solve_for_arm(STATE)

print("kociemba:", " ".join(moves))
print("arm:     ", " ".join(actions))
print("plan correct:", check_plan(moves, actions))

arm = Arm(ARM_PORT, ARM_ID)

try:
    input("scramble with: " + SCRAMBLE + "\nput it in the holder in home orientation, then press enter")
    run_actions(arm, load_poses(), actions)
    print("done. the cube should be solved.")
finally:
    input("support the arm, then press enter to disconnect")
    arm.disconnect()