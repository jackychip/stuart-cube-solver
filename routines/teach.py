import json
import os

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