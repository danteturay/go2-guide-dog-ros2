# Go2 Guide Dog - ROS2

A ROS2-based software stack for using the Unitree Go2 robot dog as a guide dog assistant for blind and visually impaired users.

## Overview

This repository provides a complete pipeline from simulation to deployment on the physical Go2 robot, including:

- Obstacle avoidance using LiDAR
- Object detection using YOLO
- Voice feedback via the Go2's onboard speaker
- Safe velocity command filtering

## Repository Structure
src/

├── obstacle_avoidance.py  # Safety node - filters unsafe velocity commands

└── fake_lidar.py          # Test utility - simulates LiDAR data
## Setup

### Requirements
- Docker
- ROS2 Humble (via Docker)
- Unitree Go2 Edu robot

### Quick Start

1. Clone this repo
2. Start Docker container with unitree_ros2
3. Source the environment:
```bash
source docker_setup.sh
```

4. Run the obstacle avoidance node:
```bash
python3 src/obstacle_avoidance.py
```

## Testing Without a Robot

Use the fake LiDAR publisher to test the obstacle avoidance node:

```bash
# Terminal 1
python3 src/obstacle_avoidance.py

# Terminal 2  
python3 src/fake_lidar.py

# Terminal 3 - send movement commands
ros2 topic pub /cmd_vel_raw geometry_msgs/msg/Twist "{linear: {x: 0.5}}" --rate 10

# Terminal 4 - watch safe output
ros2 topic echo /cmd_vel
```

## Authors
Dante Turay - University of Southampton 2026