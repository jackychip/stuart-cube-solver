import time
from lerobot.robots.so_follower import SO101Follower, SO101FollowerConfig

JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]

class Arm:
    """
    
    Direct joint control of an SO-101 follower arm.

    Wraps LeRobot's SO101Follower class. Positions are in degrees for the five arm
    joints (0 = middle of each joint's calibrated range) and 0-100 for the gripper.
    Degree commands are NOT clamped to the calibrated range

    """
    def __init__(self, port, robot_id):
        """
        
        Create the robot instance and connect to it.

        Opens the serial port, loads the calibration file into motors, and enables
        torque. After this returns, the arm holds it current pose.

        Args:
            port (str): Serial port of the motor bus (e.g. "/dev/tty.usbmodem5B415336751").
                You can find it with `lerobot-find-port`.
            robot_id (str): Calibration id or the calibration file name without
                ".json" in ~/.cache/huggingface/lerobot/calibration/robots/.

        Raises:
            ConnectionError: If the port can't be opened or the motors don't respond
        
        """
        config = SO101FollowerConfig(
            port=port,
            id=robot_id,
            use_degrees=True,
        )
        self.robot = SO101Follower(config)
        self.robot.connect()

    def read(self):
        """
        
        Read the measured position of every joint.

        Returns the actual encoder positions.

        Returns:
            dict[str, float]: Joint name -> position. Ex.
                {
                "shoulder_pan": 3.2, 
                "shoulder_lift", -10.5,
                ...
                "gripper", 42.0
                }

                Arm joints are in degrees, gripper is in 0-100.
        
        """
        obs = self.robot.get_observation()

        positions = {}

        for joint in JOINTS:
            key = joint + ".pos"
            positions[joint] = obs[key]

        return positions

    def move_to(self, target, duration=2.0):
        """
        
        Move joints to target positions along a straight-line path in joint space.

        Reads the current position, then sends `steps` intermediate goals at 50Hz
        (one every 20ms), so the motion takes `duration` seconds instead of the 
        servos jumping at full speed. Only joints listed in `target` are
        commanded; all other joints keep their current position.

        Blocking: returns after the last step is sent. Does not wait for the 
        servos to actually arrive, so check with read() if accuracy matters.

        Args:
            target (dict[str, float]): Joint name -> goal position. Ex.
                {"elbow_flex": 30.0} or {"wrist_flex": -10.0, "gripper": 20.0}.
                Arm joints in degrees, gripper in 0-100.
            duration (float): Total time for the move, in seconds. Default 2.0.
            steps (int): Number of intermediate goals sent. Default 100
                (50Hz for a 2s move).

        Raises:
            KeyError: If `target` contains a name not in JOINTS.
        
        """
        hz = 50 # commands per second
        steps = int(duration * hz)
        if steps < 1:
            steps = 1

        start = self.read()

        for i in range(1, steps + 1):
            t = i/steps

            action = {}

            for joint in target:
                goal = target[joint]
                current_goal = start[joint] + t * (goal - start[joint])
                key = joint + ".pos"
                action[key] = current_goal

            self.robot.send_action(action)
            time.sleep(1 / hz)

    def torque_off(self):
        self.robot.bus.disable_torque()

    def torque_on(self):
        present = self.robot.bus.sync_read("Present_Position")
        self.robot.bus.sync_write("Goal_Position", present)
        self.robot.bus.enable_torque()

    def disconnect(self):
        """
        
        Disconnect from the arm and close the serial port.

        Disables torque by default, so the arm goes limp and falls due to gravity.
        Move it to a resting pose before calling.

        """
        self.robot.disconnect()
