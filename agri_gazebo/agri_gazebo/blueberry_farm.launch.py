from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, Command
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():

    # Package paths
    agri_gazebo_share = get_package_share_directory('agri_gazebo')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')

    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time')
    gui = LaunchConfiguration('gui')
    headless = LaunchConfiguration('headless')
    world_name = LaunchConfiguration('world_name')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true'
    )

    declare_gui = DeclareLaunchArgument(
        'gui',
        default_value='true'
    )

    declare_headless = DeclareLaunchArgument(
        'headless',
        default_value='false'
    )

    declare_world_name = DeclareLaunchArgument(
        'world_name',
        default_value=os.path.join(
            agri_gazebo_share,
            'worlds',
            'actually_empty_world.world'
        )
    )

    # Xacro -> URDF
    agriculture_urdf = Command([
        'xacro ',
        os.path.join(
            agri_gazebo_share,
            'urdf',
            'agriculture_geometry.urdf.xacro'
        )
    ])

    # Gazebo launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_name,
            'gui': gui,
            'headless': headless,
            'use_sim_time': use_sim_time
        }.items()
    )

    # Spawn model in Gazebo
    spawn_agriculture_model = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='agriculture_world_spawner',
        arguments=[
            '-entity', 'agriculture_geom',
            '-topic', 'robot_description',
            '-x', '0',
            '-y', '0',
            '-z', '0',
            '-Y', '0'
        ],
        parameters=[{
            'robot_description': agriculture_urdf,
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    return LaunchDescription([
        declare_use_sim_time,
        declare_gui,
        declare_headless,
        declare_world_name,
        gazebo,
        spawn_agriculture_model
    ])

