def wiggle(arm, pan_amount=15, roll_amount=30, wiggles=4, speed=0.25):
    """
    
    Wiggle the base left/right while counter-rolling the wrist, then return.

    All motion is relative to the arm's position when called, so it can run
    from any pose. Only shoulder_pan and wrist_roll move.

    Args:
        arm (Arm): A connected Arm.
        pan_amount (float): Degrees to swing shoulder_pan each side of start.
        roll_amount (float): Degrees to twist wrist_roll each side of start.
        wiggles (int): Number of left-right cycles.
        speed (float): Seconds per half-wiggle. Below ~0.15 the servos
            can't keep up and the motion shrinks instead of speeding up.
    
    """
    start = arm.read()

    for i in range(wiggles):
        left = {
            "shoulder_pan": start["shoulder_pan"] + pan_amount,
            "wrist_roll": start["wrist_roll"] - roll_amount,
        }
        arm.move_to(left, duration=speed)

        right = {
            "shoulder_pan": start["shoulder_pan"] - pan_amount,
            "wrist_roll": start["wrist_roll"] + roll_amount,
        }
        arm.move_to(right, duration=speed)

    home = {
        "shoulder_pan": start["shoulder_pan"],
        "wrist_roll": start["wrist_roll"],
    }
    arm.move_to(home, duration=0.5)