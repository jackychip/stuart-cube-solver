from routines.teach import BODY, load_poses, save_all, save_pose, biggest_joint_difference

ROTATION_HINTS = {
    "x'": "top face comes to the FRONT",
    "y":  "front face goes to the LEFT",
    "y'": "front face goes to the RIGHT",
}


def capture_pose(mirror, name, prompt, path="poses.json"):
    input(prompt + ", then press enter to save '" + name + "'")
    pose = mirror.capture()
    save_pose(name, pose, path)
    return pose


def capture_waypoints(mirror, label, start_roll):
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
        waypoints.append(mirror.capture())

    # check for the wrist wrapping past +-180 between points (it would spin the long way on replay)
    previous_roll = start_roll
    for i in range(len(waypoints)):
        jump = abs(waypoints[i]["wrist_roll"] - previous_roll)
        if jump > 180:
            print("warning: wrist_roll jumps", round(jump), "degrees at waypoint", i + 1,
                  "- it crossed the wrap point. re-teach this.")
        previous_roll = waypoints[i]["wrist_roll"]

    return waypoints


def teach_shared(mirror, path="poses.json"):
    hover = capture_pose(mirror, "hover",
        "put the follower straight above the holder center, gripper pointing down, "
        "jaws front/back and OPEN, tips ~8-10 mm above the cube", path)

    grasp = capture_pose(mirror, "turn_grasp",
        "lower STRAIGHT DOWN until the jaws surround the top two layers, still open", path)
    for joint in ["shoulder_pan", "wrist_roll"]:
        if abs(grasp[joint] - hover[joint]) > 3:
            print("warning:", joint, "moved from hover - this grasp isn't straight below it")

    capture_pose(mirror, "grip_closed",
        "close the leader's gripper until the follower grips the cube FIRMLY "
        "(a little past touching - this is the squeeze)", path)

    input("open the gripper and go back up to hover, then press enter")


def teach_turn(mirror, direction, path="poses.json"):
    if direction == 1:
        s = "_pos"
    else:
        s = "_neg"
    poses = load_poses(path)

    input("go to turn_grasp and grip firmly (like grip_closed), then press enter")

    turned = capture_pose(mirror, "turned" + s,
        "turn the top two layers 90 degrees, still gripping", path)
    roll_change = turned["wrist_roll"] - poses["turn_grasp"]["wrist_roll"]
    if roll_change * direction < 0:
        print("warning: wrist_roll went the opposite way from direction", direction)

    capture_pose(mirror, "retreat" + s,
        "open the gripper, then slide 2-4 mm away from the fixed jaw (don't lift)", path)

    input("lift straight up, unroll the wrist in the air, back to hover, then press enter")


def teach_rotation(mirror, name, path="poses.json"):
    poses = load_poses(path)
    hover = poses["hover"]
    print("teaching rotation", name, "-", ROTATION_HINTS[name])
    input("start at hover, then press enter")

    approach = capture_waypoints(mirror,
        "move from hover to the grasp, gripper OPEN. roll the wrist up here in the air first, "
        "then go straight down. the LAST point: jaws around the cube, ready to grip.",
        hover["wrist_roll"])

    input("close the leader's gripper so the follower grips the cube firmly, then press enter")
    grip = mirror.capture()["gripper"]

    carry = capture_waypoints(mirror,
        "lift the cube, rotate it, and set it back in the holder, keeping the grip. "
        "the LAST point: cube fully seated, still gripped.",
        approach[-1]["wrist_roll"])

    input("open the gripper to release the cube, then press enter")

    exit_path = capture_waypoints(mirror,
        "move clear of the cube. FIRST move away along the jaws' opening until the jaws clear it, "
        "THEN straighten the gripper and rise to about hover height. the LAST point: close to hover.",
        carry[-1]["wrist_roll"])

    if biggest_joint_difference(approach[0], hover) > 20:
        print("warning: first approach point is far from hover - add a waypoint closer to it")
    if biggest_joint_difference(exit_path[-1], hover) > 20:
        print("warning: last exit point is far from hover - add a waypoint closer to it")

    poses = load_poses(path)
    if "rotations" not in poses:
        poses["rotations"] = {}
    poses["rotations"][name] = {
        "approach": approach,
        "grip": grip,
        "carry": carry,
        "exit": exit_path,
    }
    save_all(poses, path)
    print("saved rotation", name, "-", len(approach), "approach,", len(carry), "carry,",
          len(exit_path), "exit points")

    input("go back to hover, then press enter")