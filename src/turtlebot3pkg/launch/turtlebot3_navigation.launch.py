"""Launch Gazebo, RViz and Nav2 against a previously saved map."""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    main_launch = PathJoinSubstitution([
        FindPackageShare('turtlebot3pkg'),
        'launch',
        'turtlebot3_slam_nav.launch.py',
    ])

    def include_navigation(context):
        map_file = os.path.abspath(
            os.path.expanduser(LaunchConfiguration('map').perform(context)))
        return [IncludeLaunchDescription(
            PythonLaunchDescriptionSource(main_launch),
            launch_arguments={
                'slam': 'False',
                'map': map_file,
                'rviz_config': PathJoinSubstitution([
                    FindPackageShare('turtlebot3pkg'),
                    'rviz',
                    'tb3_navigation.rviz',
                ]),
            }.items(),
        )]

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            description='Full path to the saved map YAML file',
        ),
        OpaqueFunction(function=include_navigation),
    ])
