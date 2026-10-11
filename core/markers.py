import math
import cv2

DICTIONARY = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
EXPECTED_IDS = [0, 1]

class Marker:

    def __init__(self, marker_id, corners):
        self.id = marker_id
        self.corners = corners

        # find center by averaging x and y of 4 corners of a marker
        sum_x = 0
        sum_y = 0
        for x, y in corners:
            sum_x += x
            sum_y += y
        self.center = (sum_x/4, sum_y/4)

        # find size (average length of 4 sides)
        total = 0
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i+1) % 4]
            total += math.hypot(x2-x1, y2-y1)
        self.size = total/4

        # find angle
        top_left = corners[0]
        top_right = corners[1]
        dx = top_right[0] - top_left[0]
        dy = top_right[1] - top_left[1]
        self.angle = math.degrees(math.atan2(dy, dx))

class MarkerDetector:
    """Finds ArUco markers in camera frames."""

    def __init__(self):
        params = cv2.aruco.DetectorParameters()
        params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

        self.detector = cv2.aruco.ArucoDetector(DICTIONARY, params)

    def detect(self, frame):
        # Returns:
        #   all_corners:    list of arrays, one per marker, each with shape (1,4,2)
        #   ids:            array with shape (N, 1), or None if nothing found
        all_corners, ids, rejected = self.detector.detectMarkers(frame)

        found = {}
        if ids is None:
            return found

        ids = ids.flatten()

        for i in range(len(ids)):
            marker_id = int(ids[i])
            if marker_id not in EXPECTED_IDS:
                continue

            points = all_corners[i].reshape(4,2)

            corners = []
            for point in points:
                corners.append((float(point[0]), float(point[1])))

            found[marker_id] = Marker(marker_id, corners)

        return found

    def draw(self, frame, markers):
        for marker in markers.values():
            for i in range(4):
                x1, y1 = marker.corners[i]
                x2, y2 = marker.corners[(i + 1) % 4]
                cv2.line(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

            tl_x, tl_y = marker.corners[0]
            cv2.circle(frame, (int(tl_x), int(tl_y)), 6, (0, 0, 255), -1)


            cx, cy = marker.center
            cv2.circle(frame, (int(cx), int(cy)), 4, (255, 0, 0), -1)
            label = "id " + str(marker.id) + "  " + str(round(marker.size)) + "px"
            cv2.putText(frame, label, (int(cx) + 10, int(cy)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

def measure(camera, detector, frames=20):
    for i in range(5):
        camera.read()

    readings = {}
    for i in range(frames):
        frame = camera.read()
        if frame is None:
            continue

        for marker_id, marker in detector.detect(frame).items():
            if marker_id not in readings:
                readings[marker_id] = []
            readings[marker_id].append(marker)

    result = {}
    for marker_id, markers in readings.items():
        if len(markers) < frames / 2:
            continue

        n = len(markers)
        sum_x = 0
        sum_y = 0
        sum_size = 0
        sum_angle = 0
        for m in markers:
            sum_x += m.center[0]
            sum_y += m.center[1]
            sum_size += m.size
            sum_angle += m.angle

        result[marker_id] = {
            "center": [sum_x / n, sum_y / n],
            "size": sum_size / n,
            "angle": sum_angle / n,
        }

    return result