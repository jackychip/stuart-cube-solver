import json
import os

BODY = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]
SQUEEZE = 5

ROTATION_HINTS = {
    "x'": "top face comes to the FRONT",
    "y":  "front face goes to the LEFT",
    "y'": "front face goes to the RIGHT",
}


def load_poses(path="poses.json"):
    # missing or empty file = no poses yet
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    with open(path) as f:
        return json.load(f)


def save_all(poses, path="poses.json"):
    temp_path = path + ".tmp"
    with open(temp_path, "w") as f:
        json.dump(poses, f, indent=2)
    os.replace(temp_path, path)     # swaps in the new file only after a successful write


def save_pose(name, values, path="poses.json"):
    poses = load_poses(path)
    poses[name] = values
    save_all(poses, path)
    print("saved", name, values)


def closed_value(poses, open_value, squeeze=SQUEEZE):
    # gripper target past the contact point, so the grip keeps pushing
    contact_value = poses["grip_closed"]["gripper"]
    if contact_value < open_value:
        return contact_value - squeeze
    return contact_value + squeeze


def biggest_joint_difference(a, b):
    biggest = 0
    for joint in BODY:
        difference = abs(a[joint] - b[joint])
        if difference > biggest:
            biggest = difference
    return biggest


def teach_pose(arm, name, path="poses.json"):
    input("support the arm, then press enter to release torque")
    arm.torque_off()
    input("move the arm to '" + name + "', then press enter to save")
    arm.torque_on()
    save_pose(name, arm.read(), path)


def teach_below_hover(arm, name, path="poses.json"):
    # a grasp pose must sit straight below hover, so approaches are a pure vertical drop
    poses = load_poses(path)
    arm.move_to(poses["hover"], duration=1.0)

    input("support the arm, then press enter to release torque")
    arm.torque_off()
    input("lower STRAIGHT DOWN to '" + name + "' (no sideways shift, no wrist roll), then press enter")
    arm.torque_on()
    pose = arm.read()

    for joint in ["shoulder_pan", "wrist_roll"]:
        difference = abs(pose[joint] - poses["hover"][joint])
        if difference > 3:
            print("warning:", joint, "moved", round(difference, 1),
                  "degrees from hover - this grasp isn't straight below it")

    save_pose(name, pose, path)
    arm.move_to(poses["hover"], duration=0.8)


def teach_grip_width(arm, path="poses.json"):
    # close the jaws by hand onto the cube; only the gripper value is used
    poses = load_poses(path)
    arm.move_to(poses["hover"], duration=1.0)
    arm.move_to(poses["turn_grasp"], duration=0.5)

    input("press enter to release the gripper only (arm keeps holding)")
    arm.torque_off(["gripper"])
    input("close the jaws by hand until they just touch the cube, then press enter")
    arm.torque_on(["gripper"])
    save_pose("grip_closed", arm.read(), path)

    arm.move_to({"gripper": poses["turn_grasp"]["gripper"]}, duration=0.3)
    arm.move_to(poses["hover"], duration=0.5)


def teach_turn(arm, direction, path="poses.json"):
    poses = load_poses(path)
    if direction == 1:
        s = "_pos"
    else:
        s = "_neg"

    open_value = poses["turn_grasp"]["gripper"]
    contact_value = poses["grip_closed"]["gripper"]

    # approach and grip, same as a real turn
    arm.move_to(poses["hover"], duration=1.0)
    arm.move_to(poses["turn_grasp"], duration=0.5)
    arm.move_to({"gripper": contact_value}, duration=0.5)

    # turned pose: arm limp, gripper still holding the layer
    input("support the arm, then press enter to release the arm joints (gripper keeps holding)")
    arm.torque_off(BODY)
    input("turn the top two layers 90 degrees by moving the arm, then press enter")
    arm.torque_on(BODY)
    turned = arm.read()
    save_pose("turned" + s, turned, path)

    # check the turn went the way this direction expects
    roll_change = turned["wrist_roll"] - poses["turn_grasp"]["wrist_roll"]
    if roll_change * direction < 0:
        print("warning: wrist_roll went the opposite way from direction", direction)

    # retreat pose: open, then slide off the fixed jaw
    arm.move_to({"gripper": open_value}, duration=0.3)
    input("support the arm, then press enter to release the arm joints")
    arm.torque_off(BODY)
    input("slide 2-4 mm away from the fixed jaw (don't lift), then press enter")
    arm.torque_on(BODY)
    save_pose("retreat" + s, arm.read(), path)

    # leave: straight up, unroll in the air
    poses = load_poses(path)
    lift = dict(poses["hover"])
    lift["wrist_roll"] = arm.read()["wrist_roll"]
    arm.move_to(lift, duration=0.5)
    arm.move_to(poses["hover"], duration=0.8)


def record_waypoints(arm, label, start_roll):
    # arm joints limp, gripper stays locked; press enter at each key point
    input("support the arm, then press enter to release the arm joints (gripper stays locked)")
    arm.torque_off(BODY)

    print(label)
    print("press enter at each key point. type 'd' + enter when done.")
    waypoints = []
    while True:
        text = input("  waypoint " + str(len(waypoints) + 1) + ": ").strip()
        if text == "d":
            if len(waypoints) == 0:
                print("  need at least one waypoint")
                continue
            break
        waypoints.append(arm.read())

    arm.torque_on(BODY)

    # check for the wrist wrapping past +-180 between points (it would spin the long way on replay)
    previous_roll = start_roll
    for i in range(len(waypoints)):
        jump = abs(waypoints[i]["wrist_roll"] - previous_roll)
        if jump > 180:
            print("warning: wrist_roll jumps", round(jump), "degrees at waypoint", i + 1,
                  "- it crossed the wrap point. re-teach this rotation.")
        previous_roll = waypoints[i]["wrist_roll"]

    return waypoints


def teach_rotation(arm, name, path="poses.json"):
    poses = load_poses(path)
    hover = poses["hover"]
    open_value = hover["gripper"]
    print("teaching rotation", name, "-", ROTATION_HINTS[name])

    arm.move_to(hover, duration=1.0)

    # approach: from hover down to the grasp, gripper open
    approach = record_waypoints(
        arm,
        "move from hover to the grasp, gripper open. roll the wrist UP HERE in the air first, "
        "then go straight down. the LAST point should be the jaws around the cube, ready to grip.",
        hover["wrist_roll"],
    )

    # grip, squeezing like a real rotation
    arm.move_to({"gripper": closed_value(poses, open_value)}, duration=0.5)

    # carry: lift, rotate, set back down, all while gripped
    carry = record_waypoints(
        arm,
        "lift the cube, rotate it, and set it back in the holder. "
        "the LAST point should be the cube fully seated, still gripped.",
        approach[-1]["wrist_roll"],
    )

    # release
    arm.move_to({"gripper": open_value}, duration=0.3)

    # exit: clear the cube, then end up near hover
    exit_path = record_waypoints(
        arm,
        "move clear of the cube. FIRST move away along the jaws' opening "
        "(straight up if gripping from the top) until the jaws clear the cube, "
        "THEN straighten the gripper and rise to about hover height above the cube. "
        "the LAST point should be close to hover.",
        carry[-1]["wrist_roll"],
    )

    # the code moves hover -> first approach point and last exit point -> hover on its own
    if biggest_joint_difference(approach[0], hover) > 20:
        print("warning: first approach point is far from hover."
              " add a waypoint closer to hover, or the first move may arc into the cube.")
    if biggest_joint_difference(exit_path[-1], hover) > 20:
        print("warning: last exit point is far from hover."
              " add a waypoint closer to hover, or the final move may arc into the cube.")

    poses = load_poses(path)
    if "rotations" not in poses:
        poses["rotations"] = {}
    poses["rotations"][name] = {
        "approach": approach,
        "carry": carry,
        "exit": exit_path,
    }
    save_all(poses, path)
    print("saved rotation", name, "-", len(approach), "approach,", len(carry), "carry,",
          len(exit_path), "exit points")

    arm.move_to(poses["hover"], duration=1.0)