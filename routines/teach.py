import json
import os

BODY = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll"]


def save_pose(name, values, path="poses.json"):
    poses = {}
    if os.path.exists(path):
        with open(path) as f:
            poses = json.load(f)
    poses[name] = values
    with open(path, "w") as f:
        json.dump(poses, f, indent=2)
    print("saved", name, values)


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
    input("slide 45 degrees away from the fixed jaw (don't lift), then press enter")
    arm.torque_on(BODY)
    save_pose("retreat" + s, arm.read(), path)

    # leave: straight up, unroll in the air
    lift = dict(poses["pre_grasp"])
    lift["wrist_roll"] = arm.read()["wrist_roll"]
    arm.move_to(lift, duration=0.5)
    arm.move_to(poses["pre_grasp"], duration=0.8)

def teach_pose(arm, name, path="poses.json"):
    poses = {}
    if os.path.exists(path):
        with open(path) as f:
            poses = json.load(f)

    input("support the arm, then press enter to release torque")
    arm.torque_off()
    input("move the arm to '" + name + "', then press enter to save")
    arm.torque_on()

    poses[name] = arm.read()
    with open(path, "w") as f:
        json.dump(poses, f, indent=2)

    print("saved ", name, poses[name])

def load_poses(path="poses.json"):
    with open(path) as f:
        return json.load(f)