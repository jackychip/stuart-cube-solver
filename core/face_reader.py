import json
import os

import cv2
import numpy as np

# 3x3 sticker centers in "face units", where the face spans 0..3 in both directions
STICKER_POINTS = []
for row in range(3):
    for col in range(3):
        STICKER_POINTS.append([col + 0.5, row + 0.5])

FACE_SQUARE = [[0, 0], [3, 0], [3, 3], [0, 3]]

# 4 sample points per sticker, one in each quadrant, so a logo in the middle is skipped.
# 0.28 = how far from the sticker's center, in sticker widths (stays inside the sticker)
SAMPLE_OFFSET = 0.28
SAMPLE_POINTS = []           # 36 points: sticker 0's four, then sticker 1's four, ...
for row in range(3):
    for col in range(3):
        for dy in [-SAMPLE_OFFSET, SAMPLE_OFFSET]:
            for dx in [-SAMPLE_OFFSET, SAMPLE_OFFSET]:
                SAMPLE_POINTS.append([col + 0.5 + dx, row + 0.5 + dy])

# which PHYSICAL corner to click, in order, for each view.
# this order is what makes the 9 stickers line up with kociemba's layout.
#   "left" = the robot's left, "front" = the side facing the robot base
CLICK_ORDER = {
    "top":   ["back-left", "back-right", "front-right", "front-left"],
    "front": ["top-left", "top-right", "bottom-right", "bottom-left"],
}


def load_views(path="views.json"):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return {}
    with open(path) as f:
        return json.load(f)


def save_views(views, path="views.json"):
    temp_path = path + ".tmp"
    with open(temp_path, "w") as f:
        json.dump(views, f, indent=2)
    os.replace(temp_path, path)


def face_to_image(corners, points):
    # map points given in face units (0..3) onto the clicked face corners in the image
    grid = cv2.getPerspectiveTransform(np.float32(FACE_SQUARE), np.float32(corners))
    return cv2.perspectiveTransform(np.float32([points]), grid)[0]


def sticker_centers(corners):
    return face_to_image(corners, STICKER_POINTS)


def sample_points(corners):
    # where the 36 sample patches land in the image
    return face_to_image(corners, SAMPLE_POINTS)


def preview(camera, title, message):
    # live camera feed until enter or 's' is pressed in the window; 'q' cancels
    print(message)
    print("press enter (or 's') in the video window when it looks right, 'q' to cancel")
    while True:
        frame = camera.read()
        if frame is None:
            continue

        # crosshair at the image center, to help aim at the face
        h, w = frame.shape[:2]
        cv2.line(frame, (w // 2 - 20, h // 2), (w // 2 + 20, h // 2), (0, 255, 255), 1)
        cv2.line(frame, (w // 2, h // 2 - 20), (w // 2, h // 2 + 20), (0, 255, 255), 1)
        cv2.putText(frame, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow(title, frame)
        key = cv2.waitKey(1)
        if key == 13 or key == ord("s"):      # 13 = enter
            cv2.destroyWindow(title)
            return True
        if key == ord("q"):
            cv2.destroyWindow(title)
            return False


def click_corners(camera, view):
    clicks = []
    order = CLICK_ORDER[view]

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(clicks) < 4:
            clicks.append([x, y])

    cv2.namedWindow("teach " + view)
    cv2.setMouseCallback("teach " + view, on_click)
    print("click the face corners by where they are ON THE CUBE, in this order:")
    print("  " + ", ".join(order))
    print("'r' = reset clicks, 's' = save, 'q' = cancel")

    while True:
        frame = camera.read()
        if frame is None:
            continue

        for i in range(len(clicks)):
            x, y = clicks[i]
            cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
            cv2.putText(frame, order[i], (x + 8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        if len(clicks) < 4:
            cv2.putText(frame, "next: " + order[len(clicks)], (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        else:
            draw_face(frame, clicks)
            cv2.putText(frame, "press 's' to save", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        cv2.imshow("teach " + view, frame)
        key = cv2.waitKey(1)
        if key == ord("r"):
            clicks.clear()
        if key == ord("q"):
            cv2.destroyWindow("teach " + view)
            return None
        if key == ord("s") and len(clicks) == 4:
            cv2.destroyWindow("teach " + view)
            return clicks


def sample_colors(frame, corners, points):
    # small patches, since there are 4 per sticker
    width = np.linalg.norm(np.float32(corners[1]) - np.float32(corners[0]))
    r = max(2, int(width / 40))

    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    colors = []
    for s in range(9):
        pixels = []
        for k in range(4):
            x, y = points[s * 4 + k]
            x = int(x)
            y = int(y)
            pixels.append(lab[y - r:y + r, x - r:x + r].reshape(-1, 3))
        all_pixels = np.concatenate(pixels)
        colors.append(np.median(all_pixels, axis=0).tolist())    # median skips odd pixels
    return colors


def read_face(camera, corners, frames=10):
    # the camera keeps a few old frames; throw them away so we see the cube as it is now
    for i in range(5):
        camera.read()

    points = sample_points(corners)
    all_samples = []
    for i in range(frames):
        frame = camera.read()
        if frame is None:
            continue
        all_samples.append(sample_colors(frame, corners, points))

    if len(all_samples) == 0:
        return None

    # median of each sticker across frames
    colors = []
    for s in range(9):
        values = []
        for sample in all_samples:
            values.append(sample[s])
        colors.append(np.median(values, axis=0).tolist())
    return colors


def draw_face(frame, corners):
    # face outline, sticker numbers, and the yellow sample dots
    pts = np.int32(corners).reshape(-1, 1, 2)
    cv2.polylines(frame, [pts], True, (0, 255, 0), 2)

    centers = sticker_centers(corners)
    for i in range(9):
        x, y = centers[i]
        cv2.putText(frame, str(i), (int(x) - 4, int(y) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

    for x, y in sample_points(corners):
        cv2.circle(frame, (int(x), int(y)), 2, (0, 255, 255), -1)