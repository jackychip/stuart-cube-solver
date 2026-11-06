import kociemba

SOLVED = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
POSITIONS = ["U", "D", "F", "B", "L", "R"]

# Whole-cube rotations (standard notation: x like R, y like U, z like F).
# Read as: after the rotation, POSITION gets the face that was at VALUE.
#   e.g. x: the face at F moves to U, so new U = old F
BASE_ROTATIONS = {
    "x": {"U": "F", "F": "D", "D": "B", "B": "U", "L": "L", "R": "R"},
    "y": {"F": "R", "R": "B", "B": "L", "L": "F", "U": "U", "D": "D"},
    "z": {"U": "L", "L": "D", "D": "R", "R": "U", "F": "F", "B": "B"},
}


def inverse(rotation):
    result = {}
    for position, source in rotation.items():
        result[source] = position
    return result


# build x, x', y, y', z, z'
ROTATIONS = {}
for name, rotation in BASE_ROTATIONS.items():
    ROTATIONS[name] = rotation
    ROTATIONS[name + "'"] = inverse(rotation)

# the rotations the robot can do
ROBOT_ROTATIONS = ["x'", "y", "y'"]


class Orientation:
    # which face (named by its center at the start) sits at each position

    def __init__(self):
        self.at = {}
        for position in POSITIONS:
            self.at[position] = position     # start: every face in its home position

    def rotate(self, name):
        source = ROTATIONS[name]
        new_at = {}
        for position in POSITIONS:
            new_at[position] = self.at[source[position]]
        self.at = new_at

    def copy(self):
        other = Orientation()
        other.at = dict(self.at)
        return other


def solve(state):
    # state: 54-character kociemba string, faces in order U R F D L B
    if state == SOLVED:
        return []
    solution = kociemba.solve(state)        # raises ValueError if the state is impossible
    return solution.split()                 # "R U' F2" -> ["R", "U'", "F2"]


def rotations_to_bottom(orientation, face):
    # shortest list of robot rotations that puts `face` on the bottom
    if orientation.at["D"] == face:
        return []

    queue = [(orientation, [])]
    for depth in range(3):
        next_queue = []
        for current, path in queue:
            for name in ROBOT_ROTATIONS:
                trial = current.copy()
                trial.rotate(name)
                new_path = path + [name]
                if trial.at["D"] == face:
                    return new_path
                next_queue.append((trial, new_path))
        queue = next_queue

    raise RuntimeError("can't bring " + face + " to the bottom")


# arm turns for each kind of move (face X must already be on the bottom)
TURNS_FOR = {"": ["u"], "'": ["u'"], "2": ["u", "u"]}

# what each arm turn does to the orientation (the top two layers' centers move)
#   u  = D  + y   (bottom face turns clockwise, cube rotates y)
#   u' = D' + y'  (bottom face turns prime, cube rotates y')
ORIENTATION_CHANGE = {"u": "y", "u'": "y'"}


def plan(moves, start=None):
    # turn kociemba moves into arm actions: rotations + "u" / "u'"
    # start: the cube's orientation when the solve begins (None = home)
    if start is None:
        orientation = Orientation()
    else:
        orientation = start.copy()
    actions = []

    for move in moves:
        face = move[0]          # "R'" -> "R"
        suffix = move[1:]       # "R'" -> "'"

        # put the face to turn on the bottom (the layer the holder keeps still)
        for name in rotations_to_bottom(orientation, face):
            orientation.rotate(name)
            actions.append(name)

        for turn in TURNS_FOR[suffix]:
            actions.append(turn)
            orientation.rotate(ORIENTATION_CHANGE[turn])

    return actions


def check_plan(moves, actions, start=None):
    # replay the arm actions and confirm they perform the same face moves
    if start is None:
        orientation = Orientation()
    else:
        orientation = start.copy()
    replayed = []
    for action in actions:
        if action in ORIENTATION_CHANGE:
            bottom = orientation.at["D"]
            if action == "u":
                replayed.append(bottom)          # u  = bottom face clockwise
            else:
                replayed.append(bottom + "'")    # u' = bottom face prime
            orientation.rotate(ORIENTATION_CHANGE[action])
        else:
            orientation.rotate(action)

    expected = []
    for move in moves:
        if move.endswith("2"):
            expected.append(move[0])
            expected.append(move[0])
        else:
            expected.append(move)

    return replayed == expected


def solve_for_arm(state, start=None):
    moves = solve(state)
    actions = plan(moves, start)
    return moves, actions