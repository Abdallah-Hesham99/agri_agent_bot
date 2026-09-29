#!/usr/bin/env python3
"""Spawn the Clearpath Husky into the farm_lite orchard world.

Robot description is generated from ~/clearpath/robot.yaml
(Husky A300 + UR10e + Robotiq + VLP16 + ZED + D435, namespace a300_0000).

Usage:
  ros2 launch agri_agent_bot spawn_husky.launch.py
  ros2 launch agri_agent_bot spawn_husky.launch.py x:=-6.0 y:=12.0 yaw:=0.0
  # drive it (namespace from robot.yaml):
  ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r __ns:=/a300_0000
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    farm_models = "/home/abdallah/farm_env/trial_2/farm_world/models"
    farm_world = "/home/abdallah/farm_env/trial_2/farm_world/worlds/farm_lite.world"

    # Resolve all sourced ROS packages so Gazebo finds clearpath meshes etc.
    packages_paths = [os.path.join(p, "share")
                      for p in os.getenv("AMENT_PREFIX_PATH", "").split(":") if p]
    gz_resource = SetEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=[farm_models + ":"] + [p + ":" for p in packages_paths],
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"
            ])
        ),
        launch_arguments={"gz_args": "-r " + farm_world}.items(),
    )

    # /clock bridge (ros_gz_sim's gz_sim.launch.py ships none; without it
    # use_sim_time nodes like controller_manager starve with "No clock received").
    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="clock_bridge",
        output="screen",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
    )

    # Pose TF bridge: gz model poses -> ROS TFMessage for training/RL consumers.
    pose_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="pose_bridge",
        output="screen",
        arguments=["/world/farm/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V"],
        remappings=[("/world/farm/pose/info", "/farm/pose_info")],
    )

    # Clearpath spawn pipeline: generates URDF/controllers from robot.yaml,
    # publishes robot_description, spawns into the running world named 'farm'.
    robot_spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("clearpath_gz"), "launch", "robot_spawn.launch.py"
            ])
        ),
        launch_arguments={
            "world": "farm",
            "setup_path": LaunchConfiguration("setup_path"),
            "use_sim_time": "true",
            "generate": "true",
            "rviz": LaunchConfiguration("rviz"),
            "x": LaunchConfiguration("x"),
            "y": LaunchConfiguration("y"),
            "z": LaunchConfiguration("z"),
            "yaw": LaunchConfiguration("yaw"),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("setup_path", default_value="/home/abdallah/clearpath",
                              description="Clearpath setup path (robot.yaml lives here)"),
        DeclareLaunchArgument("rviz", default_value="false"),
        # Aisle-0 entrance, facing +X down the aisle, orchard row on the right.
        DeclareLaunchArgument("x", default_value="-6.0"),
        DeclareLaunchArgument("y", default_value="4.0"),
        DeclareLaunchArgument("z", default_value="0.3"),
        DeclareLaunchArgument("yaw", default_value="0.0"),
        gz_resource,
        clock_bridge,
        pose_bridge,
        gz_sim,
        robot_spawn,
    ])
