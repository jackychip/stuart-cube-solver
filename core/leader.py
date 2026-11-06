import threading
import time

from lerobot.teleoperators.so_leader import SO101Leader, SO101LeaderConfig

from core.arm import JOINTS


class Leader:
    def __init__(self, port, leader_id):
        config = SO101LeaderConfig(port=port, id=leader_id, use_degrees=True)
        self.device = SO101Leader(config)
        self.device.connect()

    def read(self):
        action = self.device.get_action()        # {"shoulder_pan.pos": ..., ...}
        positions = {}
        for joint in JOINTS:
            positions[joint] = action[joint + ".pos"]
        return positions

    def disconnect(self):
        self.device.disconnect()


class Mirror:
    # copies the leader to the follower in the background, while the main program waits for enter

    def __init__(self, arm, leader, hz=50):
        self.arm = arm
        self.leader = leader
        self.hz = hz
        self.running = False
        self.latest = None
        self.lock = threading.Lock()
        self.thread = None

    def start(self):
        # ease the follower to the leader's current pose first, so it doesn't jump
        self.latest = self.leader.read()
        self.arm.move_to(self.latest, duration=2.0)

        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running:
            pose = self.leader.read()

            action = {}
            for joint in JOINTS:
                action[joint + ".pos"] = pose[joint]
            self.arm.robot.send_action(action)

            with self.lock:
                self.latest = pose
            time.sleep(1 / self.hz)

    def capture(self):
        # the leader's current values = the command that put the follower where you see it
        with self.lock:
            return dict(self.latest)

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()