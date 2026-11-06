import time

from config import ARM_PORT, ARM_ID, CAMERA_NAME, LEADER_PORT, LEADER_ID
from core.arm import Arm
from core.camera import Camera
from core.leader import Leader, Mirror
from core.face_reader import click_corners, load_views, save_views, preview
from routines.teach import load_poses

VIEW = "top"        # "top" or "front"

arm = Arm(ARM_PORT, ARM_ID)
cam = Camera(CAMERA_NAME)
leader = Leader(LEADER_PORT, LEADER_ID)
mirror = Mirror(arm, leader)

try:
    input("hold the leader roughly in the follower's pose, then press enter to start mirroring")
    mirror.start()
    if not preview(cam, "position " + VIEW, "move so the camera sees the " + VIEW + " face clearly"):
        raise SystemExit
    pose = mirror.capture()
    mirror.stop()

    # re-arrive the way the scan will (from hover), so the clicks match what scanning sees
    poses = load_poses()
    arm.move_to(poses["hover"], duration=1.0)
    arm.move_to(pose, duration=1.0)
    time.sleep(0.5)                          # let it settle before clicking

    corners = click_corners(cam, VIEW)
    if corners is not None:
        views = load_views()
        views[VIEW] = {"pose": pose, "corners": corners}
        save_views(views)
        print("saved view", VIEW)
finally:
    mirror.stop()
    cam.close()
    leader.disconnect()
    input("support the arm, then press enter to disconnect")
    arm.disconnect()