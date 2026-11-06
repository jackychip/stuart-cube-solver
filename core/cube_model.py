# A simple facelet model of a 3x3 cube, using kociemba's sticker order:
#   54 stickers, faces in order U R F D L B, each face read left-to-right,
#   top-to-bottom as seen from outside the cube
#   (U with B at the top, D with F at the top, the side faces with U at the top).
#
# Coordinates: x = toward R, y = toward U, z = toward F.

FACES = ["U", "R", "F", "D", "L", "B"]

# for each face: its outward direction
NORMALS = {
    "U": (0, 1, 0), "R": (1, 0, 0), "F": (0, 0, 1),
    "D": (0, -1, 0), "L": (-1, 0, 0), "B": (0, 0, -1),
}


def sticker_position(face, row, col):
    # where sticker (row, col) of a face sits in 3D
    if face == "U":
        return (-1 + col, 1, -1 + row)
    if face == "R":
        return (1, 1 - row, 1 - col)
    if face == "F":
        return (-1 + col, 1 - row, 1)
    if face == "D":
        return (-1 + col, -1, 1 - row)
    if face == "L":
        return (-1, 1 - row, -1 + col)
    if face == "B":
        return (1 - col, 1 - row, -1)


# index of every sticker, looked up by (position, normal)
STICKERS = []
INDEX = {}
for face in FACES:
    for row in range(3):
        for col in range(3):
            key = (sticker_position(face, row, col), NORMALS[face])
            INDEX[key] = len(STICKERS)
            STICKERS.append(key)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def turn_clockwise(v, axis):
    # rotate v by 90 degrees clockwise, as seen looking at the face from outside
    c = cross(axis, v)
    d = dot(axis, v)
    return (-c[0] + axis[0] * d, -c[1] + axis[1] * d, -c[2] + axis[2] * d)


def solved_state():
    state = []
    for face in FACES:
        for i in range(9):
            state.append(face)
    return state


def apply_quarter(state, face):
    axis = NORMALS[face]
    new_state = list(state)
    for i in range(54):
        position, normal = STICKERS[i]
        if dot(position, axis) == 1:      # sticker is in the turning layer
            new_key = (turn_clockwise(position, axis), turn_clockwise(normal, axis))
            new_state[INDEX[new_key]] = state[i]
    return new_state


def apply_moves(state, moves):
    # moves: list like ["R", "U'", "F2"]
    for move in moves:
        face = move[0]
        suffix = move[1:]
        if suffix == "":
            turns = 1
        elif suffix == "2":
            turns = 2
        else:
            turns = 3
        for i in range(turns):
            state = apply_quarter(state, face)
    return state


def scramble_to_state(scramble):
    # scramble: "R U F'" applied to a solved cube -> 54-character kociemba string
    state = apply_moves(solved_state(), scramble.split())
    return "".join(state)