 # TurtleBot3 ROS2 Workspace

This is a ROS2 workspace for developing, building, and running TurtleBot3 applications. It provides a workspace structure for robot simulation, navigation, teleoperation, sensor integration, and custom ROS2 nodes.

## Prerequisites

- Ubuntu Linux with a supported ROS2 distribution installed
- ROS2 desktop tools and build dependencies
- Git
- Gazebo or the simulator supported by the ROS2 distribution
- TurtleBot3 packages and a configured TurtleBot3 model

Source ROS2 before using the workspace:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
```

## Workspace layout

```text
turtlebot3_ws/
├── src/       # ROS2 packages and application source code
├── build/     # Colcon build artifacts (generated)
├── install/   # Installed packages and environment setup (generated)
└── log/       # Build and runtime logs (generated)
```

## Setup

Clone or place the project in the workspace, then install dependencies and build it:

```bash
cd ~/turtlebot3_ws
source /opt/ros/$ROS_DISRO/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

The `--symlink-install` option makes Python and other supported source changes available without copying files into the install space.

## TurtleBot3 configuration

Set the robot model before launching TurtleBot3 nodes or simulations. Use the model appropriate for the installed robot or simulation assets:

```bash
export TURTLEBOT3_MODEL=waffle
```

Common model values include `burger`, `waffle`, and `waffle_pi`. The `waffle` model was used in this case. Add the export to `~/.bashrc` if it should persist across multiple sessions.

## Running the project

Open a new terminal for each independent ROS2 process and source both environments:

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
source ~/turtlebot3_ws/install/setup.bash
```

Launch files and executable names depend on the packages included in `src/`. Discover available packages and executables with:

```bash
ros2 pkg list
ros2 pkg executables
```

To generate the RViz SLAM map from the Gazebo world, launch the map generation code:

```bash
cd ~/turtlebot3_ws
colcon build --packages-select turtlebot3pkg --symlink-install
source install/setup.bash
mkdir -p ~/maps
ros2 run turtlebot3pkg world_to_map $(ros2 pkg prefix turtlebot3pkg)/share/turtlebot3pkg/worlds/turtlebot3World.sdf --output ~/maps/tb3_ground_truth_map
```

To launch autonomous navigation from the generated map, launch the navigation code:

```bash
cd ~/turtlebot3_ws
source install/setup.bash

ros2 launch turtlebot3pkg turtlebot3_navigation.launch.py map:=~/maps/tb3_ground_truth_map.yaml
```

## Rebuilding and cleaning

Rebuild after changing source files or package metadata:

```bash
colcon build --symlink-install
source install/setup.bash
```

If stale build artifacts cause errors, clean the generated directories and rebuild:

```bash
rm -rf build install log
colcon build --symlink-install
source install/setup.bash
```

## Troubleshooting

- **Package not found:** source the ROS2 installation and workspace setup files in the current terminal.
- **Missing dependencies:** run `rosdep install --from-paths src --ignore-src -r -y` and rebuild.
- **No robot topics:** verify that the required launch process is running and that ROS2 discovery is working across the network.
- **Simulator fails to start:** check that the simulator and TurtleBot3 packages match the installed ROS2 distribution.

## Development guidelines

- Keep each ROS2 package focused and document its nodes, parameters, topics, services, and actions.
- Use descriptive names and consistent coordinate-frame conventions.
- Test changes in simulation before deploying them to hardware.
- Keep generated build artifacts out of version control.
- Record the ROS2 distribution, TurtleBot3 model, and launch command used for reproducibility.

## License

