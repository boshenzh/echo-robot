#!/usr/bin/env python3
"""
Camera Utilities for Echo Robot Vision System
摄像头工具函数

This module provides utility functions for camera operations,
including auto-detection, configuration, and basic operations.
"""

import cv2
import time
import numpy as np

def detect_available_cameras(max_cameras=10):
    """
    Detect all available cameras
    检测所有可用的摄像头
    
    Args:
        max_cameras: Maximum number of camera IDs to test
        
    Returns:
        List of available camera IDs with their properties
    """
    print("🔍 Detecting available cameras...")
    available_cameras = []
    
    for camera_id in range(max_cameras):
        cap = cv2.VideoCapture(camera_id)
        
        if cap.isOpened():
            # Try to read a frame to confirm camera is working
            ret, frame = cap.read()
            if ret:
                # Get camera properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                camera_info = {
                    'id': camera_id,
                    'width': width,
                    'height': height,
                    'fps': fps,
                    'backend': cap.getBackendName()
                }
                
                available_cameras.append(camera_info)
                print(f"✅ Camera {camera_id}: {width}x{height} @ {fps:.1f}FPS ({cap.getBackendName()})")
            
            cap.release()
        else:
            cap.release()
    
    if not available_cameras:
        print("❌ No cameras detected")
    else:
        print(f"📷 Found {len(available_cameras)} camera(s)")
    
    return available_cameras

def configure_camera(camera_id, width=1280, height=720, fps=30):
    """
    Configure camera with specified parameters
    配置摄像头参数
    
    Args:
        camera_id: Camera ID to configure
        width: Desired frame width
        height: Desired frame height
        fps: Desired frame rate
        
    Returns:
        Configured VideoCapture object or None if failed
    """
    cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        print(f"❌ Cannot open camera {camera_id}")
        return None
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    
    # Verify settings
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    actual_fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"📐 Camera {camera_id} configured:")
    print(f"   Resolution: {actual_width}x{actual_height} (requested: {width}x{height})")
    print(f"   FPS: {actual_fps:.1f} (requested: {fps})")
    
    return cap

def test_camera_feed(camera_id, duration=10):
    """
    Test camera feed for specified duration
    测试摄像头画面
    
    Args:
        camera_id: Camera ID to test
        duration: Test duration in seconds
    """
    cap = configure_camera(camera_id)
    if cap is None:
        return
    
    print(f"🎥 Testing camera {camera_id} for {duration} seconds...")
    print("Press 'q' to exit early")
    
    start_time = time.time()
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to read frame")
                break
            
            frame_count += 1
            elapsed = time.time() - start_time
            current_fps = frame_count / elapsed if elapsed > 0 else 0
            
            # Add info overlay
            cv2.putText(frame, f'Camera {camera_id}', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f'FPS: {current_fps:.1f}', (10, 70),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, f'Time: {elapsed:.1f}s', (10, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            cv2.imshow(f'Camera {camera_id} Test', frame)
            
            # Check for exit conditions
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            if elapsed >= duration:
                break
    
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        final_fps = frame_count / (time.time() - start_time)
        print(f"✅ Test completed: {frame_count} frames, average FPS: {final_fps:.1f}")

def capture_image(camera_id, filename=None):
    """
    Capture a single image from camera
    从摄像头捕获单张图像
    
    Args:
        camera_id: Camera ID to use
        filename: Output filename (auto-generated if None)
        
    Returns:
        Path to saved image or None if failed
    """
    cap = configure_camera(camera_id)
    if cap is None:
        return None
    
    # Warm up camera
    for _ in range(5):
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to read frame")
            cap.release()
            return None
    
    # Capture final image
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Failed to capture image")
        return None
    
    # Generate filename if not provided
    if filename is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"camera_{camera_id}_{timestamp}.jpg"
    
    # Save image
    cv2.imwrite(filename, frame)
    print(f"📷 Image captured: {filename}")
    
    return filename

def compare_cameras(camera_ids):
    """
    Compare multiple cameras side by side
    并排比较多个摄像头
    
    Args:
        camera_ids: List of camera IDs to compare
    """
    caps = []
    
    # Initialize all cameras
    for camera_id in camera_ids:
        cap = configure_camera(camera_id, width=640, height=480)
        if cap is not None:
            caps.append((camera_id, cap))
        else:
            print(f"⚠️ Skipping camera {camera_id}")
    
    if not caps:
        print("❌ No cameras available for comparison")
        return
    
    print(f"🔄 Comparing {len(caps)} cameras. Press 'q' to exit")
    
    try:
        while True:
            frames = []
            
            # Read from all cameras
            for camera_id, cap in caps:
                ret, frame = cap.read()
                if ret:
                    # Add camera ID label
                    cv2.putText(frame, f'Camera {camera_id}', (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                    frames.append(frame)
                else:
                    # Create black frame if camera fails
                    black_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(black_frame, f'Camera {camera_id} FAILED', (10, 240),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    frames.append(black_frame)
            
            if frames:
                # Arrange frames in a grid
                if len(frames) == 1:
                    combined = frames[0]
                elif len(frames) == 2:
                    combined = np.hstack(frames)
                elif len(frames) <= 4:
                    if len(frames) == 3:
                        frames.append(np.zeros_like(frames[0]))  # Add black frame
                    top_row = np.hstack(frames[:2])
                    bottom_row = np.hstack(frames[2:4])
                    combined = np.vstack([top_row, bottom_row])
                else:
                    # For more than 4 cameras, just show first 4
                    top_row = np.hstack(frames[:2])
                    bottom_row = np.hstack(frames[2:4])
                    combined = np.vstack([top_row, bottom_row])
                
                cv2.imshow('Camera Comparison', combined)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        print("\n⏹️ Comparison interrupted")
    
    finally:
        # Release all cameras
        for camera_id, cap in caps:
            cap.release()
        cv2.destroyAllWindows()
        print("📷 All cameras released")

def main():
    """Main function for testing camera utilities"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Camera Utilities')
    parser.add_argument('--detect', action='store_true', help='Detect available cameras')
    parser.add_argument('--test', type=int, metavar='ID', help='Test specific camera')
    parser.add_argument('--capture', type=int, metavar='ID', help='Capture image from camera')
    parser.add_argument('--compare', type=int, nargs='+', metavar='ID', help='Compare multiple cameras')
    parser.add_argument('--duration', type=int, default=10, help='Test duration in seconds')
    
    args = parser.parse_args()
    
    if args.detect:
        detect_available_cameras()
    elif args.test is not None:
        test_camera_feed(args.test, args.duration)
    elif args.capture is not None:
        capture_image(args.capture)
    elif args.compare:
        compare_cameras(args.compare)
    else:
        print("Camera Utilities - Echo Robot Vision System")
        print("摄像头工具 - Echo机器人视觉系统")
        print("\nUsage examples:")
        print("  python camera_utils.py --detect          # Detect cameras")
        print("  python camera_utils.py --test 0          # Test camera 0")
        print("  python camera_utils.py --capture 0       # Capture image")
        print("  python camera_utils.py --compare 0 1 2   # Compare cameras")

if __name__ == "__main__":
    main()
