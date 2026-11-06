import cv2

from config import ARM_PORT, ARM_ID, CAMERA_NAME
from core.arm import Arm
from core.camera import Camera
from core.colors import nearest_reference
from core.face_reader import load_views, draw_face, read_face
from routines.teach import load_poses

VIEW = "top"        # "top" or "front"

arm = Arm(ARM_PORT, ARM_ID)
cam = Camera(CAMERA_NAME)

try:
    poses = load_poses()
    view = load_views()[VIEW]
    arm.move_to(poses["hover"], duration=1.0)
    arm.move_to(view["pose"], duration=1.0)

    print("'p' = print sticker colors, 'q' = quit")
    while True:
        frame = cam.read()
        if frame is None:
            continue
        draw_face(frame, view["corners"])
        cv2.imshow("view " + VIEW, frame)

        key = cv2.waitKey(1)
        if key == ord("q"):
            break
        if key == ord("p"):
            colors = read_face(cam, view["corners"])
            for i in range(9):
                name, dist = nearest_reference(colors[i])
                print(i, name.ljust(7), [round(v) for v in colors[i]], " distance", round(dist))

    arm.move_to(poses["hover"], duration=1.0)
finally:
    cam.close()
    cv2.destroyAllWindows()
    input("support the arm, then press enter to disconnect")
    arm.disconnect()