# myagv_2023_jn

An integrated navigation and control stack for the **Elephant Robotics myAGV (2023 Jetson Nano Edition)**. This repository contains specialized modules for **vision-guided target following** and **autonomous spatial waypoint management**.

---

# Features

- ArUco marker following (ROS 1)
- Human following using MediaPipe Pose (ROS 1)
- Navigation to named waypoints using ROS 2 Nav2

---

# Ground Zero: System Prerequisites & Initialization

Before running any application modules, initialize the required hardware and software components for your selected module.

> **First-Time Setup**
>
> If this is your first time using the platform, complete the initial network mapping and remote access configuration by following the official Elephant Robotics guide:
>
> https://docs.elephantrobotics.com/docs/myagv_jn23_en/5-BasicApplication/5.1-SystemInstructionManual.html

---

# Module 1 — ArUco Marker Follower (ROS 1)

The **ArUco Marker Follower** uses OpenCV's ArUco detection to locate and follow printed fiducial markers while maintaining a safe distance.

## Features

### Vision Optimization

- Uses **DICT_4X4_50**
- Sub-pixel corner refinement (`CORNER_REFINE_SUBPIX`)
- Stable pose estimation
- Reduced steering jitter

### Motion Control

- Computes horizontal displacement (`error_x`)
- Smooth proportional turning
- Angular velocity limited between:

```
-0.6 rad/s → 0.6 rad/s
```

### Distance Regulation

Maintains an ideal following distance using marker width:

```
190 px ← Ideal Distance → 210 px
```

### Fault Tolerance

Includes a **0.5 second COAST_TIME**.

If the marker is temporarily lost because of:

- motion blur
- glare
- camera noise

The robot continues its previous motion briefly instead of stopping abruptly.

---

## Running the ArUco Follower

### Terminal 1 — Launch Camera

```bash
roslaunch orbbec_camera astra_pro2.launch
```

### Terminal 2 — Launch myAGV Odometry

```bash
roslaunch myagv_odometry myagv_active.launch
```

### Terminal 3 — Run the ArUco Follower

Navigate to the project directory containing the script and run:

```bash
python3 aruco_follower.py
```

---

# Module 2 — Human Follower (ROS 1)

This module follows a human using **Google MediaPipe Pose Estimation**.

Instead of tracking hands or feet, it follows the user's torso for smoother and more stable movement.

---

## Features

### Edge Optimized

Configured for Jetson Nano:

- `model_complexity = 0`
- Camera resized to **320 × 240**
- Lightweight inference

### Stable Target Detection

Computes the torso center using landmarks:

- Left Shoulder (11)
- Right Shoulder (12)
- Left Hip (23)
- Right Hip (24)

This avoids sudden movement caused by swinging arms.

### Motion Control

Features include:

- Angular deadzone of **0.05**
- Fast catch-up turning gain (**-2.5**)
- Shoulder-width depth estimation

---

## Running the Human Follower

### Terminal 1 — Launch Camera

```bash
roslaunch orbbec_camera astra_pro2.launch
```

### Terminal 2 — Launch myAGV Odometry

```bash
roslaunch myagv_odometry myagv_active.launch
```

### Terminal 3 — Run the Human Follower

Navigate to the project directory containing the script and run:

```bash
python3 human_following.py
```

---

# Module 3 — Navigation to Named Waypoints (ROS 2)

This module provides an intuitive waypoint management system using **ROS 2 Nav2**.

Instead of hardcoding coordinates inside Python scripts, named locations are stored in a YAML configuration file.

Example:

```yaml
table:
  x: 2.51
  y: 1.78
  yaw: 1.57

fruit:
  x: -1.20
  y: 0.83
  yaw: 0.00
```

---

## Features

### Decoupled Configuration

Waypoints are stored inside:

```
waypoints.yaml
```

### Non-Blocking Recorder

The recorder:

- subscribes to `/amcl_pose`
- uses a `MultiThreadedExecutor`
- allows terminal input while ROS continues spinning

### Autonomous Navigation

Uses the Nav2 `BasicNavigator` API to:

- compute global paths
- perform obstacle avoidance
- visualize trajectories in RViz
- navigate autonomously to saved destinations

---

# Navigation Workflow (ROS 2)

## Terminal 1 — Start the LiDAR

```bash
./start_ydlidar.sh
```

---

## Terminal 2 — Launch myAGV Odometry

```bash
ros2 launch myagv_odometry myagv_active.launch
```

---

## Terminal 3 — Launch Navigation Stack

```bash
ros2 launch myagv_navigation2 navigation2_active.launch.py map:=/path-to-your-map.yaml
```

This starts:

- Navigation stack
- Localization
- RViz
- Costmaps
- Planner
- Controller

---

## Step 1 — Record a Waypoint

Navigate to the scripts directory:

```text
~/myagv_ros2/src/myagv_navigation2/scripts/
```

Run:

```bash
python3 record_waypoints.py
```

Example prompt:

```
Enter waypoint name:
```

The current robot pose is automatically saved to:

```
~/myagv_ros2/src/myagv_navigation2/config/waypoints.yaml
```

---

## Step 2 — Navigate to a Saved Waypoint

From the same scripts directory:

```text
~/myagv_ros2/src/myagv_navigation2/scripts/
```

Run:

```bash
python3 goto_waypoint.py
```

The robot will:

- load the selected waypoint
- compute a global path
- visualize the path in RViz
- autonomously navigate to the destination
