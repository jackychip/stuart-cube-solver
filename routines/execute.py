from routines.turns import turn_u
from routines.rotations import rotate_cube

# turn_u's direction=1 happens to produce u' on this arm
TURN_DIRECTION = {"u": -1, "u'": 1}

def run_actions(arm, poses, actions, status=None):
    for i in range(len(actions)):
        if status is not None and status.stop:
            print("stopped after", i, "actions")
            return

        action = actions[i]
        label = str(i + 1) + "/" + str(len(actions)) + " " + action
        print(label)
        if status is not None:
            status.text = label

        if action in TURN_DIRECTION:
            turn_u(arm, poses, direction=TURN_DIRECTION[action])
        else:
            rotate_cube(arm, poses, action)