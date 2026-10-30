import json
import os

BODY = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]

ROTATION_HINTS = {
    "x":  "front face goes UP to the top",
    "x'": "front face goes DOWN to the bottom",
    "y":  "front face goes to the LEFT",
    "y'": "front face goes to the RIGHT",
    "z":  "top face goes to the RIGHT",
    "z'": "top face goes to the LEFT",
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

def teach_pose(arm, name, path="poses.json"):
    input("support the arm, then press enter to release torque")
    arm.torque_off()
    input("move the arm to '" + name + "', then press enter to save")
    arm.torque_on()
    save_pose(name, arm.read(), path)

def teach_turn(arm, direction, path="poses.json"):
    poses = load_poses(path)
    if direction == 1:
        s = "_pos"
    else:
        s = "_neg"

    open_value = poses["grasp"]["gripper"]
    contact_value = poses["grasp_closed"]["gripper"]

    # approach and grip, same as a real turn
    arm.move_to(poses["pre_grasp"], duration=1.0)
    arm.move_to(poses["grasp"], duration=0.5)
    arm.move_to({"gripper": contact_value}, duration=0.5)

    # turned pose: arm limp, gripper still holding the layer
    input("support the arm, then press enter to release the arm joints (gripper keeps holding)")
    arm.torque_off(BODY)
    input("turn the top layer 90 degrees by moving the arm, then press enter")
    arm.torque_on(BODY)
    turned = arm.read()
    save_pose("turned" + s, turned, path)

    # check the turn went the way this direction expects
    roll_change = turned["wrist_roll"] - poses["grasp"]["wrist_roll"]
    if roll_change * direction < 0:
        print("warning: wrist_roll went the opposite way from direction", direction)

    # retreat pose: open, then slide off the fixed jaw
    arm.move_to({"gripper": open_value}, duration=0.3)
    input("support the arm, then press enter to release the arm joints")
    arm.torque_off(BODY)
    input("slide 45 degrees (relative to shoulder_pan) away from the fixed jaw (don't lift), then press enter")
    arm.torque_on(BODY)
    save_pose("retreat" + s, arm.read(), path)

    # leave: straight up, unroll in the air
    lift = dict(poses["pre_grasp"])
    lift["wrist_roll"] = arm.read()["wrist_roll"]
    arm.move_to(lift, duration=0.5)
    arm.move_to(poses["pre_grasp"], duration=0.8)

def record_waypoints(arm, label, start_roll):
    # arm joints torque off, gripper locked, enter at each key point
    input("support the arm, then press enter to release the arm joints")
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

ROTATION_HINTS = {
    "x'": "top face comes to the FRONT",
    "y":  "front face goes to the LEFT",
    "y'": "front face goes to the RIGHT",
}


def teach_rotation(arm, name, path="poses.json"):
    poses = load_poses(path)
    contact_value = poses["grasp_closed"]["gripper"]
    print("teaching rotation", name, "-", ROTATION_HINTS[name])

    # pre-rotation pose: hovering above the cube, gripper open
    input("support the arm, then press enter to release torque")
    arm.torque_off()
    input("move to the PRE-ROTATION pose (hovering, gripper open), then press enter")
    arm.torque_on()
    pre = arm.read()

    # grasp pose: jaws around the cube, still open
    input("press enter to release torque")
    arm.torque_off()
    input("move down to the GRASP pose (jaws around the cube, still open), then press enter")
    arm.torque_on()
    grasp = arm.read()

    # close on the cube, squeezing past contact so the grip holds while carrying
    squeeze = 7
    open_value = grasp["gripper"]
    if contact_value < open_value:
        closed_value = contact_value - squeeze
    else:
        closed_value = contact_value + squeeze
    arm.move_to({"gripper": closed_value}, duration=0.5)

    # carry: lift, rotate, set back down, all while gripped
    carry = record_waypoints(
        arm,
        "lift the cube, rotate it, and set it back in the holder. "
        "the LAST point should be the cube fully seated, still gripped.",
        grasp["wrist_roll"],
    )

    # release
    arm.move_to({"gripper": grasp["gripper"]}, duration=0.3)

    # exit: move clear without disturbing the cube
    exit_path = record_waypoints(
        arm,
        "move the gripper up and away from the cube. the LAST point should be clear and safe.",
        carry[-1]["wrist_roll"],
    )

    poses = load_poses(path)
    if "rotations" not in poses:
        poses["rotations"] = {}
    poses["rotations"][name] = {
        "pre": pre,
        "grasp": grasp,
        "carry": carry,
        "exit": exit_path,
    }
    save_all(poses, path)
    print("saved rotation", name, "-", len(carry), "carry points,", len(exit_path), "exit points")