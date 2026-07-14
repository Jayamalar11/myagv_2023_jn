# myagv_2023_jn

An integrated navigation and control stack for the **Elephant Robotics myAGV (2023 Jetson Nano Edition)**. This repository contains specialized modules for **vision-guided target following** and **autonomous spatial waypoint management**.

---

# Features

- ArUco marker following
- Human following using MediaPipe Pose
- Navigation to named waypoints using ROS 2 Nav2

---

# Ground Zero: System Prerequisites & Initialization

Before running any application modules, initialize the core hardware communication layer to bridge your Python nodes with the myAGV hardware.

> **First-Time Setup**
>
> If this is your first time using the platform, complete the initial network mapping and remote access configuration by following the official Elephant Robotics guide:
>
> https://docs.elephantrobotics.com/docs/myagv_jn23_en/5-BasicApplication/5.1-SystemInstructionManual.html

---

## Launch Base Odometry

Open a terminal on the Jetson Nano and run:

```bash
roslaunch myagv_odometry myagv_active.launch
```

Keep this terminal running while using any module in this repository.

---

# Module 1 — ArUco Marker Follower

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
-0.6 rad/s  →  0.6 rad/s
```

### Distance Regulation

Maintains an ideal following distance using marker width:

```
190 px  ← Ideal Distance → 210 px
```

### Fault Tolerance

Includes a **0.5 second COAST_TIME**.

If the marker is temporarily lost because of:

- motion blur
- glare
- camera noise

the robot continues its previous motion briefly instead of stopping abruptly.

---

## Running the ArUco Follower

### Terminal 1

Launch the Astra Pro Plus camera.

```bash
roslaunch astra_camera astra_pro_plus.launch
```

### Terminal 2

Run the follower node.

```bash
python3 aruco_follower.py
```

---

# Module 2 — Human Follower

This module follows a human using **Google MediaPipe Pose Estimation**.

Instead of tracking hands or feet, it follows the user's torso for much smoother movement.

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

### Terminal 1

```bash
roslaunch astra_camera astra_pro_plus.launch
```

### Terminal 2

```bash
python3 human_following.py
```

---

# Module 3 — Navigation to Named Waypoints

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

using semantic names such as:

- table
- kitchen
- fruit
- charging_station

---

### Non-Blocking Recorder

The recorder:

- subscribes to `/amcl_pose`
- uses a `MultiThreadedExecutor`
- allows terminal input while ROS continues spinning

---

### Autonomous Navigation

Uses the Nav2 `BasicNavigator` API to:

- compute global paths
- perform obstacle avoidance
- visualize trajectories in RViz
- navigate autonomously to saved destinations

---

# Navigation Workflow

## Step 1 — Launch Navigation

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

## Step 2 — Record a Waypoint

Drive the robot using the **Nav2 Goal Tool** in RViz.

After the robot reaches the desired location:

```bash
python3 waypoint_recorder.py
```

Example prompt:

```
Enter waypoint name:
```

The pose is automatically saved into:

```
waypoints.yaml
```

---

## Step 3 — Navigate to a Saved Waypoint

Example:

```bash
python3 goto_waypoint.py 
```

The robot will:

- load the waypoint
- compute a global path
- display the path in RViz
- autonomously drive to the destination

---
