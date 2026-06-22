"""
Launch file for the Go2 Guide Dog system.

Starts the core safety pipeline (obstacle avoidance, YOLO detection, voice
feedback) together. Voice commands are off by default since they require a
working microphone - enable with use_voice_commands:=true, or rely on
keyboard teleop instead (run separately, since it needs an interactive
terminal):

    ros2 run teleop_twist_keyboard teleop_twist_keyboard \
        --ros-args -r /cmd_vel:=/cmd_vel_raw

Usage:
    ros2 launch guide_dog_launch.py
    ros2 launch guide_dog_launch.py use_voice_commands:=true
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_voice_commands = LaunchConfiguration('use_voice_commands')

    declare_use_voice_commands = DeclareLaunchArgument(
        'use_voice_commands',
        default_value='false',
        description='Whether to start voice_commands.py (requires a working microphone)'
    )

    # This project's nodes are plain Python scripts rather than an installed
    # ROS2 package, so they're launched with ExecuteProcess + python3 rather
    # than the usual Node action. The path is resolved relative to this
    # launch file's own location so it works regardless of where the repo
    # is cloned to.
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(pkg_dir, 'src')

    obstacle_avoidance = ExecuteProcess(
        cmd=['python3', os.path.join(src_dir, 'obstacle_avoidance.py')],
        output='screen',
        name='obstacle_avoidance'
    )

    yolo_detector = ExecuteProcess(
        cmd=['python3', os.path.join(src_dir, 'yolo_detector.py')],
        output='screen',
        name='yolo_detector'
    )

    voice_feedback = ExecuteProcess(
        cmd=['python3', os.path.join(src_dir, 'voice_feedback.py')],
        output='screen',
        name='voice_feedback'
    )

    voice_commands = ExecuteProcess(
        cmd=['python3', os.path.join(src_dir, 'voice_commands.py')],
        output='screen',
        name='voice_commands',
        condition=IfCondition(use_voice_commands)
    )

    return LaunchDescription([
        declare_use_voice_commands,
        obstacle_avoidance,
        yolo_detector,
        voice_feedback,
        voice_commands,
    ])
