import threading
import time

import cv2

from config import ARM_PORT, ARM_ID, CAMERA_NAME
from core.arm import Arm
from core.camera import Camera
from core.face_reader import load_views, draw_face
from core.scan import SCAN_TOP_ONLY, SCAN_TOP_FRONT
from core.solver import solve_for_arm, check_plan
from core.status import Status
from routines.teach import load_poses
from routines.scan_cube import scan_cube
from routines.execute import run_actions

STEPS = SCAN_TOP_ONLY       # or SCAN_TOP_FRONT once the front view is taught

arm = Arm(ARM_PORT, ARM_ID)
cam = Camera(CAMERA_NAME)
status = Status()


def work():
    # everything that moves the arm runs here, so the main thread can show video
    try:
        poses = load_poses()
        views = load_views()

        if not status.wait_for_enter("put the cube in the holder, enter = scan"):
            return
        arm.move_to(poses["hover"], duration=1.0)

        try:
            state, start = scan_cube(arm, cam, poses, views, STEPS, status)
            moves, actions = solve_for_arm(state, start)
        except ValueError as error:
            print("scan didn't produce a valid cube - check lighting and the views, then rescan")
            print(error)
            return

        print("state:   ", state)
        print("kociemba:", " ".join(moves))
        print("arm:     ", " ".join(actions))
        print("plan correct:", check_plan(moves, actions, start))

        if not status.wait_for_enter(str(len(actions)) + " actions, enter = solve"):
            return
        run_actions(arm, poses, actions, status)
        print("done")
    finally:
        status.done = True


def draw_text(frame, text):
    # black outline under yellow text, readable on any background
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
    cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)


worker = threading.Thread(target=work)
try:
    worker.start()
    print("keys go in the video window: enter = continue, 'q' = stop after the current action")

    # macOS only allows windows on the main thread, so the display loop lives here
    while not status.done:
        frame = cam.read()
        if frame is None:
            time.sleep(0.01)
            continue
        if status.corners is not None:
            draw_face(frame, status.corners)
        draw_text(frame, status.text)
        cv2.imshow("stuart", frame)

        key = cv2.waitKey(1)
        if key == 13:                       # enter
            status.enter.set()
        if key == ord("q") and not status.stop:
            status.stop = True
            status.text = "stopping after this action..."

    worker.join()
finally:
    cam.close()
    cv2.destroyAllWindows()
    input("support the arm, then press enter to disconnect")
    arm.disconnect()