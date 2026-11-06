import math

FACES = ["U", "R", "F", "D", "L", "B"]       # kociemba's face order
CENTERS = [4, 13, 22, 31, 40, 49]           # index of each face's center sticker


def distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def classify(stickers):
    # stickers: 54 Lab colors in kociemba order
    # each sticker gets the label of the center whose color it's closest to
    labels = ""
    for color in stickers:
        best_face = None
        best_dist = float("inf")
        for k in range(6):
            d = distance(color, stickers[CENTERS[k]])
            if d < best_dist:
                best_dist = d
                best_face = FACES[k]
        labels += best_face

    # a real cube has exactly 9 of each
    problems = []
    for face in FACES:
        count = labels.count(face)
        if count != 9:
            problems.append(face + " x" + str(count))
    if len(problems) > 0:
        raise ValueError("color counts are off (" + ", ".join(problems) + "): " + labels)

    return labels


# rough OpenCV Lab values for standard cube colors, for debugging single faces only.
# tune these to your lighting: point the camera at each color and copy the printed values in.
REFERENCE = {
    "WHITE":  [235, 128, 128],
    "YELLOW": [225, 115, 200],
    "RED":    [130, 185, 165],
    "ORANGE": [170, 160, 185],
    "GREEN":  [160,  75, 165],
    "BLUE":   [100, 135,  75],
}


def nearest_reference(color):
    best_name = None
    best_dist = float("inf")
    for name, reference in REFERENCE.items():
        d = distance(color, reference)
        if d < best_dist:
            best_dist = d
            best_name = name
    return best_name, best_dist