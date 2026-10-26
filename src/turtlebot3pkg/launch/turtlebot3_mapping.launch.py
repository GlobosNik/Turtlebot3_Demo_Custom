"""Launch Gazebo, online SLAM, RViz and the TurtleBot3 sensors."""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    main_launch = PathJoinSubstitution([
        FindPackageShare('turtlebot3pkg'),
        'launch',
        'turtlebot3_slam_nav.launch.py',
    ])

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(main_launch),
            launch_arguments={'slam': 'True'}.items(),
        ),
    ])
