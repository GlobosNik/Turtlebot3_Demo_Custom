from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import (
    PythonLaunchDescriptionSource,
)
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    world_file = PathJoinSubstitution([
        FindPackageShare('turtlebot3pkg'),
        'worlds',
        'turtlebot3World.sdf',
    ])

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py',
            ])
        ),
        launch_arguments={
            'gz_args': ['-r ', world_file],
        }.items(),
    )

    return LaunchDescription([
        gazebo_launch,
    ])
