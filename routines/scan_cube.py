import time

from core.face_reader import read_face
from core.colors import classify
from core.scan import place_readings, orientation_after
from routines.rotations import rotate_cube


def scan_cube(arm, camera, poses, views, steps):
    # steps: SCAN_TOP_ONLY or SCAN_TOP_FRONT from core/scan.py
    # returns: kociemba state string, and the cube's orientation afterwards
    done = []
    readings = []

    for rotation, view_names in steps:
        if rotation is not None:
            rotate_cube(arm, poses, rotation)
            done.append(rotation)

        for view in view_names:
            arm.move_to(views[view]["pose"], duration=1.0)
            time.sleep(0.5)                  # let the arm settle before reading
            colors = read_face(camera, views[view]["corners"])
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