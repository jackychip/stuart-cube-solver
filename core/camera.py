import threading
import time

import cv2
from cv2_enumerate_cameras import enumerate_cameras

def list_cameras():
    """Print every connected camera's OpenCV index and name."""
    for cam in enumerate_cameras(cv2.CAP_AVFOUNDATION):
        print(cam.index, cam.name)

def find_camera(name_contains):
    """
    
    Find a camera's OpenCV index by part of its name.

    Args:
        name_contains (str): Text that appears in the camera's name e.g. "USB".
            Not case-sensitive.

    Returns:
        int: The OpenCV index to open.

    Raises:
        RuntimeError: If no connected camera's name contains the text.
    
    """
    for cam in enumerate_cameras(cv2.CAP_AVFOUNDATION):
        if name_contains.lower() in cam.name.lower():
            return cam.index

    raise RuntimeError("no camera with '" + name_contains + "' in its name.")

class Camera:
    """A USB camera opened by name. A background thread keeps the newest frame."""

    def __init__(self, name_contains, width=640, height=420):
        """
        
        Open the camera, request a resolution, and start the grabber thread.

        Args:
            name_contains (str): Part of the camera's name (see list_cameras()).
            width (int): Requested frame width in pixels. Default 640.
            height (int): Requested frame height in pixels. Default 420.
                The camera may not support every resolution; it picks the 
                closest one it can do.

        Raises:
            RuntimeError: If the camera isn't found or can't be opened.

        """
        index = find_camera(name_contains)

        self.cap = cv2.VideoCapture(index, cv2.CAP_AVFOUNDATION)
        if not self.cap.isOpened():
            raise RuntimeError("could not open camera" + str(index))

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # a background thread keeps reading, so read() always gets the newest frame
        # and several loops (display + scanning) can share one camera
        self.frame = None
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            ok, frame = self.cap.read()       # blocks until the camera has a new frame
            if not ok:
                time.sleep(0.01)
                continue
            with self.lock:
                self.frame = frame

    def read(self):
        # a copy, so drawing on it doesn't change what other loops see
        with self.lock:
            if self.frame is None:
                return None
            return self.frame.copy()

    def close(self):
        self.running = False
        self.thread.join(timeout=1.0)
        self.cap.release()