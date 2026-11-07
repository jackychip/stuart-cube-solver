import time

from core.face_reader import read_face
from core.colors import classify
from core.scan import place_readings, orientation_after
from routines.rotations import rotate_cube


def scan_cube(arm, camera, poses, views, steps, status=None):
    # steps: SCAN_TOP_ONLY or SCAN_TOP_FRONT from core/scan.py
    # status: optional Status, for the live display
    # returns: kociemba state string, and the cube's orientation afterwards
    done = []
    readings = []

    for rotation, view_names in steps:
        if rotation is not None:
            if status is not None:
                status.text = "scan: " + rotation
            rotate_cube(arm, poses, rotation)
            done.append(rotation)

        for view in view_names:
            if status is not None:
                status.text = "scan: reading " + view
            # arrive from hover, the same way step 6 taught the view
            arm.move_to(poses["hover"], duration=0.8)
            arm.move_to(views[view]["pose"], duration=1.0)
            time.sleep(0.5)                  # let the arm settle before reading

            if status is not None:
                status.corners = views[view]["corners"]
            colors = read_face(camera, views[view]["corners"])
            if status is not None:
                status.corners = None

            if colors is None:
                raise RuntimeError("camera returned no frames")
            readings.append((view, list(done), colors))
            print("read", view, "after rotations", done)

        if len(view_names) > 0:
            arm.move_to(poses["hover"], duration=0.8)

    stickers = place_readings(readings)
    for i in range(54):
        if stickers[i] is None:
            raise RuntimeError("sticker " + str(i) + " was never seen - check the scan steps")

    state = classify(stickers)
    return state, orientation_after(done)