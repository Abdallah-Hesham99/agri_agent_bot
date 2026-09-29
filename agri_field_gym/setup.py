from setuptools import find_packages, setup

package_name = 'agri_field_gym'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='abdallah',
    maintainer_email='abdallah@example.com',
    description='Gymnasium + SB3 navigation training for the Husky in farm_lite.',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'train = agri_field_gym.train:main',
        ],
    },
)
