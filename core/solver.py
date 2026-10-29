import kociemba

SOLVED = "UUUUUUUUURRRRRRRRRFFFFFFFFFDDDDDDDDDLLLLLLLLLBBBBBBBBB"
POSITIONS = ["U", "D", "F", "B", "L", "R"]

# x,y,z are whole cube rotations
# after rotation, the face moves to a new value
# ex. after rotating x the face at F turns into U
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

# the rotations the robot can do (a 180 is planned as two 90s, e.g. "x x")
ROBOT_ROTATIONS = ["x", "x'", "z", "z'"]

class Orientation:
    # which face sits at each position (denoted by center on each face)

    def __init__(self):
        self.at = {}
        for position in POSITIONS:
            self.at[position] = position

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
    # state = 54-character kociemba string with faces in order of U R F D L B
    if state == SOLVED:
        return []

    solution = kociemba.solve(state)
    return solution.split() # return string into array

def rotations_to_bottom(orientation, face):
    # shortest list of rotations that puts face at the bottom for wide U turn
    # specific to this use case
    # we actually use BFS??

    if orientation.at["D"] == face:
        return []

    queue = [(orientation, [])]
    for depth in range(3):
        next_queue = []
        for current, path in queue:
            for name in ROBOT_ROTATIONS:
                temp = current.copy()
                temp.rotate(name)
                new_path = path + [name]
                if temp.at["D"] == face:
                    return new_path
                next_queue.append((temp, new_path))

        queue = next_queue

    raise RuntimeError("can't bring " + face + " to the bottom")

# arm turns for each kind of move (face must already be on the bottom)
TURNS_FOR = {"": ["u"], "'": ["u'"], "2": ["u", "u"]}

# what each arm turn does to the orientation (the top two layers' centers move)
#   u  = D  + y   (bottom face turns clockwise, cube rotates y)
#   u' = D' + y'  (bottom face turns prime, cube rotates y')
ORIENTATION_CHANGE = {"u": "y", "u'": "y'"}

def plan(moves):
    # turn kociemba moves into arm actions (rotations + u or u')
    orientation = Orientation()
    actions = []

    for move in moves:
        face = move[0]
        suffix = move[1:]

        # put face to turn to bottom
        for name in rotations_to_bottom(orientation, face):
            orientation.rotate(name)
            actions.append(name)

        for turn in TURNS_FOR[suffix]:
            actions.append(turn)
            orientation.rotate(ORIENTATION_CHANGE[turn])

    return actions

def check_plan(moves, actions):
    # replay actions and confirm they perform the same moves
    orientation = Orientation()
    replayed = []
    for action in actions:
        if action in ORIENTATION_CHANGE:
            bottom = orientation.at["D"]
            if action == "u":
                replayed.append(bottom)         # u
            else:
                replayed.append(bottom + "'")   # u'
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

def solve_for_arm(state):
    moves = solve(state)
    actions = plan(moves)
    return moves, actions