from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'turtlebot3pkg'


def package_data_files(*directories):
    """Install every file below the given directories, keeping their relative layout."""
    entries = {}
    for directory in directories:
        for root, _dirs, files in os.walk(directory):
            if files:
                install_dir = os.path.join('share', package_name, root)
                entries.setdefault(install_dir, []).extend(
                    os.path.join(root, name) for name in files)
    return list(entries.items())


setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        (
            'share/' + package_name,
            ['package.xml'],
        ),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.py'),
        ),
        (
            os.path.join('share', package_name, 'worlds'),
            glob('worlds/*.sdf'),
        ),
    ] + package_data_files('config', 'rviz', 'urdf', 'models'),
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nikhil',
    maintainer_email='nikhil.bhaktha@gmail.com',
    description='TurtleBot3 Waffle in Gazebo with SLAM, Nav2 navigation and RViz',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'world_to_map = turtlebot3pkg.world_to_map:main',
        ],
    },
)
