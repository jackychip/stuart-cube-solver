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
    """A USB camera opened by name, returning frames as images."""

    def __init__(self, name_contains, width=640, height=420):
        """
        
        Open the camera and request a resolution.

        Args:
            name_contains (str): Part of the camera's name (see list_cameras()).
            width (int): Requested frame width in pixels. Default 1280.
            height (int): Requested frame height in pixels. Default 720.
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

    def read(self):
        ok, frame = self.cap.read()
        if not ok:
            return None
        return frame

    def close(self):
        self.cap.release()