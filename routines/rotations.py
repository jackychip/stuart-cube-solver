from routines.teach import closed_value


def follow(arm, points, step_duration):
    # one smooth move through taught waypoints, leaving the gripper wherever it already is
    targets = []
    for point in points:
        target = dict(point)
        del target["gripper"]
        targets.append(target)
    arm.move_through(targets, duration=step_duration * len(targets))


def rotate_cube(arm, poses, name, squeeze=5, step_duration=0.8):
    rotation = poses["rotations"][name]
    open_value = poses["hover"]["gripper"]
    closed = rotation["grip"]

    # start at the shared hover pose
    arm.move_to(poses["hover"], duration=1.0)

    # approach the cube, gripper open
    follow(arm, rotation["approach"], step_duration)

    # grip
    arm.move_to({"gripper": closed}, duration=0.5)

    # lift, rotate, set down (gripper keeps squeezing)
    follow(arm, rotation["carry"], step_duration)

    # release
    arm.move_to({"gripper": open_value}, duration=0.3)

    # move clear
    follow(arm, rotation["exit"], step_duration)

    # finish at the shared hover pose
    arm.move_to(poses["hover"], duration=0.8)