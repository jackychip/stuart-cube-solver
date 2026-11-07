import threading
import time


class Status:
    # shared between the solve thread (writes it) and the display loop (reads it)

    def __init__(self):
        self.text = ""
        self.corners = None      # face corners to draw while a face is being read
        self.stop = False        # set by 'q', checked between actions
        self.done = False        # set when the solve thread finishes
        self.enter = threading.Event()

    def wait_for_enter(self, text):
        # show text, wait for enter in the video window. returns False if 'q' was pressed
        self.text = text
        self.enter.clear()
        while not self.enter.is_set():
            if self.stop:
                return False
            time.sleep(0.05)
        return True