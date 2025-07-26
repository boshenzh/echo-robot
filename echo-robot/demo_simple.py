#!/usr/bin/env python3
"""
Simple Demo Script for Robot Arm with YOLO Detection and Audio
简化版演示脚本：机器人手臂 + YOLO检测 + 音频反馈

This is a lightweight version that uses system beep for audio.
这是使用系统蜂鸣器的轻量级版本。

Features:
1. Camera visualization with YOLO bottle detection
2. Robot trajectory: forward/backward push motion  
3. Simple audio beep before robot movement
4. Can run in simulation mode without robot hardware

Requirements:
- OpenCV
- ultralytics (YOLO)
- lerobot (optional, for real robot)
"""

import cv2
import time
import math
import threading
import os
import sys
from ultralytics import YOLO

# Try to import robot modules
try:
    from lerobot.robots.so100_follower import SO100Follower, SO100FollowerConfig
    ROBOT_AVAILABLE = True
    print("🤖 Robot modules available")
except ImportError:
    ROBOT_AVAILABLE = False
    print("⚠️  Robot modules not available - simulation mode only")

def play_beep_sound(duration=0.5, frequency=800):
    """播放简单蜂鸣音"""
    try:
        # Try different methods for audio feedback
        if os.name == 'posix':  # Linux/macOS
            # Method 1: Use speaker-test (most common on Linux)
            os.system(f"timeout {duration} speaker-test -t sine -f {frequency} -l 1 >/dev/null 2>&1 &")
        else:
            # Method 2: Use print bell character as fallback
            print(f"\a")  # Bell character
        
        print(f"🔊 Audio alert: {frequency}Hz for {duration}s")
    except Exception as e:
        print(f"⚠️  Audio alert failed: {e}")
        print("🔔 BEEP! (Robot starting movement)")

class SimpleRobotController:
    """简化机器人控制器"""
    
    def __init__(self, port="/dev/ttyACM1", simulation_mode=False):
        self.simulation_mode = simulation_mode or not ROBOT_AVAILABLE
        self.robot = None
        self.current_x = 0.0
        self.current_y = 0.16  # Starting Y position
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
                    print("🔧 Calibrating robot...")
                    self.robot.calibrate()
                    print("✅ Calibration completed!")
                
            except Exception as e:
                print(f"❌ Robot connection failed: {e}")
                raise RuntimeError(f"❌ Failed to connect to robot at {port}. Check connection and port.")
        else:
            print("🎮 Running in simulation mode")
    
    def inverse_kinematics_simple(self, x, y):
        """简化的逆运动学计算"""
        # 简单的2关节逆运动学
        l1, l2 = 0.1159, 0.1350  # Link lengths
        
        # 确保目标在工作空间内
        r = math.sqrt(x**2 + y**2)
        r_max = l1 + l2
        
        if r > r_max:
            scale = r_max / r
            x *= scale
            y *= scale
            r = r_max
        
        # 计算关节角度 (简化版)
        cos_theta2 = (r**2 - l1**2 - l2**2) / (2 * l1 * l2)
        cos_theta2 = max(-1, min(1, cos_theta2))  # Clamp to valid range
        
        theta2 = math.acos(cos_theta2)
        theta1 = math.atan2(y, x) - math.atan2(l2 * math.sin(theta2), l1 + l2 * math.cos(theta2))
        
        # 转换为度数
        joint2_deg = math.degrees(theta1)
        joint3_deg = math.degrees(theta2)
        
        return joint2_deg, joint3_deg
    
    def move_to_position(self, target_x, target_y, duration=4.0, num_waypoints=5):
        """移动到指定位置 - 使用多个航点实现平滑运动"""
        self.is_moving = True
        print(f"🎯 Moving to position: x={target_x:.3f}, y={target_y:.3f} (duration: {duration}s)")
        
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
                    joint2, joint3 = self.inverse_kinematics_simple(wp_x, wp_y)
                    
                    # 从当前位置平滑移动到航点
                    prev_x, prev_y = self.current_x, self.current_y
                    
                    for j in range(steps_per_waypoint):
                        step_progress = j / steps_per_waypoint
                        
                        # 当前步骤的目标位置
                        intermediate_x = prev_x + (wp_x - prev_x) * step_progress
                        intermediate_y = prev_y + (wp_y - prev_y) * step_progress
                        
                        # 计算中间位置的关节角度
                        inter_joint2, inter_joint3 = self.inverse_kinematics_simple(intermediate_x, intermediate_y)
                        
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
    
    def execute_push_sequence(self):
        """执行推瓶序列 - 慢速平滑运动"""
        print("\n" + "="*60)
        print("🚀 STARTING SMOOTH PUSH SEQUENCE")
        print("="*60)
        
        # 播放音频警告
        print("🔊 Playing audio warning...")
        play_beep_sound(duration=0.8, frequency=800)
        time.sleep(1.0)  # 等待音频播放完成
        
        # 定义轨迹点
        start_pos = (0.0, 0.16)    # 起始位置
        push_pos = (0.1, 0.16)     # 推进位置 (10cm forward)
        
        print(f"\n📋 Smooth Trajectory Plan:")
        print(f"   🏠 Start:  x={start_pos[0]:.3f}m, y={start_pos[1]:.3f}m")
        print(f"   🎯 Target: x={push_pos[0]:.3f}m, y={push_pos[1]:.3f}m")
        print(f"   ⏱️  Total time: ~12 seconds")
        print(f"   🛤️  Using 5 waypoints per movement")
        
        # Phase 1: 向前推进
        print(f"\n⏩ PHASE 1: Smooth Forward Push (5s)")
        self.move_to_position(push_pos[0], push_pos[1], duration=5.0, num_waypoints=5)
        
        # 短暂停留
        print(f"\n⏸️  PHASE 2: Hold Position (2s)")
        print("   🤚 Maintaining contact with bottle...")
        time.sleep(2.0)
        
        # Phase 3: 向后退回
        print(f"\n⏪ PHASE 3: Smooth Backward Retreat (5s)")
        self.move_to_position(start_pos[0], start_pos[1], duration=5.0, num_waypoints=5)
        
        print(f"\n" + "="*60)
        print("✅ SMOOTH PUSH SEQUENCE COMPLETED!")
        print("   Total execution time: ~12 seconds")
        print("="*60)
    
    def cleanup(self):
        """清理资源"""
        if self.robot and not self.simulation_mode:
            try:
                print("🔌 Disconnecting robot...")
                self.robot.disconnect()
                print("✅ Robot disconnected")
            except:
                pass

class SimpleCameraYOLO:
    """简化摄像头YOLO系统"""
    
    def __init__(self, camera_id=4):
        self.camera_id = camera_id
        self.model = None
        self.cap = None
        self.running = False
        self.detection_callback = None
        
        # 加载YOLO模型
        try:
            print("🤖 Loading YOLO model...")
            self.model = YOLO("yolov8n.pt")
            print("✅ YOLO model loaded successfully")
        except Exception as e:
            print(f"❌ YOLO model loading failed: {e}")
            raise
    
    def find_camera(self):
        """查找可用摄像头"""
        print("🔍 Searching for cameras...")
        
        for i in range(5):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    print(f"✅ Found working camera: {i}")
                    cap.release()
                    return i
                cap.release()
        
        print("❌ No working cameras found")
        return None
    
    def initialize_camera(self):
        """初始化摄像头"""
        if self.camera_id is None:
            self.camera_id = self.find_camera()
            if self.camera_id is None:
                return False
        
        try:
            print(f"📷 Initializing camera {self.camera_id}...")
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                print(f"❌ Cannot open camera {self.camera_id}")
                return False
            
            # 设置摄像头参数
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # 测试读取
            ret, _ = self.cap.read()
            if not ret:
                print("❌ Camera cannot capture frames")
                return False
            
            print("✅ Camera initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            return False
    
    def set_detection_callback(self, callback):
        """设置瓶子检测回调"""
        self.detection_callback = callback
    
    def run_detection(self):
        """运行检测循环"""
        if not self.model or not self.cap:
            print("❌ Camera or model not ready")
            return
        
        self.running = True
        print("\n🎯 Starting camera detection...")
        print("Controls:")
        print("  'q' or ESC: Quit")
        print("  'p': Manual push trigger")
        print("  's': Save current frame")
        print("-" * 40)
        
        fps_count = 0
        fps_display = 0
        last_time = time.time()
        detection_count = 0
        
        try:
            while self.running:
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Failed to read frame")
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
                            
                            if conf > 0.5:  # 置信度阈值
                                detection_count += 1
                                
                                # 检查是否为瓶子类别
                                if 'bottle' in label.lower():
                                    bottle_detected = True
                                
                                # 绘制检测框
                                color = (0, 255, 255) if bottle_detected else (0, 255, 0)
                                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                                
                                # 绘制标签
                                label_text = f'{label} {conf:.2f}'
                                cv2.putText(frame, label_text, (x1, y1 - 10),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                # 计算FPS
                fps_count += 1
                current_time = time.time()
                if current_time - last_time >= 1.0:
                    fps_display = fps_count
                    fps_count = 0
                    last_time = current_time
                
                # 显示信息
                cv2.putText(frame, f'FPS: {fps_display}', (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(frame, f'Detections: {detection_count}', (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                if bottle_detected:
                    cv2.putText(frame, 'BOTTLE DETECTED!', (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                # 显示窗口
                cv2.imshow('Simple Robot Demo - YOLO Detection', frame)
                
                # 处理按键
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # ESC退出
                    break
                elif key == ord('p'):  # 手动触发推进
                    if self.detection_callback:
                        print("🎯 Manual push trigger activated!")
                        threading.Thread(target=self.detection_callback, daemon=True).start()
                elif key == ord('s'):  # 保存帧
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    filename = f'demo_frame_{timestamp}.jpg'
                    cv2.imwrite(filename, frame)
                    print(f"💾 Frame saved: {filename}")
                
        except KeyboardInterrupt:
            print("⏹️  Detection interrupted")
        finally:
            self.running = False
    
    def cleanup(self):
        """清理资源"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

def main():
    """主函数"""
    print("🎪 Simple Robot Demo")
    print("="*50)
    print("Features:")
    print("✅ Camera + YOLO bottle detection")
    print("✅ Robot push/pull trajectory")
    print("✅ Audio beep before movement")
    print("✅ Manual trigger with 'p' key")
    print("="*50)
    
    robot_controller = None
    camera_system = None
    
    try:
        # 配置参数
        print("\n📋 Configuration:")
        
        # 摄像头选择
        camera_input = input("Camera ID (0/1/2/3/4) or Enter for default (4): ").strip()
        camera_id = int(camera_input) if camera_input.isdigit() else 4
        
        # 机器人设置
        if not ROBOT_AVAILABLE:
            print("❌ Robot modules not available! Please install lerobot package.")
            return
        
        robot_port = input("Robot port (default /dev/ttyACM1): ").strip()
        if not robot_port:
            robot_port = "/dev/ttyACM1"
        
        print(f"\n🔧 Settings:")
        print(f"   Camera: {camera_id}")
        print(f"   Robot: {robot_port}")
        
        # 初始化系统
        print("\n🚀 Initializing systems...")
        
        # 机器人控制器
        robot_controller = SimpleRobotController(robot_port, simulation_mode=False)
        
        # 摄像头系统
        camera_system = SimpleCameraYOLO(camera_id)
        if not camera_system.initialize_camera():
            print("❌ Camera initialization failed")
            return
        
        # 设置回调
        camera_system.set_detection_callback(robot_controller.execute_push_sequence)
        
        print("✅ All systems ready!")
        
        # 演示模式选择
        print("\n🎮 Demo modes:")
        print("1. Interactive (camera + manual trigger)")
        print("2. Automatic test (no camera)")
        
        mode = input("Choose mode (1/2): ").strip()
        
        if mode == "2":
            # 自动测试模式
            print("\n🔄 Automatic test mode")
            cycles = int(input("Number of cycles (default 3): ") or "3")
            
            for i in range(cycles):
                print(f"\n🎯 Cycle {i+1}/{cycles}")
                robot_controller.execute_push_sequence()
                if i < cycles - 1:
                    print("⏳ Waiting 5 seconds...")
                    time.sleep(5)
        else:
            # 交互模式
            print("\n🎯 Starting interactive demo...")
            camera_system.run_detection()
        
    except KeyboardInterrupt:
        print("\n⏹️  Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        print("\n🧹 Cleaning up...")
        if camera_system:
            camera_system.cleanup()
        if robot_controller:
            robot_controller.cleanup()
        print("✅ Demo ended")

if __name__ == "__main__":
    main()
