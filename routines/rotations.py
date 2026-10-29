def rotate_cube(arm, poses, name, step_duration=0.5):
    rotation = poses["rotations"][name]
    gripper_value = rotation["pre"]["gripper"] 

    # approach
    arm.move_to(rotation["pre"], duration=1.0)

    # push the cube over, following the taught path
    for point in rotation["push"]:
        target = dict(point)
        target["gripper"] = gripper_value
        arm.move_to(target, duration=step_duration)

    # back off
    for point in rotation["exit"]:
        target = dict(point)
        target["gripper"] = gripper_value
        arm.move_to(target, duration=step_duration)