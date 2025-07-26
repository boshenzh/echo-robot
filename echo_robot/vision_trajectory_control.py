#!/usr/bin/env python3
"""
Integrated Vision-Based Robot Control with Trajectory Planning
集成视觉导航和轨迹规划的机器人控制系统

This module combines YOLO detection, camera calibration, and trajectory planning
to autonomously push bottles using the LeRobot SO-100 arm.
"""

import time
import logging
import traceback
import math
import cv2
import numpy as np
from ultralytics import YOLO
from trajectory_planner import TrajectoryPlanner

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 关节校准系数 (from your lerobot_yolo.py)
JOINT_CALIBRATION = [
    ['shoulder_pan', 6.0, 1.0],      
    ['shoulder_lift', 2.0, 0.97],     
    ['elbow_flex', 0.0, 1.05],        
    ['wrist_flex', 0.0, 0.94],        
    ['wrist_roll', 0.0, 0.5],        
    ['gripper', 0.0, 1.0],           
]

def apply_joint_calibration(joint_name, raw_position):
    """应用关节校准系数"""
    for joint_cal in JOINT_CALIBRATION:
        if joint_cal[0] == joint_name:
            offset = joint_cal[1]
            scale = joint_cal[2]
            calibrated_position = (raw_position - offset) * scale
            return calibrated_position
    return raw_position

class VisionTrajectoryController:
    def __init__(self, camera_id=0):
        """
        Initialize vision-based trajectory controller
        初始化视觉轨迹控制器
        """
        self.camera_id = camera_id
        self.trajectory_planner = TrajectoryPlanner()
        self.model = YOLO("yolov8n.pt")
        self.cap = None
        self.robot = None
        self.keyboard = None
        
        # Control parameters
        self.control_freq = 50  # Hz
        self.kp = 0.5  # Proportional gain
        
        print("🚀 Vision Trajectory Controller initialized")
    
    def initialize_camera(self):
        """Initialize camera with error handling"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                raise Exception(f"Cannot open camera {self.camera_id}")
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print(f"📷 Camera {self.camera_id} initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            return False
    
    def initialize_robot(self, port="/dev/ttyACM0"):
        """Initialize robot connection"""
        try:
            from lerobot.robots.so100_follower import SO100Follower, SO100FollowerConfig
            from lerobot.teleoperators.keyboard import KeyboardTeleop, KeyboardTeleopConfig
            
            # Configure robot
            robot_config = SO100FollowerConfig(port=port)
            self.robot = SO100Follower(robot_config)
            
            # Configure keyboard for emergency stop
            keyboard_config = KeyboardTeleopConfig()
            self.keyboard = KeyboardTeleop(keyboard_config)
            
            # Connect devices
            self.robot.connect()
            self.keyboard.connect()
            
            print(f"🤖 Robot connected to {port}")
            return True
        except Exception as e:
            print(f"❌ Robot initialization failed: {e}")
            return False
    
    def move_to_zero_position(self, duration=3.0):
        """Move robot to zero position using P control"""
        if not self.robot:
            print("❌ Robot not initialized")
            return False
        
        print("🏠 Moving robot to zero position...")
        
        zero_positions = {
            'shoulder_pan': 0.0,
            'shoulder_lift': 0.0,
            'elbow_flex': 0.0,
            'wrist_flex': 0.0,
            'wrist_roll': 0.0,
            'gripper': 0.0
        }
        
        total_steps = int(duration * self.control_freq)
        step_time = 1.0 / self.control_freq
        
        for step in range(total_steps):
            # Get current robot state
            current_obs = self.robot.get_observation()
            current_positions = {}
            for key, value in current_obs.items():
                if key.endswith('.pos'):
                    motor_name = key.removesuffix('.pos')
                    calibrated_value = apply_joint_calibration(motor_name, value)
                    current_positions[motor_name] = calibrated_value
            
            # P control calculation
            robot_action = {}
            for joint_name, target_pos in zero_positions.items():
                if joint_name in current_positions:
                    current_pos = current_positions[joint_name]
                    error = target_pos - current_pos
                    control_output = self.kp * error
                    new_position = current_pos + control_output
                    robot_action[f"{joint_name}.pos"] = new_position
            
            if robot_action:
                self.robot.send_action(robot_action)
            
            time.sleep(step_time)
        
        print("✅ Robot moved to zero position")
        return True
    
    def execute_trajectory_waypoint(self, waypoint, duration=2.0):
        """
        Execute a single trajectory waypoint using P control
        执行单个轨迹点
        """
        if not self.robot:
            print("❌ Robot not initialized")
            return False
        
        target_positions = waypoint['joint_angles']
        total_steps = int(duration * self.control_freq)
        step_time = 1.0 / self.control_freq
        
        print(f"🎯 Executing waypoint: {waypoint['name']} ({waypoint['description']})")
        print(f"   Target: pan={target_positions['shoulder_pan']:.1f}°, "
              f"lift={target_positions['shoulder_lift']:.1f}°, "
              f"flex={target_positions['elbow_flex']:.1f}°")
        
        for step in range(total_steps):
            # Check for emergency stop
            if self.keyboard:
                keyboard_action = self.keyboard.get_action()
                if keyboard_action and 'x' in keyboard_action:
                    print("⛔ Emergency stop detected!")
                    return False
            
            # Get current robot state
            current_obs = self.robot.get_observation()
            current_positions = {}
            for key, value in current_obs.items():
                if key.endswith('.pos'):
                    motor_name = key.removesuffix('.pos')
                    calibrated_value = apply_joint_calibration(motor_name, value)
                    current_positions[motor_name] = calibrated_value
            
            # P control calculation
            robot_action = {}
            total_error = 0
            for joint_name, target_pos in target_positions.items():
                if joint_name in current_positions:
                    current_pos = current_positions[joint_name]
                    error = target_pos - current_pos
                    total_error += abs(error)
                    
                    control_output = self.kp * error
                    new_position = current_pos + control_output
                    robot_action[f"{joint_name}.pos"] = new_position
            
            if robot_action:
                self.robot.send_action(robot_action)
            
            # Check if waypoint reached
            if total_error < 2.0:  # If total error < 2 degrees
                print(f"✅ Waypoint {waypoint['name']} reached")
                break
            
            time.sleep(step_time)
        
        return True
    
    def execute_trajectory(self, trajectory):
        """
        Execute complete trajectory
        执行完整轨迹
        """
        print(f"\n🎬 Executing trajectory with {len(trajectory)} waypoints")
        print("="*60)
        
        for i, waypoint in enumerate(trajectory):
            print(f"\nStep {i+1}/{len(trajectory)}: {waypoint['name']}")
            
            success = self.execute_trajectory_waypoint(waypoint, waypoint['duration'])
            if not success:
                print(f"❌ Failed to execute waypoint {waypoint['name']}")
                return False
            
            # Small pause between waypoints
            time.sleep(0.5)
        
        print("\n🎉 Trajectory execution completed successfully!")
        return True
    
    def detect_and_plan_trajectory(self):
        """
        Detect bottles and plan trajectory for the best target
        检测瓶子并规划最佳目标的轨迹
        """
        if not self.cap:
            print("❌ Camera not initialized")
            return None
        
        # Capture frame
        ret, frame = self.cap.read()
        if not ret:
            print("❌ Failed to capture camera frame")
            return None
        
        # Detect bottles
        bottles = self.trajectory_planner.detect_bottles(frame, self.model)
        
        if not bottles:
            print("🔍 No bottles detected in workspace")
            cv2.imshow("Detection", frame)
            cv2.waitKey(1)
            return None
        
        # Select the closest bottle (or implement other selection criteria)
        target_bottle = min(bottles, key=lambda b: math.sqrt(b['world_x']**2 + b['world_y']**2))
        
        print(f"🎯 Selected target bottle at ({target_bottle['world_x']:.3f}, "
              f"{target_bottle['world_y']:.3f}) with confidence {target_bottle['confidence']:.2f}")
        
        # Draw detection on frame
        annotated_frame = self.model(frame)[0].plot()
        
        # Highlight selected bottle
        x1, y1, x2, y2 = target_bottle['bbox']
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
        cv2.putText(annotated_frame, "TARGET", (x1, y1-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("Bottle Detection", annotated_frame)
        cv2.waitKey(1)
        
        # Generate trajectory
        push_direction = math.radians(0)  # Push in +X direction
        trajectory = self.trajectory_planner.generate_push_trajectory(target_bottle, push_direction)
        
        # Apply smoothing
        trajectory = self.trajectory_planner.smooth_trajectory(trajectory)
        
        return trajectory
    
    def run_autonomous_mode(self):
        """
        Run autonomous bottle pushing mode
        运行自主推瓶模式
        """
        print("\n🚀 Starting autonomous bottle pushing mode")
        print("Press 'x' for emergency stop, 'q' to quit detection window")
        print("="*60)
        
        while True:
            try:
                # Detect bottles and plan trajectory
                trajectory = self.detect_and_plan_trajectory()
                
                if trajectory:
                    # Show trajectory visualization
                    self.trajectory_planner.visualize_trajectory(trajectory, save_plot=False)
                    
                    # Ask for confirmation
                    print("\n🤔 Execute this trajectory? (y/n/q): ", end="")
                    response = input().strip().lower()
                    
                    if response == 'y':
                        # Execute trajectory
                        success = self.execute_trajectory(trajectory)
                        if success:
                            print("🎉 Bottle push completed successfully!")
                        else:
                            print("❌ Trajectory execution failed")
                    elif response == 'q':
                        break
                    else:
                        print("⏭️  Skipping trajectory execution")
                
                # Check for quit
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
                time.sleep(1)  # Pause before next detection
                
            except KeyboardInterrupt:
                print("\n⛔ User interrupted")
                break
            except Exception as e:
                print(f"❌ Error in autonomous mode: {e}")
                traceback.print_exc()
                break
        
        print("🏁 Autonomous mode stopped")
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        if self.robot:
            self.robot.disconnect()
        if self.keyboard:
            self.keyboard.disconnect()
        cv2.destroyAllWindows()
        print("🧹 Resources cleaned up")

def main():
    """Main function"""
    print("Echo Robot Vision-Based Trajectory Control")
    print("="*50)
    
    controller = None
    
    try:
        # Get robot port
        port = input("请输入SO100机器人的USB端口 (例如: /dev/ttyACM0): ").strip()
        if not port:
            port = "/dev/ttyACM0"
        
        # Get camera ID
        camera_input = input("请输入摄像头ID (默认: 0): ").strip()
        camera_id = int(camera_input) if camera_input else 0
        
        # Initialize controller
        controller = VisionTrajectoryController(camera_id)
        
        # Initialize camera
        if not controller.initialize_camera():
            return
        
        # Initialize robot
        if not controller.initialize_robot(port):
            return
        
        # Ask for calibration
        while True:
            calibrate_choice = input("是否重新校准机器人? (y/n): ").strip().lower()
            if calibrate_choice in ['y', 'yes', '是']:
                print("开始重新校准...")
                controller.robot.calibrate()
                print("校准完成！")
                break
            elif calibrate_choice in ['n', 'no', '否']:
                print("使用之前的校准文件")
                break
            else:
                print("请输入 y 或 n")
        
        # Move to zero position
        controller.move_to_zero_position()
        
        print("\n🎮 控制模式选择:")
        print("1. 自主推瓶模式 (检测瓶子并自动生成轨迹)")
        print("2. 手动轨迹测试 (使用模拟瓶子位置)")
        
        mode = input("请选择模式 (1/2): ").strip()
        
        if mode == "1":
            controller.run_autonomous_mode()
        elif mode == "2":
            # Manual test mode
            mock_bottle = {
                'world_x': 0.18,
                'world_y': 0.05,
                'world_z': 0.0,
                'confidence': 0.85
            }
            
            trajectory = controller.trajectory_planner.generate_push_trajectory(mock_bottle)
            trajectory = controller.trajectory_planner.smooth_trajectory(trajectory)
            
            controller.trajectory_planner.visualize_trajectory(trajectory)
            
            response = input("执行测试轨迹? (y/n): ").strip().lower()
            if response == 'y':
                controller.execute_trajectory(trajectory)
        else:
            print("无效选择")
        
    except Exception as e:
        print(f"程序执行失败: {e}")
        traceback.print_exc()
    finally:
        if controller:
            controller.cleanup()

if __name__ == "__main__":
    main()
