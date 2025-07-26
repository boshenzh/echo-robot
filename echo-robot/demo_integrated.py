#!/usr/bin/env python3
"""
Integrated Demo Script for Robot Arm with YOLO Detection and Audio
集成演示脚本：机器人手臂 + YOLO检测 + 音频反馈

This script                # Quick calibration check
                calibrate = input("Calibrate robot? (y/n): ").strip().lower()
                if calibrate in ['y', 'yes']:
                    print("🔧 Calibrating robot...")
                    self.robot.calibrate()
                    print("✅ Calibration completed!")
                
                # Move to initial safe position
                print("🏠 Moving to initial safe position...")
                self.move_to_safe_start_position()
                
            except Exception as e:
                print(f"❌ Robot connection failed: {e}")
                raise RuntimeError(f"❌ Failed to connect to robot at {port}. Check connection and port.")
        else:
            print("🎮 Running in simulation mode")
    
    def move_to_safe_start_position(self):
        """移动到安全的起始位置"""
        try:
            # 计算安全起始位置的关节角度
            safe_x, safe_y = 0.0, 0.16
            joint2, joint3 = self.inverse_kinematics(safe_x, safe_y)
            
            print(f"🔧 Moving to safe start: x={safe_x}, y={safe_y}")
            print(f"   Joint angles: shoulder={joint2:.1f}°, elbow={joint3:.1f}°")
            
            robot_action = {
                'shoulder_lift.pos': joint2,
                'elbow_flex.pos': joint3
            }
            
            if not self.simulation_mode:
                self.robot.send_action(robot_action)
                time.sleep(2.0)  # 等待到达位置
            
            self.current_x = safe_x
            self.current_y = safe_y
            print("✅ Robot moved to safe start position")
            
        except Exception as e:
            print(f"⚠️  Failed to move to safe start position: {e}")
            print("   Continuing with current position..."). Camera visualization with YOLO bottle detection (from test_camera_yolo.py)
2. Robot trajectory movement: forward/backward push (from lerobot_yolo.py)
3. Audio feedback before robot arm starts movement

Dependencies:
- pip install pygame (for audio)
或者使用系统音频：
- sudo apt-get install alsa-utils (for aplay)
"""

import cv2
import time
import math
import numpy as np
import threading
import logging
import traceback
import os
import sys
from ultralytics import YOLO

# Audio imports - try multiple options
try:
    import pygame
    AUDIO_METHOD = "pygame"
    print("🔊 Using pygame for audio")
except ImportError:
    AUDIO_METHOD = "system"
    print("🔊 Using system commands for audio")

# Robot imports (only if available)
try:
    from lerobot.robots.so100_follower import SO100Follower, SO100FollowerConfig
    ROBOT_AVAILABLE = True
    print("🤖 Robot modules available")
except ImportError:
    ROBOT_AVAILABLE = False
    print("⚠️  Robot modules not available - simulation mode only")

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioManager:
    """音频管理器"""
    
    def __init__(self):
        self.audio_enabled = True
        if AUDIO_METHOD == "pygame":
            try:
                pygame.mixer.init()
                print("✅ Pygame audio initialized")
            except Exception as e:
                print(f"❌ Pygame audio initialization failed: {e}")
                self.audio_enabled = False
    
    def play_alert_sound(self, sound_type="push"):
        """播放警告音"""
        if not self.audio_enabled:
            return
        
        try:
            if AUDIO_METHOD == "pygame":
                self._play_pygame_sound(sound_type)
            else:
                self._play_system_sound(sound_type)
        except Exception as e:
            print(f"❌ Audio playback failed: {e}")
    
    def _play_pygame_sound(self, sound_type):
        """使用pygame播放声音"""
        # 生成简单的蜂鸣音
        frequency = 800 if sound_type == "push" else 600
        duration = 0.5
        sample_rate = 22050
        
        # 生成正弦波
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2))
        
        for i in range(frames):
            wave = np.sin(2 * np.pi * frequency * i / sample_rate)
            arr[i] = [wave, wave]
        
        # 转换为pygame格式并播放
        sound_array = (arr * 32767).astype(np.int16)
        sound = pygame.sndarray.make_sound(sound_array)
        sound.play()
        time.sleep(duration)
    
    def _play_system_sound(self, sound_type):
        """使用系统命令播放声音"""
        if sound_type == "push":
            # 高音调警告
            os.system("speaker-test -t sine -f 800 -l 1 > /dev/null 2>&1 &")
        else:
            # 低音调提示
            os.system("speaker-test -t sine -f 600 -l 1 > /dev/null 2>&1 &")
        time.sleep(0.1)
    
    def cleanup(self):
        """清理音频资源"""
        if AUDIO_METHOD == "pygame":
            try:
                pygame.mixer.quit()
            except:
                pass

class RobotController:
    """机器人控制器"""
    
    def __init__(self, port="/dev/ttyACM1", simulation_mode=False):
        self.simulation_mode = simulation_mode or not ROBOT_AVAILABLE
        self.robot = None
        self.current_x = 0.0
        self.current_y = 0.06  # 初始y位置 - 在机器人工作空间内
        self.is_moving = False
        
        if not ROBOT_AVAILABLE:
            raise RuntimeError("❌ Robot modules not available! Please install lerobot package.")
        
        if not self.simulation_mode:
            try:
                print(f"🔌 Connecting to robot at {port}...")
                robot_config = SO100FollowerConfig(port=port)
                self.robot = SO100Follower(robot_config)
                self.robot.connect()
                print("✅ Robot connected successfully!")
                
                # Quick calibration check
                calibrate = input("Calibrate robot? (y/n): ").strip().lower()
                if calibrate in ['y', 'yes']:
                    print("� Calibrating robot...")
                    self.robot.calibrate()
                    print("✅ Calibration completed!")
                
            except Exception as e:
                print(f"❌ Robot connection failed: {e}")
                raise RuntimeError(f"❌ Failed to connect to robot at {port}. Check connection and port.")
        else:
            print("🎮 Running in simulation mode")
    
    def inverse_kinematics(self, x, y, l1=0.1159, l2=0.1350):
        """
        Calculate inverse kinematics for a 2-link robotic arm
        从lerobot_yolo.py复制的逆运动学计算
        """
        # Calculate joint2 and joint3 offsets in theta1 and theta2
        theta1_offset = math.atan2(0.028, 0.11257)  # theta1 offset when joint2=0
        theta2_offset = math.atan2(0.0052, 0.1349) + theta1_offset  # theta2 offset when joint3=0
        
        # Calculate distance from origin to target point
        r = math.sqrt(x**2 + y**2)
        r_max = l1 + l2  # Maximum reachable distance
        
        # If target point is beyond maximum workspace, scale it to the boundary
        if r > r_max:
            scale_factor = r_max / r
            x *= scale_factor
            y *= scale_factor
            r = r_max
        
        # If target point is less than minimum workspace (|l1-l2|), scale it
        r_min = abs(l1 - l2)
        if r < r_min and r > 0:
            scale_factor = r_min / r
            x *= scale_factor
            y *= scale_factor
            r = r_min
        
        # Use law of cosines to calculate theta2
        cos_theta2 = -(r**2 - l1**2 - l2**2) / (2 * l1 * l2)
        
        # Calculate theta2 (elbow angle)
        theta2 = math.pi - math.acos(cos_theta2)
        
        # Calculate theta1 (shoulder angle)
        beta = math.atan2(y, x)
        gamma = math.atan2(l2 * math.sin(theta2), l1 + l2 * math.cos(theta2))
        theta1 = beta + gamma
        
        # Convert theta1 and theta2 to joint2 and joint3 angles
        joint2 = theta1 + theta1_offset
        joint3 = theta2 + theta2_offset
        
        # Ensure angles are within URDF limits
        joint2 = max(-0.1, min(3.45, joint2))
        joint3 = max(-0.2, min(math.pi, joint3))
        
        # Convert from radians to degrees
        joint2_deg = math.degrees(joint2)
        joint3_deg = math.degrees(joint3)
        
        joint2_deg = 90 - joint2_deg
        joint3_deg = joint3_deg - 90
        
        return joint2_deg, joint3_deg
    
    def move_to_position(self, target_x, target_y, duration=4.0, num_waypoints=5):
        """移动到指定位置 - 使用多个航点实现平滑运动"""
        self.is_moving = True
        print(f"🎯 Moving to position: x={target_x:.3f}, y={target_y:.3f} (duration: {duration}s)")
        
        # 验证目标位置是否在工作空间内
        distance_from_origin = math.sqrt(target_x**2 + target_y**2)
        l1, l2 = 0.1159, 0.1350
        max_reach = l1 + l2
        min_reach = abs(l1 - l2)
        
        if distance_from_origin > max_reach:
            print(f"⚠️  Target position ({target_x:.3f}, {target_y:.3f}) is beyond max reach {max_reach:.3f}m")
            print(f"   Scaling to workspace boundary...")
            scale = max_reach / distance_from_origin
            target_x *= scale
            target_y *= scale
            print(f"   New target: ({target_x:.3f}, {target_y:.3f})")
        elif distance_from_origin < min_reach and distance_from_origin > 0:
            print(f"⚠️  Target position ({target_x:.3f}, {target_y:.3f}) is within min reach {min_reach:.3f}m")
            print(f"   Scaling to minimum workspace...")
            scale = min_reach / distance_from_origin
            target_x *= scale
            target_y *= scale
            print(f"   New target: ({target_x:.3f}, {target_y:.3f})")
        
        start_x, start_y = self.current_x, self.current_y
        
        # 生成中间航点
        waypoints = []
        for i in range(num_waypoints + 1):
            progress = i / num_waypoints
            # 使用平滑的S曲线插值（缓进缓出）
            smooth_progress = self._smooth_interpolation(progress)
            
            wp_x = start_x + (target_x - start_x) * smooth_progress
            wp_y = start_y + (target_y - start_y) * smooth_progress
            waypoints.append((wp_x, wp_y))
        
        print(f"📍 Generated {len(waypoints)} waypoints for smooth trajectory")
        
        if self.simulation_mode:
            # 模拟移动 - 通过每个航点
            waypoint_duration = duration / num_waypoints
            
            for i, (wp_x, wp_y) in enumerate(waypoints[1:], 1):  # 跳过起始点
                print(f"🎯 Waypoint {i}/{num_waypoints}: x={wp_x:.3f}, y={wp_y:.3f}")
                
                # 每个航点内部的细分步骤
                steps_per_waypoint = int(waypoint_duration * 20)  # 20Hz for smooth simulation
                prev_x, prev_y = self.current_x, self.current_y
                
                for j in range(steps_per_waypoint + 1):
                    step_progress = j / steps_per_waypoint
                    
                    current_x = prev_x + (wp_x - prev_x) * step_progress
                    current_y = prev_y + (wp_y - prev_y) * step_progress
                    
                    self.current_x = current_x
                    self.current_y = current_y
                    
                    if j % 10 == 0:  # 每0.5秒显示一次位置
                        print(f"   📍 Position: x={current_x:.3f}, y={current_y:.3f}")
                    
                    time.sleep(waypoint_duration / steps_per_waypoint)
        else:
            # 真实机器人移动 - 通过每个航点
            try:
                control_freq = 30  # 30Hz控制频率
                waypoint_duration = duration / num_waypoints
                steps_per_waypoint = int(waypoint_duration * control_freq)
                
                for i, (wp_x, wp_y) in enumerate(waypoints[1:], 1):  # 跳过起始点
                    print(f"🎯 Waypoint {i}/{num_waypoints}: x={wp_x:.3f}, y={wp_y:.3f}")
                    
                    # 计算该航点的关节角度
                    joint2, joint3 = self.inverse_kinematics(wp_x, wp_y)
                    print(f"   🔧 Joint angles: shoulder={joint2:.1f}°, elbow={joint3:.1f}°")
                    
                    # 从当前位置平滑移动到航点
                    prev_x, prev_y = self.current_x, self.current_y
                    
                    for j in range(steps_per_waypoint):
                        step_progress = j / steps_per_waypoint
                        
                        # 当前步骤的目标位置
                        intermediate_x = prev_x + (wp_x - prev_x) * step_progress
                        intermediate_y = prev_y + (wp_y - prev_y) * step_progress
                        
                        # 计算中间位置的关节角度
                        inter_joint2, inter_joint3 = self.inverse_kinematics(intermediate_x, intermediate_y)
                        
                        robot_action = {
                            'shoulder_lift.pos': inter_joint2,
                            'elbow_flex.pos': inter_joint3
                        }
                        
                        self.robot.send_action(robot_action)
                        time.sleep(1.0 / control_freq)
                    
                    # 更新当前位置到航点位置
                    self.current_x = wp_x
                    self.current_y = wp_y
                    
                    if i % 2 == 0:  # 每隔一个航点显示位置
                        print(f"   ✅ Reached waypoint {i}: x={wp_x:.3f}, y={wp_y:.3f}")
                
                # 最终位置确认
                self.current_x = target_x
                self.current_y = target_y
                
            except Exception as e:
                print(f"❌ Robot movement failed: {e}")
        
        self.is_moving = False
        print("✅ Smooth movement completed")
    
    def _smooth_interpolation(self, t):
        """平滑插值函数 - S曲线（缓进缓出）"""
        # 使用3次贝塞尔曲线实现平滑过渡
        # 这提供了缓慢开始、加速、然后缓慢结束的效果
        return t * t * (3.0 - 2.0 * t)
    
    def execute_push_trajectory(self, audio_manager):
        """执行推瓶动作轨迹 - 慢速平滑运动"""
        print("\n" + "="*60)
        print("🚀 STARTING SMOOTH PUSH TRAJECTORY")
        print("="*60)
        
        # 播放音频警告
        print("🔊 Playing audio alert...")
        audio_manager.play_alert_sound("push")
        
        # 等待音频播放完成
        time.sleep(1.0)
        
        # 定义轨迹点
        start_pos = (0.0, 0.16)      # 起始位置 - 在机器人工作空间内
        push_pos = (0.1, 0.16)       # 推进位置 (10cm forward)
        
        print(f"\n📋 Smooth Trajectory Plan:")
        print(f"   🏠 Start:  x={start_pos[0]:.3f}m, y={start_pos[1]:.3f}m")
        print(f"   🎯 Target: x={push_pos[0]:.3f}m, y={push_pos[1]:.3f}m")
        print(f"   ⏱️  Total time: ~12 seconds")
        print(f"   🛤️  Using 5 waypoints per movement")
        
        # Phase 1: 向前推进 (慢速)
        print(f"\n⏩ PHASE 1: Smooth Forward Push (5s)")
        self.move_to_position(push_pos[0], push_pos[1], duration=5.0, num_waypoints=5)
        
        # 较长停留时间
        print(f"\n⏸️  PHASE 2: Hold Position (2s)")
        print("   🤚 Maintaining contact with bottle...")
        time.sleep(2.0)
        
        # Phase 3: 向后退回 (慢速)
        print(f"\n⏪ PHASE 3: Smooth Backward Retreat (5s)")
        self.move_to_position(start_pos[0], start_pos[1], duration=5.0, num_waypoints=5)
        
        print(f"\n" + "="*60)
        print("✅ SMOOTH PUSH TRAJECTORY COMPLETED!")
        print("   Total execution time: ~12 seconds")
        print("="*60)
    
    def disconnect(self):
        """断开机器人连接"""
        if self.robot and not self.simulation_mode:
            try:
                self.robot.disconnect()
                print("🔌 Robot disconnected")
            except:
                pass

class CameraYOLOSystem:
    """摄像头YOLO检测系统"""
    
    def __init__(self, camera_id=4, model_path="yolov8n.pt"):
        self.camera_id = camera_id
        self.model = None
        self.cap = None
        self.running = False
        self.detection_callback = None
        
        # 初始化YOLO模型
        try:
            self.model = YOLO(model_path)
            print("✅ YOLO model loaded successfully")
        except Exception as e:
            print(f"❌ YOLO model loading failed: {e}")
    
    def auto_detect_camera(self):
        """自动检测可用摄像头"""
        print("🔍 Auto-detecting cameras...")
        available_cameras = []
        
        for camera_id in range(5):
            cap = cv2.VideoCapture(camera_id)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    available_cameras.append(camera_id)
                    print(f"✅ Camera {camera_id} detected")
                cap.release()
        
        if available_cameras:
            print(f"📷 Available cameras: {available_cameras}")
            return available_cameras[0]
        else:
            print("❌ No cameras detected")
            return None
    
    def initialize_camera(self):
        """初始化摄像头"""
        # 自动检测或使用指定摄像头
        if self.camera_id is None:
            self.camera_id = self.auto_detect_camera()
            if self.camera_id is None:
                return False
        
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                print(f"❌ Cannot open camera {self.camera_id}")
                return False
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print(f"📷 Camera {self.camera_id} initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            return False
    
    def set_detection_callback(self, callback):
        """设置检测回调函数"""
        self.detection_callback = callback
    
    def run_detection_loop(self, show_robot_status=False, robot_controller=None):
        """运行检测循环"""
        if not self.model or not self.cap:
            print("❌ Camera or model not initialized")
            return
        
        self.running = True
        fps_counter = 0
        fps_display = 0
        prev_time = time.time()
        detection_count = 0
        start_time = time.time()
        
        print("🎯 Starting camera detection loop...")
        print("Controls:")
        print("  'q' or ESC: Quit")
        print("  's': Save current frame")
        print("  'p': Manual push trigger")
        if show_robot_status:
            print("  Robot runs automatically every 15 seconds")
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to capture frame")
                    break
                
                # YOLO检测
                results = self.model(frame, device='cpu', verbose=False)
                
                # 处理检测结果
                bottle_detected = False
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            conf = float(box.conf[0])
                            cls = int(box.cls[0])
                            label = self.model.names[cls]
                            
                            # 只显示置信度大于0.5的检测结果
                            if conf > 0.5:
                                detection_count += 1
                                
                                # 检查是否为瓶子
                                if 'bottle' in label.lower():
                                    bottle_detected = True
                                
                                # 计算中心点
                                center_x = (x1 + x2) // 2
                                center_y = (y1 + y2) // 2
                                
                                # 绘制检测框
                                color = (0, 255, 255) if 'bottle' in label.lower() else (0, 255, 0)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                                cv2.circle(frame, (center_x, center_y), 5, color, -1)
                                
                                # 绘制标签
                                label_text = f'{label} {conf:.2f}'
                                cv2.putText(frame, label_text, (x1, y1 - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # 计算FPS
                current_time = time.time()
                fps_counter += 1
                if current_time - prev_time >= 1.0:
                    fps_display = fps_counter
                    fps_counter = 0
                    prev_time = current_time
                
                # 显示信息
                info_y = 30
                cv2.putText(frame, f'FPS: {fps_display}', (10, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                info_y += 30
                cv2.putText(frame, f'Camera: {self.camera_id}', (10, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                info_y += 25
                cv2.putText(frame, f'Detections: {detection_count}', (10, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # 显示运行时间
                info_y += 25
                runtime = int(current_time - start_time)
                cv2.putText(frame, f'Runtime: {runtime}s', (10, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # 显示机器人状态
                if show_robot_status and robot_controller:
                    info_y += 25
                    robot_status = "MOVING" if robot_controller.is_moving else "READY"
                    status_color = (0, 165, 255) if robot_controller.is_moving else (0, 255, 0)
                    cv2.putText(frame, f'Robot: {robot_status}', (10, info_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
                    
                    # 显示下次自动推进倒计时（估算）
                    if not robot_controller.is_moving:
                        info_y += 25
                        # 简单的倒计时估算
                        time_since_start = runtime % 15  # 假设15秒周期
                        next_push_in = 15 - time_since_start
                        cv2.putText(frame, f'Next auto push: {next_push_in}s', (10, info_y),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                if bottle_detected:
                    info_y += 25
                    cv2.putText(frame, 'BOTTLE DETECTED!', (10, info_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # 显示模式信息
                if show_robot_status:
                    cv2.putText(frame, 'UNIFIED MODE: YOLO + TIMED ROBOT', (10, frame.shape[0] - 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
                    cv2.putText(frame, 'Press P for manual push, Q to quit', (10, frame.shape[0] - 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # 显示画面
                cv2.imshow('Robot Demo - YOLO Detection + Timed Robot', frame)
                
                # 检查按键
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # ESC键退出
                    break
                elif key == ord('s'):  # 保存当前帧
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f'demo_frame_{timestamp}.jpg'
                    cv2.imwrite(filename, frame)
                    print(f"💾 Frame saved as {filename}")
                elif key == ord('p'):  # 触发推瓶动作
                    if self.detection_callback:
                        print("🎯 Manual push trigger activated")
                        threading.Thread(target=self.detection_callback, daemon=True).start()
                
                # 自动触发（当检测到瓶子时）
                if bottle_detected and self.detection_callback:
                    # 可以在这里添加自动触发逻辑
                    pass
                    
        except KeyboardInterrupt:
            print("⏹️  Detection loop interrupted by user")
        finally:
            self.running = False
    
    def stop(self):
        """停止检测"""
        self.running = False
    
    def cleanup(self):
        """清理资源"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

class IntegratedDemo:
    """集成演示系统"""
    
    def __init__(self):
        self.audio_manager = AudioManager()
        self.robot_controller = None
        self.camera_system = None
        self.demo_running = False
        
    def initialize_systems(self, robot_port="/dev/ttyACM1", camera_id=4, simulation_mode=False):
        """初始化所有系统"""
        print("🚀 Initializing Integrated Demo System...")
        print("="*60)
        
        # 初始化机器人控制器
        print("🤖 Initializing robot controller...")
        self.robot_controller = RobotController(robot_port, simulation_mode)
        
        # 初始化摄像头系统
        print("📷 Initializing camera system...")
        self.camera_system = CameraYOLOSystem(camera_id)
        
        if not self.camera_system.initialize_camera():
            print("❌ Camera system initialization failed")
            return False
        
        # 设置检测回调
        self.camera_system.set_detection_callback(self.on_bottle_detected)
        
        print("✅ All systems initialized successfully!")
        return True
    
    def on_bottle_detected(self):
        """瓶子检测回调函数"""
        if self.robot_controller and not self.robot_controller.is_moving:
            print("🍼 Bottle detected! Executing push trajectory...")
            self.robot_controller.execute_push_trajectory(self.audio_manager)
        else:
            print("⚠️  Robot is busy, skipping trajectory")
    
    def _manual_push_action(self):
        """手动推瓶动作 - 用于手动模式"""
        if self.robot_controller and not self.robot_controller.is_moving:
            print("🎯 Manual push triggered!")
            self.robot_controller.execute_push_trajectory(self.audio_manager)
        else:
            print("⚠️  Robot is busy, cannot execute manual push")
    
    def run_unified_demo(self, cycle_interval=15):
        """运行统一演示 - 连续YOLO检测 + 定时机器人动作"""
        if not self.camera_system or not self.robot_controller:
            print("❌ Systems not properly initialized")
            return
        
        self.demo_running = True
        print("🎬 Starting Unified Demo (YOLO + Timed Robot)...")
        print("="*60)
        print("Demo Features:")
        print("✅ Continuous YOLO bottle detection")
        print("✅ Automatic robot push every 15 seconds")
        print("✅ Manual trigger with 'p' key")
        print("✅ Audio alerts before movement")
        print(f"✅ Robot cycle interval: {cycle_interval}s")
        print("="*60)
        
        # 启动定时机器人动作线程
        robot_thread = threading.Thread(
            target=self._timed_robot_worker, 
            args=(cycle_interval,), 
            daemon=True
        )
        robot_thread.start()
        print(f"🤖 Started timed robot worker (every {cycle_interval}s)")
        
        try:
            # 启动摄像头检测循环（主线程）- 显示机器人状态
            self.camera_system.run_detection_loop(
                show_robot_status=True, 
                robot_controller=self.robot_controller
            )
            
        except KeyboardInterrupt:
            print("⏹️  Demo interrupted by user")
        finally:
            self.demo_running = False
            self.cleanup()
    
    def _timed_robot_worker(self, interval):
        """定时机器人工作线程"""
        print(f"⏰ Timed robot worker started (interval: {interval}s)")
        cycle_count = 0
        
        # 等待初始延迟
        initial_delay = 5
        print(f"⏳ Initial delay: {initial_delay}s before first robot movement...")
        time.sleep(initial_delay)
        
        while self.demo_running:
            if not self.robot_controller.is_moving:
                cycle_count += 1
                print(f"\n🔔 Timed Cycle {cycle_count} - Automatic Push Triggered!")
                
                try:
                    # 执行机器人推瓶动作
                    self.robot_controller.execute_push_trajectory(self.audio_manager)
                    print(f"✅ Timed cycle {cycle_count} completed")
                    
                    # 等待下一个周期
                    if self.demo_running:
                        print(f"⏳ Waiting {interval}s until next automatic push...")
                        time.sleep(interval)
                        
                except Exception as e:
                    print(f"❌ Timed robot cycle {cycle_count} failed: {e}")
                    time.sleep(5)  # 错误时短暂等待
            else:
                print("⚠️  Robot busy, skipping timed cycle...")
                time.sleep(2)  # 机器人忙碌时短暂等待
        
        print("🔄 Timed robot worker stopped")
    
    def cleanup(self):
        """清理所有资源"""
        print("🧹 Cleaning up systems...")
        
        if self.camera_system:
            self.camera_system.stop()
            self.camera_system.cleanup()
        
        if self.robot_controller:
            self.robot_controller.disconnect()
        
        if self.audio_manager:
            self.audio_manager.cleanup()
        
        print("✅ Cleanup completed")

def main():
    """主函数"""
    print("🎪 Integrated Robot Demo")
    print("="*60)
    print("This demo combines:")
    print("1. 📷 Camera + YOLO bottle detection")
    print("2. 🤖 Robot arm trajectory (push/pull)")
    print("3. 🔊 Audio alerts before movement")
    print("="*60)
    
    # 配置选项
    try:
        # 摄像头选择
        camera_input = input("Enter camera ID (0/1/2/3/4) or Enter for default (4): ").strip()
        camera_id = int(camera_input) if camera_input.isdigit() else 4
        
        # 机器人端口
        if not ROBOT_AVAILABLE:
            print("❌ Robot modules not available! Please install lerobot package.")
            return
        
        robot_port = input("Enter robot port (default /dev/ttyACM1): ").strip()
        if not robot_port:
            robot_port = "/dev/ttyACM1"
        
        # 演示模式选择
        print("\nDemo modes:")
        print("1. Camera Only (YOLO detection only)")
        print("2. Manual Mode (camera + manual robot trigger)")
        print("3. Unified Mode (camera + timed robot cycles)")
        mode_choice = input("Choose mode (1/2/3): ").strip()
        
        # 创建并运行演示
        demo = IntegratedDemo()
        
        if demo.initialize_systems(robot_port, camera_id, simulation_mode=False):
            if mode_choice == "3":
                # 统一模式 - 摄像头显示 + 定时机器人动作
                interval = int(input("Robot cycle interval in seconds (default: 15): ") or "15")
                print(f"🎬 Starting unified mode with {interval}s robot cycles...")
                demo.run_unified_demo(cycle_interval=interval)
            elif mode_choice == "2":
                # 手动模式 - 摄像头显示 + 手动触发
                print("🎬 Starting manual mode (press 'p' to trigger robot)...")
                demo.camera_system.set_detection_callback(demo._manual_push_action)
                demo.camera_system.run_detection_loop()
            else:
                # 仅摄像头模式
                print("🎬 Starting camera-only mode...")
                demo.camera_system.set_detection_callback(None)  # 禁用机器人触发
                demo.camera_system.run_detection_loop()
        else:
            print("❌ Demo initialization failed")
            
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
