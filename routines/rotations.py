def rotate_cube(arm, poses, name, squeeze=7, step_duration=0.8):
    rotation = poses["rotations"][name]

    open_value = rotation["grasp"]["gripper"]
    contact_value = poses["grasp_closed"]["gripper"]
    if contact_value < open_value:
        closed_value = contact_value - squeeze
    else:
        closed_value = contact_value + squeeze

    # approach
    arm.move_to(rotation["pre"], duration=1.0)
    arm.move_to(rotation["grasp"], duration=0.5)

    # grip
    arm.move_to({"gripper": closed_value}, duration=0.5)

    # lift, rotate, set down (gripper left out, so it keeps squeezing)
    carry = []
    for point in rotation["carry"]:
        target = dict(point)
        del target["gripper"]
        carry.append(target)
    arm.move_through(carry, duration=step_duration * len(carry))

    # release
    arm.move_to({"gripper": open_value}, duration=0.3)

    # move clear (gripper left out, it's already open)
    exit_points = []
    for point in rotation["exit"]:
        target = dict(point)
        del target["gripper"]
        exit_points.append(target)
    arm.move_through(exit_points, duration=step_duration * len(exit_points))