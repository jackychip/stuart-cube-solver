from config import ARM_PORT, ARM_ID, CAMERA_NAME
from core.arm import Arm
from core.camera import Camera
from core.face_reader import load_views
from core.scan import SCAN_TOP_ONLY, SCAN_TOP_FRONT
from core.solver import solve_for_arm, check_plan
from routines.teach import load_poses
from routines.scan_cube import scan_cube
from routines.execute import run_actions

STEPS = SCAN_TOP_ONLY       # or SCAN_TOP_FRONT once the front view is taught

arm = Arm(ARM_PORT, ARM_ID)
cam = Camera(CAMERA_NAME)

try:
    poses = load_poses()
    views = load_views()

    input("put the scrambled cube in the holder, then press enter to scan")
    arm.move_to(poses["hover"], duration=1.0)

    try:
        state, start = scan_cube(arm, cam, poses, views, STEPS)
        moves, actions = solve_for_arm(state, start)
    except ValueError as error:
        print("scan didn't produce a valid cube - check lighting and the views, then rescan")
        print(error)
        raise SystemExit

    print("state:   ", state)
    print("kociemba:", " ".join(moves))
    print("arm:     ", " ".join(actions))
    print("plan correct:", check_plan(moves, actions, start))

    input(str(len(actions)) + " actions - press enter to solve")
    run_actions(arm, poses, actions)
    print("done")
finally:
    cam.close()
    input("support the arm, then press enter to disconnect")
    arm.disconnect()