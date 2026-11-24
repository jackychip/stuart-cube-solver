# Stuart

Stuart is an SO-101 robot arm that solves a Rubik's Cube. It scans the cube with one camera, plans the solve, and carries it out with motions taught from a second arm.

<a href="https://jackyzhang.vercel.app/#projects">
  <img src="https://jackyzhang.vercel.app/media/stuart-timelapse.jpg" alt="Stuart, a white SO-101 arm, solving a Rubik's Cube" width="300">
</a>

Videos and a longer write-up: [jackyzhang.vercel.app](https://jackyzhang.vercel.app/#projects)

## How it works

1. **Scan.** The arm moves the camera over the cube, reads the top face, then re-grips and rotates the cube to show the next face. Seven rotations show all six faces.
2. **Classify.** Each sticker's colour is read in CIE Lab and labelled by the centre sticker it is closest to.
3. **Solve.** [Kociemba's two-phase solver](https://github.com/muodov/kociemba) returns face turns such as `R U' F2`.
4. **Plan.** Stuart can only turn one layer, so the planner rewrites those face turns as whole-cube rotations plus that one turn.
5. **Execute.** The arm replays taught poses and waypoint paths, streaming joint targets at 50 Hz.

### Vision

- Each camera view is taught once: an arm pose, plus the four corners of the face clicked in the image. A perspective transform maps a 3×3 grid onto those corners.
- Every sticker is sampled at four small patches, one per quadrant, 0.28 sticker-widths off centre. Sampling the middle read the white centre sticker as blue because of the logo printed on it.
- A sticker's colour is the median of its patch pixels, then the median across 10 frames. A full scan reads 216 patches (6 faces × 9 stickers × 4).
- There are no fixed colour thresholds. Each of the 54 stickers takes the label of its nearest centre sticker in Lab space, so the classifier adapts to the lighting on every scan. A scan that doesn't produce exactly nine of each colour is rejected.

### Cube model

`core/cube_model.py` stores the cube as 54 stickers, each keyed by its 3D position and outward normal, in Kociemba's `URFDLB` order. A reading is taken at a fixed physical position (the top face), so `core/scan.py` finds which logical sticker it was by undoing the rotations done so far, as 90° vector rotations.

The scan leaves the cube in a different orientation from where it started. The planner starts from that orientation instead of rotating the cube back.

### Planning

The cube sits in a holder that keeps the bottom layer still. The gripper holds the two layers above it and twists. That one move, written `u`, is a turn of the bottom face plus a quarter turn of the whole cube about the vertical axis.

`core/solver.py` tracks which face is at each of the six positions. For every move in the solution it runs a breadth-first search over the three rotations the arm knows (`x'`, `y`, `y'`) to bring the target face to the bottom, then adds `u`, `u'` or `u u`. Before the arm moves, `check_plan` replays the arm actions and confirms they match the solver's move list.

Output of `scripts/test_solver.py` for one scramble:

```text
kociemba: D2 R' D' F2 B D R2 D2 R' F2 D' F2 U' B2 L2 U2 D R2 U
arm:      u u y' x' u' y' x' u' x' x' x' u u x' x' u y' x' u x' u u x' u u x' u' x' u u y x' u' y' x' u u x' x' x' u' y' x' u u y x' u u y x' u u x' x' u y' x' u u x' x' x' u
19 moves -> 29 turns + 35 rotations
plan correct: True
```

### Teaching

Poses are taught by teleoperation. A background thread copies the leader arm's joint angles to the follower at 50 Hz, and pressing Enter saves the pose. The saved values are the leader's command, not the follower's encoder reading, so a replay sends the same command that put the arm there.

- **Shared poses:** `hover`, `turn_grasp` and `grip_closed`. Every action starts and ends at `hover`, so any action can follow any other.
- **Turns:** a `turned` pose and a `retreat` pose for each direction.
- **Rotations:** three waypoint paths each (approach, carry, exit) and a grip value.

The teaching tool warns when the wrist roll crosses the ±180° wrap point between waypoints, when a grasp isn't straight below `hover`, and when a path starts or ends more than 20° from `hover`.

### Motion

- `Arm.move_to` interpolates in joint space at 50 Hz along a quintic ease curve, `10t³ − 15t⁴ + 6t⁵`, so each joint starts and stops with zero velocity and zero acceleration.
- `Arm.move_through` runs a multi-waypoint path as one continuous move. Time is split across segments by the largest joint change in each, and the easing is applied once over the whole path.
- For a turn, the wrist goes 5° past the taught quarter-turn pose and then backs off before releasing. The jaws slide clear of the cube before lifting, and the wrist unrolls in the air. A wrist target beyond ±170° raises an error instead of letting the joint wrap.

## Hardware

- SO-101 follower arm (the one that solves)
- SO-101 leader arm (only for teaching)
- A USB camera mounted on the arm
- A holder that keeps the cube's bottom layer still
- A Mac. The camera code uses OpenCV's AVFoundation backend.

## Setup

Tested with Python 3.12, LeRobot 0.6.2, kociemba 1.2.1 and NumPy 2.2.

1. Install [LeRobot](https://github.com/huggingface/lerobot) with Feetech motor support, and calibrate both arms by following its SO-101 guide. The calibration ids must match `ARM_ID` and `LEADER_ID` in `config.py`.
2. Install the other dependencies:

   ```bash
   pip install kociemba cv2-enumerate-cameras opencv-python
   ```

   The scripts open video windows, so OpenCV needs GUI support. The headless build can't show them.
3. Edit `config.py`:

   | Setting | Meaning |
   | --- | --- |
   | `ARM_PORT` | Serial port of the follower arm. `lerobot-find-port` prints it. |
   | `ARM_ID` | LeRobot calibration id of the follower |
   | `LEADER_PORT` | Serial port of the leader arm |
   | `LEADER_ID` | LeRobot calibration id of the leader |
   | `CAMERA_NAME` | Part of the camera's name, not case-sensitive |

The `poses.json` and `views.json` in this repo were taught on my arm, holder and camera. Any other setup needs its own.

## Usage

Run everything from the repo root as a module, so that `config` and `core` import correctly.

Check the planner, with no hardware connected:

```bash
python -m scripts.test_solver
```

Check the arm connection:

```bash
python -m scripts.demo_wiggle
```

Teach the poses with the leader arm. The flags at the top of the script choose what to teach: the shared poses, the two turns, or one rotation.

```bash
python -m scripts.step3_teach_turn_poses
```

Replay a turn in each direction, then one rotation:

```bash
python -m scripts.step4_test_turn
```

```bash
python -m scripts.step4b_test_rotation
```

Solve a known scramble without the camera:

```bash
python -m scripts.step5_test_solve
```

Teach the camera view. Move the arm until the camera sees the top face, then click the four face corners in the order the script prints.

```bash
python -m scripts.step6_teach_views
```

Check the colour readings. Press `p` in the video window to print each sticker's Lab value.

```bash
python -m scripts.step7_test_view
```

Scan and solve:

```bash
python -m scripts.solve
```

`solve` shows the live camera feed with the current step drawn on it. Keys go in the video window: Enter continues, and `q` stops after the current action.

Disconnecting turns the motor torque off and the arm goes limp. Every script asks you to support the arm first.

## Repository layout

| Path | Contents |
| --- | --- |
| `config.py` | Ports, calibration ids and the camera name |
| `core/arm.py` | Follower control: read, eased moves, waypoint paths, torque |
| `core/leader.py` | Leader arm, and the thread that mirrors it to the follower |
| `core/camera.py` | Camera lookup by name, and a thread that keeps the newest frame |
| `core/face_reader.py` | Corner teaching, sampling points and colour reads |
| `core/colors.py` | Nearest-centre colour classification |
| `core/cube_model.py` | The 54-sticker cube model |
| `core/scan.py` | Scan sequences, and where each reading goes in the cube state |
| `core/solver.py` | Kociemba wrapper, orientation tracking, arm planner and plan check |
| `core/status.py` | State shared between the solve thread and the display loop |
| `routines/` | Teaching, turns, rotations, scanning and running a plan |
| `scripts/` | One script per step, plus `solve.py` |
| `poses.json` | Taught poses and rotation paths |
| `views.json` | Taught camera view: arm pose and face corners |

Some files are left from earlier versions and the solver doesn't use them: `main.py`, `core/markers.py`, `routines/observe.py`, `scripts/step1_teach_observe.py`, `scripts/step2_check_observe.py`, `observe.json`, `poses_old.json` and `poses_handtaught.json.`.

## Next

- Port the arm into MuJoCo and build forward and inverse kinematics, so targets can be given in Cartesian space instead of as taught joint poses.
