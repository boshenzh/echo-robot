#!/usr/bin/env python3
"""
Camera Calibration Script for Echo Robot Vision System
摄像头校准脚本 - 实现精确定位

This script helps calibrate camera intrinsic and extrinsic parameters
for accurate 2D to 3D coordinate transformation in bottle pushing tasks.

Usage:
    python camera_calibration.py --camera-id 0 --calibrate
    python camera_calibration.py --camera-id 0 --test
"""

import cv2
import numpy as np
import argparse
import json
import os
import time
import math
from datetime import datetime
import glob

class CameraCalibrator:
    def __init__(self, camera_id=0):
        """
        Initialize camera calibrator
        初始化摄像头校准器
        """
        self.camera_id = camera_id
        self.cap = None
        
        # Calibration pattern settings (棋盘格参数)
        self.pattern_size = (9, 6)  # Number of inner corners (内角点数量)
        self.square_size = 25.0     # Size of squares in mm (方格尺寸，毫米)
        
        # Calibration data
        self.calibration_data = {
            'camera_matrix': None,
            'distortion_coeffs': None,
            'rotation_vectors': None,
            'translation_vectors': None,
            'calibration_date': None,
            'reprojection_error': None
        }
        
        # Create calibration directory
        os.makedirs('config', exist_ok=True)
        
    def initialize_camera(self):
        """Initialize camera connection 初始化摄像头连接"""
        try:
            print(f"🔍 Attempting to open camera {self.camera_id}...")
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                # Try different backends
                print(f"⚠️  Direct access failed, trying different backends...")
                for backend in [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_FFMPEG]:
                    self.cap = cv2.VideoCapture(self.camera_id, backend)
                    if self.cap.isOpened():
                        print(f"✅ Camera opened with backend: {self.cap.getBackendName()}")
                        break
                    self.cap.release()
                
                if not self.cap.isOpened():
                    raise Exception(f"Cannot open camera {self.camera_id} with any backend")
            
            # Set camera properties BEFORE testing frames
            print("🔧 Configuring camera settings...")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to avoid lag
            
            # Warm up camera - flush initial frames
            print("🔥 Warming up camera...")
            for i in range(10):
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    if i == 0:
                        print(f"📐 Initial frame: {frame.shape[1]}x{frame.shape[0]}")
                    if i == 9:
                        print(f"📐 Final frame: {frame.shape[1]}x{frame.shape[0]}")
                        # Check if frame is too dark
                        brightness = frame.mean()
                        print(f"🔆 Frame brightness: {brightness:.1f}")
                        if brightness < 10:
                            print("⚠️  Warning: Very dark frame. Check lighting or camera settings.")
                else:
                    print(f"❌ Failed to read frame {i+1} during warmup")
            
            # Final test
            ret, test_frame = self.cap.read()
            if not ret or test_frame is None:
                raise Exception(f"Camera {self.camera_id} opened but cannot read frames after warmup")
            
            # Verify resolution was set
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"📐 Final resolution: {actual_width}x{actual_height}")
            
            print(f"✅ Camera {self.camera_id} initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize camera: {e}")
            if self.cap:
                self.cap.release()
            return False
    
    def collect_calibration_images(self, num_images=20):
        """
        Collect calibration images with checkerboard pattern
        收集棋盘格标定图像
        """
        if not self.initialize_camera():
            return False
        
        print(f"\n📸 Collecting {num_images} calibration images...")
        print("Instructions 使用说明:")
        print("- Hold a checkerboard pattern (9x6) in front of the camera")
        print("- Press SPACE to capture image when pattern is detected")
        print("- Press ESC to finish early")
        print("- Move the pattern to different positions and angles")
        print("- 在摄像头前放置棋盘格标定板(9x6)")
        print("- 检测到图案时按空格键拍照")
        print("- 按ESC键提前结束")
        print("- 将标定板移动到不同位置和角度\n")
        
        captured_count = 0
        os.makedirs('calibration_images', exist_ok=True)
        
        # Test initial frame reading
        print("📋 Testing initial frame capture...")
        for i in range(10):  # Try more frames to let camera warm up properly
            ret, frame = self.cap.read()
            if ret and frame is not None:
                brightness = frame.mean()
                print(f"✅ Frame {i+1}: {frame.shape[1]}x{frame.shape[0]}, brightness: {brightness:.1f}")
                if i >= 4 and brightness > 10:  # Need decent brightness after warmup
                    break
            else:
                print(f"❌ Frame {i+1}: Failed to read")
                if i > 7:  # Try more attempts before giving up
                    time.sleep(0.1)  # Small delay between attempts
        
        if not ret or frame is None:
            print("❌ Cannot read frames from camera. Check camera connection.")
            return False
        
        print("🎯 Starting calibration capture loop...")
        
        # Test if we can create OpenCV window
        try:
            cv2.namedWindow('Camera Calibration - 摄像头标定', cv2.WINDOW_AUTOSIZE)
            print("✅ OpenCV window created successfully")
        except Exception as e:
            print(f"❌ Failed to create OpenCV window: {e}")
            print("🔧 Trying headless mode - will save images without display")
        
        loop_count = 0
        max_loops = 1000  # Safety limit to prevent infinite loops
        
        while captured_count < num_images and loop_count < max_loops:
            loop_count += 1
            
            # Progress indicator every 50 loops
            if loop_count % 50 == 0:
                print(f"🔄 Loop {loop_count}: Still looking for patterns... (captured: {captured_count}/{num_images})")
            
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print(f"❌ Failed to read from camera (loop {loop_count})")
                time.sleep(0.1)  # Brief pause before retrying
                continue
            
            # Check if frame is valid (not all black/empty)
            frame_brightness = frame.mean()
            if frame_brightness < 5:  # Very dark image, likely camera issue
                print(f"⚠️  Warning: Very dark frame detected (brightness: {frame_brightness:.1f}). Check camera and lighting.")
                # Don't break immediately, give it a few more tries
                time.sleep(0.1)
                continue
            
            # Convert to grayscale for pattern detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Find checkerboard corners
            found, corners = cv2.findChessboardCorners(gray, self.pattern_size, None)
            
            # Draw corners if found
            display_frame = frame.copy()
            if found:
                cv2.drawChessboardCorners(display_frame, self.pattern_size, corners, found)
                cv2.putText(display_frame, f"Pattern detected! Press SPACE to capture ({captured_count}/{num_images})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(display_frame, "Checkerboard found - ready to capture", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(display_frame, f"Move checkerboard into view ({captured_count}/{num_images})", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(display_frame, f"Looking for {self.pattern_size[0]}x{self.pattern_size[1]} pattern", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Add frame info
            cv2.putText(display_frame, f"Camera {self.camera_id} - Frame: {frame.shape[1]}x{frame.shape[0]}", 
                       (10, display_frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Show progress
            cv2.putText(display_frame, f"Loop: {loop_count}, Brightness: {frame_brightness:.1f}", 
                       (10, display_frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Try to show the window
            try:
                cv2.imshow('Camera Calibration - 摄像头标定', display_frame)
                key = cv2.waitKey(1) & 0xFF
            except Exception as e:
                if loop_count % 100 == 1:  # Only print error occasionally
                    print(f"⚠️  Display error (continuing anyway): {e}")
                key = 255  # No key pressed
                
                # In headless mode, auto-capture when pattern is found
                if found and loop_count % 30 == 0:  # Auto-capture every 30 loops when pattern found
                    key = ord(' ')  # Simulate spacebar
            if key == ord(' ') and found:  # Space key
                # Save image
                filename = f'calibration_images/calib_{captured_count:02d}.jpg'
                cv2.imwrite(filename, frame)
                captured_count += 1
                print(f"📷 Captured image {captured_count}/{num_images}")
                
            elif key == 27:  # ESC key
                break
            elif key == ord('q'):  # Q key alternative
                break
            elif key == ord('d'):  # D key for debug info
                print(f"🔍 Debug: Frame shape: {frame.shape}, mean brightness: {frame.mean():.1f}")
                print(f"🔍 Debug: Loop {loop_count}, captured {captured_count}/{num_images}")
        
        # Check if we hit the loop limit
        if loop_count >= max_loops:
            print(f"⚠️  Reached maximum loop limit ({max_loops}). Stopping capture.")
        
        cv2.destroyAllWindows()
        self.cap.release()
        
        if captured_count >= 10:
            print(f"✅ Collected {captured_count} calibration images")
            return True
        else:
            print(f"❌ Need at least 10 images for calibration, got {captured_count}")
            return False
    
    def calibrate_camera(self):
        """
        Perform camera calibration using collected images
        使用收集的图像进行摄像头标定
        """
        # Get list of calibration images
        image_files = glob.glob('calibration_images/*.jpg')
        if len(image_files) < 10:
            print("❌ Not enough calibration images. Please collect images first.")
            return False
        
        print(f"\n🔧 Calibrating camera with {len(image_files)} images...")
        
        # Prepare object points (3D points in real world space)
        objp = np.zeros((self.pattern_size[0] * self.pattern_size[1], 3), np.float32)
        objp[:, :2] = np.mgrid[0:self.pattern_size[0], 0:self.pattern_size[1]].T.reshape(-1, 2)
        objp *= self.square_size
        
        # Arrays to store object points and image points
        objpoints = []  # 3D points in real world space
        imgpoints = []  # 2D points in image plane
        
        for image_file in image_files:
            img = cv2.imread(image_file)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Find checkerboard corners
            found, corners = cv2.findChessboardCorners(gray, self.pattern_size, None)
            
            if found:
                objpoints.append(objp)
                
                # Refine corner positions
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), 
                                          (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                imgpoints.append(corners2)
        
        if len(objpoints) < 10:
            print("❌ Not enough valid calibration patterns found")
            return False
        
        # Perform camera calibration
        img_shape = gray.shape[::-1]
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, img_shape, None, None)
        
        if ret:
            # Calculate reprojection error
            total_error = 0
            for i in range(len(objpoints)):
                imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], 
                                                camera_matrix, dist_coeffs)
                error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
                total_error += error
            
            mean_error = total_error / len(objpoints)
            
            # Store calibration data
            self.calibration_data = {
                'camera_matrix': camera_matrix.tolist(),
                'distortion_coeffs': dist_coeffs.tolist(),
                'rotation_vectors': [r.tolist() for r in rvecs],
                'translation_vectors': [t.tolist() for t in tvecs],
                'calibration_date': datetime.now().isoformat(),
                'reprojection_error': mean_error,
                'image_size': img_shape,
                'pattern_size': self.pattern_size,
                'square_size': self.square_size
            }
            
            # Save calibration data
            self.save_calibration()
            
            print(f"✅ Camera calibration successful!")
            print(f"📊 Reprojection error: {mean_error:.3f} pixels")
            print(f"📐 Camera matrix:")
            print(f"   fx: {camera_matrix[0,0]:.2f}, fy: {camera_matrix[1,1]:.2f}")
            print(f"   cx: {camera_matrix[0,2]:.2f}, cy: {camera_matrix[1,2]:.2f}")
            print(f"🔧 Distortion coefficients: {dist_coeffs.flatten()}")
            
            return True
        else:
            print("❌ Camera calibration failed")
            return False
    
    def save_calibration(self):
        """Save calibration parameters to file 保存标定参数到文件"""
        filename = 'config/camera_params.json'
        with open(filename, 'w') as f:
            json.dump(self.calibration_data, f, indent=2)
        print(f"💾 Calibration data saved to {filename}")
    
    def load_calibration(self):
        """Load calibration parameters from file 从文件加载标定参数"""
        filename = 'config/camera_params.json'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                self.calibration_data = json.load(f)
            print(f"📂 Calibration data loaded from {filename}")
            return True
        else:
            print(f"❌ Calibration file {filename} not found")
            return False
    
    def test_camera_live(self, duration=10):
        """
        Simple live camera test to debug issues
        简单的实时摄像头测试用于调试
        """
        if not self.initialize_camera():
            return False
        
        print(f"🎥 Testing live camera feed for {duration} seconds...")
        print("Press 'q' to exit early, 's' to save frame")
        
        start_time = time.time()
        frame_count = 0
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("❌ Failed to read frame")
                    break
                
                frame_count += 1
                elapsed = time.time() - start_time
                
                # Add debugging info to frame
                info_text = [
                    f'Camera {self.camera_id}',
                    f'Frame: {frame.shape[1]}x{frame.shape[0]}',
                    f'FPS: {frame_count/elapsed:.1f}',
                    f'Brightness: {frame.mean():.1f}',
                    f'Time: {elapsed:.1f}s'
                ]
                
                for i, text in enumerate(info_text):
                    y_pos = 30 + i * 25
                    cv2.putText(frame, text, (10, y_pos),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Add a test pattern overlay to verify the image is updating
                center_x, center_y = frame.shape[1] // 2, frame.shape[0] // 2
                radius = int(20 + 10 * abs(math.sin(elapsed * 2)))
                cv2.circle(frame, (center_x, center_y), radius, (255, 0, 0), 3)
                
                cv2.imshow('Camera Test - Press Q to quit', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break
                elif key == ord('s'):
                    filename = f'camera_test_{int(time.time())}.jpg'
                    cv2.imwrite(filename, frame)
                    print(f"📷 Saved frame: {filename}")
                
                if elapsed >= duration:
                    break
                    
        except Exception as e:
            print(f"❌ Error during camera test: {e}")
            
        finally:
            self.cap.release()
            cv2.destroyAllWindows()
            
            if frame_count > 0:
                avg_fps = frame_count / (time.time() - start_time)
                print(f"✅ Test completed: {frame_count} frames, {avg_fps:.1f} FPS")
            else:
                print("❌ No frames captured")
            
            return frame_count > 0
    
    def test_calibration(self):
        """
        Test camera calibration by showing undistorted video
        测试摄像头标定效果
        """
        if not self.load_calibration():
            print("❌ Please calibrate camera first")
            return
        
        if not self.initialize_camera():
            return
        
        # Convert calibration data back to numpy arrays
        camera_matrix = np.array(self.calibration_data['camera_matrix'])
        dist_coeffs = np.array(self.calibration_data['distortion_coeffs'])
        
        print("\n📺 Testing calibration - Press ESC to exit")
        print("Left: Original image, Right: Undistorted image")
        print("左侧：原始图像，右侧：去畸变图像")
        
        # Test initial frame reading
        print("🔍 Testing frame capture for calibration test...")
        for i in range(5):
            ret, frame = self.cap.read()
            if ret and frame is not None:
                brightness = frame.mean()
                print(f"✅ Test frame {i+1}: {frame.shape[1]}x{frame.shape[0]}, brightness: {brightness:.1f}")
                break
            else:
                print(f"❌ Test frame {i+1}: Failed to read")
                time.sleep(0.1)
        
        if not ret or frame is None:
            print("❌ Cannot read frames from camera for calibration test")
            self.cap.release()
            return
        
        print("🎯 Starting calibration test display...")
        
        try:
            cv2.namedWindow('Calibration Test - 标定测试', cv2.WINDOW_AUTOSIZE)
            print("✅ Test window created successfully")
        except Exception as e:
            print(f"❌ Failed to create test window: {e}")
        
        frame_count = 0
        max_frames = 1000  # Safety limit
        
        while frame_count < max_frames:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print(f"❌ Failed to read frame {frame_count}")
                time.sleep(0.1)
                continue
            
            frame_count += 1
            
            # Check frame validity
            frame_brightness = frame.mean()
            if frame_brightness < 5:
                print(f"⚠️  Very dark frame detected (brightness: {frame_brightness:.1f})")
                time.sleep(0.1)
                continue
            
            # Progress indicator
            if frame_count % 100 == 1:
                print(f"🔄 Processing frame {frame_count}, brightness: {frame_brightness:.1f}")
            
            try:
                # Undistort image
                undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs)
                
                # Combine original and undistorted images
                h, w = frame.shape[:2]
                combined = np.hstack([frame, undistorted])
                
                # Add labels and info
                cv2.putText(combined, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.putText(combined, "Undistorted", (w + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(combined, f"Frame: {frame_count}, Brightness: {frame_brightness:.1f}", 
                           (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                cv2.imshow('Calibration Test - 标定测试', combined)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 27 or key == ord('q'):  # ESC or Q key
                    print("🛑 User requested exit")
                    break
                elif key == ord('s'):  # S key to save
                    filename = f'calibration_test_{int(time.time())}.jpg'
                    cv2.imwrite(filename, combined)
                    print(f"📷 Saved test image: {filename}")
                    
            except Exception as e:
                if frame_count % 50 == 1:  # Only print error occasionally
                    print(f"⚠️  Display error in calibration test: {e}")
                time.sleep(0.1)
                continue
        
        print(f"✅ Calibration test completed: {frame_count} frames processed")
        cv2.destroyAllWindows()
        self.cap.release()
    
    def pixel_to_world(self, pixel_x, pixel_y, world_z=0):
        """
        Convert pixel coordinates to world coordinates
        将像素坐标转换为世界坐标
        
        Args:
            pixel_x, pixel_y: Pixel coordinates in image
            world_z: Z coordinate in world space (assumed depth)
        
        Returns:
            world_x, world_y: World coordinates in mm
        """
        if not self.calibration_data['camera_matrix']:
            print("❌ Camera not calibrated")
            return None, None
        
        camera_matrix = np.array(self.calibration_data['camera_matrix'])
        dist_coeffs = np.array(self.calibration_data['distortion_coeffs'])
        
        # Undistort pixel coordinates
        pixel_points = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
        undistorted_points = cv2.undistortPoints(pixel_points, camera_matrix, dist_coeffs, P=camera_matrix)
        
        # Convert to normalized coordinates
        u_norm = (undistorted_points[0][0][0] - camera_matrix[0, 2]) / camera_matrix[0, 0]
        v_norm = (undistorted_points[0][0][1] - camera_matrix[1, 2]) / camera_matrix[1, 1]
        
        # Assuming camera is looking down at a plane at height world_z
        # Simple pinhole projection (requires known depth or plane assumption)
        world_x = u_norm * world_z
        world_y = v_norm * world_z
        
        return world_x, world_y

def auto_detect_working_camera():
    """
    Auto-detect a working camera ID
    自动检测可用的摄像头ID
    """
    print("🔍 Auto-detecting working cameras...")
    
    for camera_id in range(10):  # Test camera IDs 0-9
        print(f"Testing camera {camera_id}...", end=" ")
        cap = cv2.VideoCapture(camera_id)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                print(f"✅ Working (resolution: {frame.shape[1]}x{frame.shape[0]})")
                cap.release()
                return camera_id
            else:
                print("❌ Opens but no frame")
        else:
            print("❌ Cannot open")
        
        cap.release()
    
    print("❌ No working cameras found!")
    return None

def main():
    parser = argparse.ArgumentParser(description='Camera Calibration for Echo Robot')
    parser.add_argument('--camera-id', type=int, default=None, help='Camera ID (auto-detect if not specified)')
    parser.add_argument('--calibrate', action='store_true', help='Perform camera calibration')
    parser.add_argument('--test', action='store_true', help='Test calibration results')
    parser.add_argument('--collect', action='store_true', help='Collect calibration images only')
    parser.add_argument('--live-test', action='store_true', help='Test live camera feed')
    parser.add_argument('--num-images', type=int, default=20, help='Number of calibration images to collect')
    parser.add_argument('--auto-detect', action='store_true', help='Auto-detect working camera')
    parser.add_argument('--duration', type=int, default=10, help='Duration for live test in seconds')
    
    args = parser.parse_args()
    
    # Auto-detect camera if not specified or if explicitly requested
    if args.camera_id is None or args.auto_detect:
        detected_camera = auto_detect_working_camera()
        if detected_camera is not None:
            camera_id = detected_camera
            print(f"🎯 Using auto-detected camera: {camera_id}")
        else:
            print("❌ No working camera detected. Please specify --camera-id manually")
            return
    else:
        camera_id = args.camera_id
    
    calibrator = CameraCalibrator(camera_id)
    
    if args.auto_detect:
        print(f"🎯 Auto-detected camera {camera_id}. You can now run:")
        print(f"   python camera_calibration.py --camera-id {camera_id} --calibrate")
        return
    
    if args.collect:
        calibrator.collect_calibration_images(args.num_images)
    elif args.calibrate:
        if calibrator.collect_calibration_images(args.num_images):
            calibrator.calibrate_camera()
    elif args.test:
        calibrator.test_calibration()
    elif args.live_test:
        calibrator.test_camera_live(args.duration)
    else:
        print("Please specify --calibrate, --test, --collect, --live-test, or --auto-detect")
        print("使用说明:")
        print("  --auto-detect: 自动检测可用摄像头")
        print("  --live-test: 测试摄像头实时画面")
        print("  --calibrate: 进行标定")
        print("  --test: 测试标定结果")
        print("  --collect: 只收集图像")

if __name__ == "__main__":
    main()
