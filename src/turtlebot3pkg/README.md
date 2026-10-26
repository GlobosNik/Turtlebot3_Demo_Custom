# turtlebot3pkg

TurtleBot3 Waffle in a Gazebo world with **SLAM (slam_toolbox)**, **autonomous navigation (Nav2)**
and **RViz2**.

## Contents

| Path | Purpose |
|---|---|
| `launch/turtlebot3_slam_nav.launch.py` | Common Gazebo + robot + bridge + RViz launch with SLAM/navigation switch |
| `launch/turtlebot3_mapping.launch.py` | SLAM launch for mapping with keyboard teleop |
| `launch/turtlebot3_navigation.launch.py` | Saved-map Nav2 launch for RViz goal-point navigation |
| `launch/gazeboLaunch.py` | Gazebo with the world only (no robot) |
| `worlds/turtlebot3World.sdf` | World with ground plane and obstacle cylinders (robot is spawned by the launch file) |
| `models/turtlebot3_waffle/` | TurtleBot3 Waffle model: DiffDrive, IMU, 360° LiDAR, camera |
| `models/turtlebot3_common/` | Mesh files used by the Waffle model |
| `urdf/turtlebot3_waffle.urdf` | Robot description for robot_state_publisher and RViz |
| `config/nav2_slam_params.yaml` | Nav2 parameters plus the `slam_toolbox` section |
| `config/turtlebot3_waffle_bridge.yaml` | Gazebo ↔ ROS 2 topic bridge |
| `rviz/tb3_slam_nav.rviz` | RViz2 layout for the map, scan, costmaps, plans and the Nav2 panel |

Robot model, meshes, URDF, RViz layout and the navigation parameters are adapted from
[ROBOTIS-GIT/turtlebot3](https://github.com/ROBOTIS-GIT/turtlebot3) and
[ROBOTIS-GIT/turtlebot3_simulations](https://github.com/ROBOTIS-GIT/turtlebot3_simulations)
(Apache-2.0). The slam_toolbox section follows
[SteveMacenski/slam_toolbox](https://github.com/SteveMacenski/slam_toolbox) (LGPL-2.1).

## Requirements

- ROS 2 Humble, built with colcon
- Gazebo (gz-sim) with `ros_gz_sim` and `ros_gz_bridge`. The world and the launch files use gz-sim
  (Harmonic/Garden-style) plugin names, so `ros_gz` must be built against that Gazebo version.
  The apt `ros-humble-ros-gz` packages are built for Gazebo Fortress and will not load this world.

```bash
sudo apt install ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-slam-toolbox \
                 ros-humble-robot-state-publisher ros-humble-rviz2
# ros_gz_sim / ros_gz_bridge: build from source against your gz-sim version
```

## Build

```bash
# Run these commands from the workspace root.
colcon build --symlink-install
source install/setup.bash
```

## Run: SLAM and navigation

```bash
ros2 launch turtlebot3pkg turtlebot3_slam_nav.launch.py
```

Launch arguments:

| Argument | Default | Description |
|---|---|---|
| `world` | `worlds/turtlebot3World.sdf` | World file to load |
| `x_pose`, `y_pose` | `0.0`, `0.0` | Spawn position of the robot (m) |
| `use_sim_time` | `true` | Use the Gazebo clock |
| `headless` | `false` | Run the gz-sim server only (no GUI) |
| `use_rviz` | `true` | Start RViz2 |
| `slam` | `true` | Build a map online; set `false` when loading a saved map |

Examples:

```bash
ros2 launch turtlebot3pkg turtlebot3_slam_nav.launch.py x_pose:=-1.0 y_pose:=0.5
ros2 launch turtlebot3pkg turtlebot3_slam_nav.launch.py headless:=true use_rviz:=false
```

## Mapping and autonomous navigation

### Generate a map directly from the SDF

For this world, a ground-truth occupancy map can be generated from the collision geometry without
driving the robot:

```bash
source install/setup.bash
mkdir -p maps
ros2 run turtlebot3pkg world_to_map \
  $(ros2 pkg prefix turtlebot3pkg)/share/turtlebot3pkg/worlds/turtlebot3World.sdf \
  --output maps/tb3_ground_truth_map
```

Create the output directory first with `mkdir -p maps`. This creates
`maps/tb3_ground_truth_map.pgm` and `maps/tb3_ground_truth_map.yaml`. Load the YAML with the
saved-map navigation launch. Because this map comes from the simulator's world coordinates rather
than SLAM, use RViz **2D Pose Estimate** to align the robot with the map before sending a goal.
The generator currently rasterizes cylinder and box collision geometry; it does not infer arbitrary
mesh interiors or sensor noise.

1. **Start mapping** in the workspace terminal. RViz displays the live `/map` from `slam_toolbox`:
  ```bash
  ros2 launch turtlebot3pkg turtlebot3_mapping.launch.py
  ```
2. **Drive the robot** from a second terminal. Keep this terminal focused while pressing the keys:
  ```bash
  source install/setup.bash
  ros2 run teleop_twist_keyboard teleop_twist_keyboard
  ```
  Cover the accessible space slowly and include turns and loop closures so the scan data overlaps.
3. **Save the completed map** before stopping the mapping launch:
  ```bash
  mkdir -p maps
  ros2 run nav2_map_server map_saver_cli -f maps/tb3_map
  ```
4. Stop the mapping launch with `Ctrl+C`, then start saved-map navigation:
  ```bash
  ros2 launch turtlebot3pkg turtlebot3_navigation.launch.py map:=maps/tb3_map.yaml
  ```
5. In RViz2, use **2D Pose Estimate** if the robot pose needs correcting, then choose **Nav2 Goal**
  and click-drag the desired goal pose on the map. Nav2 plans and drives to that pose.

The common launch can also be used directly: leave `slam:=true` for mapping, or pass
`slam:=false map:=maps/tb3_map.yaml` for saved-map navigation.

## Topics and frames

- Frames: `map` → `odom` (slam_toolbox) → `base_footprint` (DiffDrive odometry) → `base_link`
  (URDF) → `base_scan` (LiDAR)
- Topics: `/cmd_vel` (in), `/odom`, `/scan`, `/imu`, `/joint_states`, `/tf`, `/clock`, `/map`
  (out)

## Notes

- Only the Waffle is supported. The Burger and Waffle Pi are not included.
- Camera data is not bridged into ROS. The camera is in the model but navigation does not use it.
