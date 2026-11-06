# Where each scanned sticker belongs in the kociemba state.
#
# The camera reads a face at a fixed PHYSICAL position (top or front). Which LOGICAL sticker
# that is depends on how the cube has been rotated since the scan started. We undo those
# rotations on the sticker's 3D position to find its home-orientation slot.

from core.cube_model import FACES, INDEX, NORMALS, sticker_position, turn_clockwise
from core.solver import Orientation

# rotation axes, same convention as the planner: x like R, y like U, z like F
AXES = {"x": NORMALS["R"], "y": NORMALS["U"], "z": NORMALS["F"]}

# the camera views, and which physical face each one sees
VIEW_FACE = {"top": "U", "front": "F"}

# scan sequences: (rotation before reading, views to read after it)
# top camera view only: 7 rotations
SCAN_TOP_ONLY = [
    (None, ["top"]),
    ("x'", ["top"]),
    ("x'", ["top"]),
    ("x'", ["top"]),
    ("y",  []),
    ("x'", ["top"]),
    ("x'", []),
    ("x'", ["top"]),
]
# top + front camera views: 4 rotations
SCAN_TOP_FRONT = [
    (None, ["top", "front"]),
    ("x'", ["top"]),
    ("x'", ["top"]),
    ("y",  ["front"]),
    ("x'", ["top"]),
]


def undo_rotation(v, name):
    # inverse of a rotation: a clockwise rotation is undone by three more clockwise ones
    axis = AXES[name[0]]
    if name.endswith("'"):
        times = 1
    else:
        times = 3
    for i in range(times):
        v = turn_clockwise(v, axis)
    return v


def logical_index(view, row, col, rotations_done):
    # kociemba index of the sticker the camera sees at (row, col) of this view
    face = VIEW_FACE[view]
    position = sticker_position(face, row, col)
    normal = NORMALS[face]
    for name in reversed(rotations_done):
        position = undo_rotation(position, name)
        normal = undo_rotation(normal, name)
    return INDEX[(position, normal)]


def place_readings(readings):
    # readings: list of (view, rotations_done, 9 colors in row-major order)
    # returns: 54 colors in kociemba order (None where a sticker was never read)
    stickers = [None] * 54
    for view, rotations_done, colors in readings:
        for row in range(3):
            for col in range(3):
                stickers[logical_index(view, row, col, rotations_done)] = colors[row * 3 + col]
    return stickers


def orientation_after(rotations_done):
    # the cube's orientation after the scan, so the solve can start from there
    orientation = Orientation()
    for name in rotations_done:
        orientation.rotate(name)
    return orientation