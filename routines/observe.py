import json
import time

import cv2

from core.markers import measure

def teach_observe(arm, camera, detector, path="observe.json"):
    input("support the arm, then press enter to release torque")
    arm.torque_off()
    print("move the arm until both markers are in view")
    print("press 's' in the video window to save, 'q' to cancel")

    while True:
        frame = camera.read()
        if frame is None:
            continue

        markers = detector.detect(frame)
        detector.draw(frame, markers)
        cv2.imshow("teach observe", frame)

        key = cv2.waitKey(1)

        if key == ord("q"):
            arm.torque_on()
            cv2.destroyWindow("teach observe")
            print("cancelled")
            return False
        if key == ord("s"):
            break

    cv2.destroyWindow("teach observe")
    arm.torque_on()
    time.sleep(0.5)

    joints = arm.read()
    reference = measure(camera, detector)

    if len(reference) < 2:
        print("warning: only saw markers", list(reference.keys()))

    markers_out = {}
    for marker_id, values in reference.items():
        markers_out[str(marker_id)] = values

    data = {"joints": joints, "markers": markers_out}
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    print("saved to", path)
    return True

def check_observe(arm, camera, detector, path="observe.json", duration=2.0):
    with open(path) as f:
        data = json.load(f)

    arm.move_to(data["joints"], duration=duration)
    time.sleep(2)

    now = measure(camera, detector)

    errors = {}
    for id_text, ref in data["markers"].items():
        marker_id = int(id_text)

        if marker_id not in now:
            print ("marker", marker_id, "NOT VISIBLE")
            continue

        cur = now[marker_id]
        dx = cur["center"][0] - ref["center"][0]
        dy = cur["center"][1] - ref["center"][1]
        dsize = cur["size"] - ref["size"]
        dangle = (cur["angle"] - ref["angle"] + 180) % 360 - 180

        errors[marker_id] = {"dx": dx, "dy": dy, "dsize": dsize, "dangle": dangle}
        print("marker", marker_id,
              " dx", round(dx, 1), "px",
              " dy", round(dy, 1), "px",
              " dsize", round(dsize, 1), "px",
              " dangle", round(dangle, 2), "deg")


    return errors
