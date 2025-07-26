import numpy as np
import pathlib
path_here = pathlib.Path(__file__).parent
import sys
print(path_here.parent)
sys.path.append(str(path_here.parent))

from src.lerobot.robots.so100_follower import SO100Follower
from src.lerobot.robots.so100_follower.config_so100_follower import SO100FollowerConfig
from src.lerobot.model.kinematics import RobotKinematics


robot_kinematics = RobotKinematics(urdf_path=path_here.parent / "urdf" / "so100.urdf",
                target_frame_name="gripper")
robot_config = SO100FollowerConfig(port="/dev/ttyACM0")
robot = SO100Follower()
robot.connect()
obs = np.array(list(robot.get_observation().values()))

goal_location = np.array(np.eye(3)).reshape(3, 1)
top = np.hstack((np.identity(3), goal_location))
desired_ee_pose = np.vstack((top, np.array([0, 0, 0, 1])))

robot_kinematics.inverse_kinematics(current_joint_pos=obs, desired_ee_pose=desired_ee_pose)