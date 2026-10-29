from routines.turns import turn_u
from routines.rotations import rotate_cube

# turn_u's direction=1 happens to produce u' on this arm
TURN_DIRECTION = {"u": -1, "u'": 1}

def run_actions(arm, poses, actions):
    for i in range(len(actions)):
        action = actions[i]
        print(i + 1, "/", len(actions), action)

        if action in TURN_DIRECTION:
            turn_u(arm, poses, direction=TURN_DIRECTION[action])
        else:
            rotate_cube(arm, poses, action)