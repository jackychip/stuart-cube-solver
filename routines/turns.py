def turn_u(arm, poses, direction=1, angle=90, overdrive=5, squeeze=5):
    open_value = poses["grasp"]["gripper"]
    contact_value = poses["grasp_closed"]["gripper"]

    if contact_value < open_value:
        closed_value = contact_value - squeeze
    else:
        closed_value = contact_value + squeeze

    # approach
    arm.move_to(poses["pre_grasp"], duration=1.0)
    arm.move_to(poses["grasp"], duration=0.3)

    # grip
    arm.move_to({"gripper": closed_value}, duration=0.5)

    # twist, then back off
    roll_start = arm.read()["wrist_roll"]
    arm.move_to({"wrist_roll": roll_start + direction * (angle + overdrive)}, duration=2.0)
    arm.move_to({"wrist_roll": roll_start + direction * angle}, duration=0.2)

    # release
    arm.move_to({"gripper": open_value}, duration=0.3)

    # back up (slide away from fixed gripper)
    if direction == 1:
        retreat = dict(poses["retreat_pos"])
    else:
        retreat = dict(poses["retreat_neg"])

    retreat["wrist_roll"] = arm.read()["wrist_roll"] 
    retreat["gripper"] = open_value
    arm.move_to(retreat, duration=0.5)

    # lift up, maintain wrist
    lift = dict(poses["pre_grasp"])
    lift["wrist_roll"] = arm.read()["wrist_roll"]
    arm.move_to(lift, duration=0.5)

    # unroll in air
    arm.move_to({"wrist_roll": poses["pre_grasp"]["wrist_roll"]}, duration=0.5)