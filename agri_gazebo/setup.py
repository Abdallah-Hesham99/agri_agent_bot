from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'agri_gazebo'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # Required for ament indexing
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),

        # Install package.xml
        ('share/' + package_name, ['package.xml']),

        # Install launch files
        (os.path.join('share', package_name, 'launch'),
         glob('launch/*.launch.py')),

        # Install URDF / Xacro files
        (os.path.join('share', package_name, 'urdf'),
         glob('urdf/*')),

        # Install Gazebo worlds
        (os.path.join('share', package_name, 'worlds'),
         glob('worlds/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='abdallah',
    maintainer_email='abdallah.ibn.hesham98@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
