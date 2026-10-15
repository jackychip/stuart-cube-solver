BODY = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]

def turn_u(arm, poses, direction=1, overdrive=5, squeeze=5, twist_duration=1.0):
    if direction == 1:
        s = "_pos"
    else:
        s = "_neg"
    turned = poses["turned" + s]

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

    # twist: every joint moves from grasp to the taught turned pose together,
    # with overdrive added to the wrist only
    twist = {}
    for joint in BODY:
        twist[joint] = turned[joint]
    twist["wrist_roll"] = turned["wrist_roll"] + direction * overdrive

    if twist["wrist_roll"] > 170 or twist["wrist_roll"] < -170:
        raise RuntimeError("wrist_roll would go to " + str(round(twist["wrist_roll"])))

    arm.move_to(twist, duration=twist_duration)

    # back off the overdrive
    arm.move_to({"wrist_roll": turned["wrist_roll"]}, duration=0.3)

    # release
    arm.move_to({"gripper": open_value}, duration=0.3)

    # back up (slide away from fixed gripper)
    retreat = dict(poses["retreat" + s])
    retreat["wrist_roll"] = arm.read()["wrist_roll"]
    retreat["gripper"] = open_value
    arm.move_to(retreat, duration=0.5)

    # lift up, maintain wrist
    lift = dict(poses["pre_grasp"])
    lift["wrist_roll"] = arm.read()["wrist_roll"]
    arm.move_to(lift, duration=0.5)

    # unroll in air
    arm.move_to({"wrist_roll": poses["pre_grasp"]["wrist_roll"]}, duration=0.5)