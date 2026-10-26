# Copyright 2026 nikhil
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Launch TurtleBot3 Waffle SLAM or saved-map autonomous navigation in Gazebo with RViz.

Starts:
  * Gazebo (gz-sim) with the turtlebot3World.sdf world
  * robot_state_publisher with the TurtleBot3 Waffle URDF
  * the Waffle model (DiffDrive, IMU and LiDAR plugins) spawned into Gazebo
    * ros_gz_bridge for clock, cmd_vel, odom, tf, joint_states, scan and imu
    * Nav2 bringup with optional slam_toolbox mapping
  * RViz2 preconfigured for SLAM and navigation

Examples
--------
    ros2 launch turtlebot3pkg turtlebot3_slam_nav.launch.py
    ros2 launch turtlebot3pkg turtlebot3_slam_nav.launch.py slam:=false map:=maps/tb3_map.yaml
  ros2 launch turtlebot3pkg turtlebot3_slam_nav.launch.py headless:=true use_rviz:=false

"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

ROBOT_NAME = 'turtlebot3_waffle'
SPAWN_DELAY_S = 3.0      # let gz-sim start before the robot is spawned
NAV2_START_DELAY_S = 8.0  # let the robot and its TF tree come up before Nav2


def generate_launch_description():
    # Strip Snap paths from LD_LIBRARY_PATH to avoid glibc symbol conflicts
    # (e.g. symbol lookup error from /snap/core20/.../libpthread.so.0)
    # when launching from VS Code installed as a Snap package.
    if 'LD_LIBRARY_PATH' in os.environ:
        cleaned_ld_path = ':'.join(
            p for p in os.environ['LD_LIBRARY_PATH'].split(':') if '/snap/' not in p
        )
        os.environ['LD_LIBRARY_PATH'] = cleaned_ld_path

    pkg_share = get_package_share_directory('turtlebot3pkg')

    default_world = os.path.join(pkg_share, 'worlds', 'turtlebot3World.sdf')
    robot_sdf = os.path.join(pkg_share, 'models', 'turtlebot3_waffle', 'model.sdf')
    urdf_file = os.path.join(pkg_share, 'urdf', 'turtlebot3_waffle.urdf')
    bridge_config = os.path.join(pkg_share, 'config', 'turtlebot3_waffle_bridge.yaml')
    nav2_params = os.path.join(pkg_share, 'config', 'nav2_slam_params.yaml')
    default_rviz_config = os.path.join(pkg_share, 'rviz', 'tb3_slam_nav.rviz')

    with open(urdf_file, 'r') as urdf:
        robot_description = urdf.read()

    # Launch arguments
    world = LaunchConfiguration('world')
    map_yaml_file = LaunchConfiguration('map')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('use_rviz')
    slam = LaunchConfiguration('slam')
    rviz_config = LaunchConfiguration('rviz_config')

    declare_args = [
        DeclareLaunchArgument(
            'world', default_value=default_world,
            description='Full path to the Gazebo world SDF file'),
        DeclareLaunchArgument(
            'map', default_value='',
            description='Full path to map yaml file when slam is false'),
        DeclareLaunchArgument(
            'x_pose', default_value='0.0',
            description='Initial x position of the robot in the world (m)'),
        DeclareLaunchArgument(
            'y_pose', default_value='0.0',
            description='Initial y position of the robot in the world (m)'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use the Gazebo simulation clock'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='Run the Gazebo server only, without the GUI'),
        DeclareLaunchArgument(
            'use_rviz', default_value='true',
            description='Start RViz2 with the SLAM and navigation configuration'),
        DeclareLaunchArgument(
            'slam', default_value='True',
            description='Build a map online with slam_toolbox; set false to navigate a saved map'),
        DeclareLaunchArgument(
            'rviz_config', default_value=default_rviz_config,
            description='RViz configuration file'),
    ]

    # Gazebo: let gz-sim find the robot's meshes under the package's models/ folder
    set_gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH', os.path.join(pkg_share, 'models'))

    gz_sim_launch = PathJoinSubstitution(
        [FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'])

    gz_sim_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={'gz_args': ['-r ', world]}.items(),
        condition=UnlessCondition(headless),
    )

    gz_sim_server_only = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_sim_launch),
        launch_arguments={'gz_args': ['-r -s ', world]}.items(),
        condition=IfCondition(headless),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_description,
        }],
    )

    spawn_robot = TimerAction(
        period=SPAWN_DELAY_S,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                name='spawn_turtlebot3',
                output='screen',
                arguments=[
                    '-name', ROBOT_NAME,
                    '-file', robot_sdf,
                    '-x', x_pose,
                    '-y', y_pose,
                    '-z', '0.01',
                ],
            ),
        ],
    )

    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        parameters=[{'config_file': bridge_config}],
    )

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare('nav2_bringup'), 'launch', 'bringup_launch.py'])),
        launch_arguments={
            'slam': slam,
            'map': map_yaml_file,
            'use_sim_time': use_sim_time,
            'params_file': nav2_params,
            'autostart': 'True',
        }.items(),
    )

    delayed_nav2 = TimerAction(period=NAV2_START_DELAY_S, actions=[nav2_bringup])

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(declare_args + [
        set_gz_resource_path,
        gz_sim_gui,
        gz_sim_server_only,
        robot_state_publisher,
        gz_bridge,
        spawn_robot,
        delayed_nav2,
        rviz,
    ])
