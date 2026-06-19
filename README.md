# Go2 Guide Dog — ROS2

A ROS2-based software stack that turns the Unitree Go2 robot dog into a guide dog assistant for blind and visually impaired users.

Built during a research internship at the University of Southampton, supervised by Dr Mohammad Soorati.

This README assumes **no prior ROS2 or Gazebo experience**. Follow it top to bottom, and you'll go from a blank Ubuntu machine to a working simulated guide dog.

---

## What This Project Does

- **Obstacle avoidance** - automatically slows or stops the robot when something is in its path, using LiDAR
- **Object detection** - uses YOLOv8 to identify what an obstacle is (person, car, bicycle, etc.)
- **Voice feedback** - the robot announces hazards out loud ("Warning, person detected ahead. Stopping.")
- **Voice commands** - control the robot by speaking ("go forward", "stop", "turn left")

### How the pieces fit together

```
[Microphone] → voice_commands.py ──→ /cmd_vel_raw ─────┐
                                                          ├─→ obstacle_avoidance.py ──→ /cmd_vel ──→ [Go2]
[LiDAR]      ───────────────────→ /velodyne_points ──────┘            │
[Camera]     ───────────────────→ /camera/rgb/image_raw → yolo_detector.py → /detections
                                                                        │
                                                            voice_feedback.py → [Speaker]
```

In plain English: a movement command (from voice or keyboard) goes through a safety filter before it ever reaches the robot. The safety filter checks the LiDAR and, if something is detected by YOLO, what that something is. If it's safe, the command passes through unchanged. If something is close, the command slows down or gets blocked. The whole time, a voice node announces what's happening.

---

## Why You Need a Linux Environment

ROS2 and Gazebo (the simulator) are built for Ubuntu Linux. They technically *can* run on macOS or Windows, but in practice:

- **macOS**: Gazebo's 3D graphics window does not work through Docker on Apple Silicon Macs. You'll get the simulation running "headless" (no visuals) at best, which makes debugging very hard.
- **Windows**: WSL2 can work, but is fiddly to set up and has the same graphics limitations as Mac in many configurations.

**The reliable path is a real or virtual Ubuntu 22.04 machine.** If you don't have a spare Ubuntu PC, a virtual machine works fine — that's what this guide uses.

---

## Part 1: Setting Up Ubuntu 22.04

### Option A: You already have Ubuntu 22.04

Skip to [Part 2](#part-2-installing-ros2-humble).

### Option B: You need a virtual machine

You'll need a virtualisation tool. **VMware Workstation** is recommended (free for personal use) — VirtualBox also works.

1. **Download the Ubuntu 22.04 Desktop ISO**
   Go to [releases.ubuntu.com/22.04](https://releases.ubuntu.com/22.04/) and download `ubuntu-22.04.x-desktop-amd64.iso`.

   ⚠️ **It must be 22.04 specifically.** Newer versions (24.04, 26.04) are not compatible with ROS2 Humble, which this project depends on.

2. **Create the VM**
   - Open VMware Workstation → **Create a New Virtual Machine**
   - Point it at the ISO you downloaded
   - Give it generous resources — this matters more than you'd think:
     - **RAM**: at least 8GB, ideally 12GB+ if your host machine has 32GB or more
     - **CPU cores**: at least 4
     - **Disk**: at least 50GB
   - In VM Settings → Display, enable **"Accelerate 3D graphics"**

3. **Install Ubuntu** following the on-screen installer (standard installation, your choice of username/password)

4. **Enable clipboard sharing** between your host machine and the VM:
   ```bash
   sudo apt install open-vm-tools open-vm-tools-desktop -y
   sudo reboot
   ```

#### If VM creation fails with a virtualisation error

If you see an error like `0x80370114` or anything mentioning "virtualisation" or "VT-x", your PC's BIOS has hardware virtualisation disabled.

1. Restart your PC and enter the BIOS (commonly F2, F10, F12, or Delete during boot — check your motherboard manual)
2. Find **Intel VT-x** or **AMD-V / SVM Mode** (usually under Advanced → CPU Configuration)
3. Enable it, save, and exit
4. Retry VM creation

---

## Part 2: Installing ROS2 Humble

Open a terminal in your Ubuntu machine and run the following, one block at a time.

**Update the system:**
```bash
sudo apt update && sudo apt upgrade -y
```

**Add the ROS2 package repository:**
```bash
sudo apt install curl software-properties-common -y
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

**Install ROS2 Humble (this takes a while):**
```bash
sudo apt update
sudo apt install ros-humble-desktop -y
```

**Install Gazebo and supporting tools:**
```bash
sudo apt install ros-humble-ros-gz ignition-fortress python3-colcon-common-extensions -y
```

**Make ROS2 available in every new terminal automatically:**
```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

**Verify the install:**
```bash
ros2 topic list
```
You should see two topics printed: `/parameter_events` and `/rosout`. If you see those, ROS2 is working.

---

## Part 3: Installing the Go2 Simulation

We use the [`anujjain-dev/unitree-go2-ros2`](https://github.com/anujjain-dev/unitree-go2-ros2) package. It provides a Go2 robot model with working physics, walking, and sensors in Gazebo, built specifically for ROS2 Humble.

**Install its dependencies:**
```bash
sudo apt install ros-humble-gazebo-ros2-control ros-humble-xacro \
    ros-humble-robot-localization ros-humble-ros2-controllers \
    ros-humble-ros2-control ros-humble-velodyne \
    ros-humble-velodyne-gazebo-plugins ros-humble-velodyne-description \
    ros-humble-controller-manager ros-humble-twist-mux \
    ros-humble-nav2-bringup ros-humble-navigation2 -y
```

**Create a workspace and clone the simulation package:**
```bash
mkdir -p ~/go2_ws/src
cd ~/go2_ws/src
git clone https://github.com/anujjain-dev/unitree-go2-ros2.git
```

**Resolve any remaining dependencies and build:**
```bash
cd ~/go2_ws
sudo apt install -y python3-rosdep
sudo rosdep init      # only needed the very first time rosdep is used on this machine
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
```

This build can take 5–15 minutes, depending on your machine. Let it finish.

**Source the workspace:**
```bash
source ~/go2_ws/install/setup.bash
```

> 💡 You'll need to run this `source` command (and the one from Part 2) in **every new terminal window** you open. To save time, add it to your `~/.bashrc`:
> ```bash
> echo "source ~/go2_ws/install/setup.bash" >> ~/.bashrc
> ```

### Enabling the 3D LiDAR

By default, the robot model in this package has no sensors attached. This project's obstacle-avoidance node needs a 3D LiDAR (Velodyne) that publishes point cloud data.

Open this file:
```bash
nano ~/go2_ws/src/unitree-go2-ros2/robots/descriptions/go2_description/xacro/robot_VLP.xacro
```

Scroll to the bottom and make sure this line is **not commented out**:
```xml
<xacro:include filename="$(find go2_description)/xacro/velodyne.xacro"/>
```
(It should be active by default — this is just a sanity check.)

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

**Rebuild:**
```bash
cd ~/go2_ws
colcon build --symlink-install
source install/setup.bash
```

### Launching the simulation

```bash
ros2 launch go2_config gazebo_velodyne.launch.py
```

A Gazebo window should open showing the Go2 robot standing in an empty world, with a LiDAR sensor visible on its back.

**Verify the LiDAR is publishing data** — open a second terminal:
```bash
source /opt/ros/humble/setup.bash
ros2 topic list | grep velodyne
```
You should see `/velodyne_points`.

> 🛑 **Common error: missing packages.** If the launch fails with something like `package 'X' not found`, install the missing package with `sudo apt install ros-humble-<package-name>` (replacing dashes/underscores as needed) and try again. This is normal — different machines are missing different optional dependencies.

---

## Part 4: Setting Up This Project

**Clone this repository:**
```bash
cd ~
git clone https://github.com/danteturay/go2-guide-dog-ros2.git
cd go2-guide-dog-ros2
```

**Install Python dependencies:**
```bash
pip3 install ultralytics SpeechRecognition pyaudio
sudo apt install portaudio19-dev espeak -y
pip3 install "numpy<2"
```

> The `numpy<2` pin is required — newer NumPy versions break some Ultralytics/YOLO dependencies at the time of writing.

**If `pyaudio` fails to build**, install its system dependency first:
```bash
sudo apt install portaudio19-dev -y
pip3 install pyaudio
```

---

## Part 5: Running the Full System

You'll need several terminal windows open at once. In **every terminal**, run this first:
```bash
source /opt/ros/humble/setup.bash
source ~/go2_ws/install/setup.bash
```

**Terminal 1 — Launch the simulation:**
```bash
ros2 launch go2_config gazebo_velodyne.launch.py
```

**Terminal 2 — Obstacle avoidance (the safety filter):**
```bash
cd ~/go2-guide-dog-ros2
python3 src/obstacle_avoidance.py
```

**Terminal 3 — Voice feedback (the robot speaking aloud):**
```bash
cd ~/go2-guide-dog-ros2
python3 src/voice_feedback.py
```

**Terminal 4 — Control the robot**, choose one:

*Voice commands* (needs a working microphone — see Troubleshooting below):
```bash
cd ~/go2-guide-dog-ros2
python3 src/voice_commands.py
```
Then say things like "go forward", "stop", "turn left".

*Or keyboard teleop* (easier for a first test):
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r /cmd_vel:=/cmd_vel_raw
```
Use `i` (forward), `k` (stop), `j`/`l` (turn).

### Trying it out

1. In the Gazebo window, insert a simple box obstacle: use the shape tool in the top toolbar and place it a metre or two in front of the robot.
2. Drive the robot toward the box.
3. Watch Terminal 2 — you should see status messages change as you get closer:
   - `CLEAR` (more than ~2.5m away)
   - `SLOW: obstacle at 1.8m` (slowing down)
   - `STOP: obstacle at 0.9m` (stopped)
4. You should hear the robot announce the obstacle via `espeak` once it enters the SLOW or STOP zone.
5. Try reversing or turning while stopped — both should still work; only *forward* motion into the obstacle is blocked.

If all of that works, you have a fully functioning simulated demo.

---

## Testing Without the Simulation

If you just want to test the node logic without Gazebo running at all, use the fake sensor publishers:

```bash
# Terminal 1
python3 src/obstacle_avoidance.py

# Terminal 2 — fake LiDAR (edit obstacle_distance in main() to test different zones)
python3 src/fake_lidar.py

# Terminal 3 — send a movement command
ros2 topic pub /cmd_vel_raw geometry_msgs/msg/Twist "{linear: {x: 0.5}}" --rate 10

# Terminal 4 — watch the result
ros2 topic echo /robot_status
```

---

## Safety Zones Reference

| Distance to obstacle | Behaviour | Status |
|---|---|---|
| > 2.5m | Full speed | `CLEAR` |
| 1.0m – 2.5m | 30% speed (forward only) | `SLOW` |
| < 1.0m | Forward blocked (reverse/turn still allowed) | `STOP` |

## Voice Commands Reference

| You say | Robot does |
|---|---|
| "go forward" | Moves forward at 0.5 m/s |
| "go forward slowly" | Moves forward at 0.2 m/s |
| "stop" / "halt" / "wait" | Stops |
| "turn left" / "turn right" | Rotates in place |
| "go back" | Moves backward |
| "faster" / "speed up" | Moves at 0.8 m/s |

## ROS2 Topics Reference

| Topic | Type | Description |
|---|---|---|
| `/velodyne_points` | `sensor_msgs/PointCloud2` | 3D LiDAR data (simulation) |
| `/camera/rgb/image_raw` | `sensor_msgs/Image` | Camera feed |
| `/cmd_vel_raw` | `geometry_msgs/Twist` | Unfiltered movement commands |
| `/cmd_vel` | `geometry_msgs/Twist` | Safety-filtered movement commands sent to the robot |
| `/detections` | `std_msgs/String` | Objects identified by YOLO |
| `/robot_status` | `std_msgs/String` | Current safety state (`CLEAR`/`SLOW`/`STOP`) |
| `/voice_text` | `std_msgs/String` | Last recognised speech |

---

## Authors

Dante Turay — University of Southampton, 2026
Supervised by Dr Mohammad Soorati
