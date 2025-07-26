#!/usr/bin/env python3
"""
Quick Test Script for Demo Components
快速测试脚本 - 验证演示组件

This script tests individual components without needing full hardware setup.
"""

import cv2
import time
import os
import sys

def test_camera():
    """测试摄像头"""
    print("🔍 Testing camera...")
    
    for i in range(3):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"✅ Camera {i}: Working ({frame.shape})")
                cap.release()
                return i
            else:
                print(f"❌ Camera {i}: Cannot read frames")
        else:
            print(f"❌ Camera {i}: Cannot open")
        cap.release()
    
    print("❌ No working cameras found")
    return None

def test_yolo():
    """测试YOLO模型"""
    print("🤖 Testing YOLO model...")
    
    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
        print("✅ YOLO model loaded successfully")
        
        # Test with dummy data
        import numpy as np
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        results = model(dummy_image, verbose=False)
        print("✅ YOLO inference test passed")
        return True
        
    except Exception as e:
        print(f"❌ YOLO test failed: {e}")
        return False

def test_audio():
    """测试音频"""
    print("🔊 Testing audio...")
    
    try:
        # Test system beep
        print("Testing system beep...")
        os.system("echo '🔔 Audio test - you should hear a beep'")
        
        # Try speaker-test (Linux)
        if os.name == 'posix':
            result = os.system("timeout 1 speaker-test -t sine -f 800 -l 1 >/dev/null 2>&1")
            if result == 0:
                print("✅ System audio (speaker-test): Working")
            else:
                print("⚠️  System audio: speaker-test not available")
        
        # Try pygame if available
        try:
            import pygame
            pygame.mixer.init()
            print("✅ Pygame audio: Available")
            pygame.mixer.quit()
        except ImportError:
            print("⚠️  Pygame audio: Not installed")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        return False

def test_robot_simulation():
    """测试机器人仿真"""
    print("🤖 Testing robot simulation...")
    
    try:
        # Simple inverse kinematics test
        import math
        
        def simple_ik(x, y):
            l1, l2 = 0.1159, 0.1350
            r = math.sqrt(x**2 + y**2)
            if r > (l1 + l2):
                return None, None
            
            cos_theta2 = (r**2 - l1**2 - l2**2) / (2 * l1 * l2)
            cos_theta2 = max(-1, min(1, cos_theta2))
            
            theta2 = math.acos(cos_theta2)
            theta1 = math.atan2(y, x) - math.atan2(l2 * math.sin(theta2), l1 + l2 * math.cos(theta2))
            
            return math.degrees(theta1), math.degrees(theta2)
        
        # Test trajectory points
        test_points = [(0.0, 0.16), (0.1, 0.16), (0.05, 0.18)]
        
        for x, y in test_points:
            j1, j2 = simple_ik(x, y)
            if j1 is not None:
                print(f"✅ IK({x:.2f}, {y:.2f}) → ({j1:.1f}°, {j2:.1f}°)")
            else:
                print(f"❌ IK({x:.2f}, {y:.2f}) → Out of workspace")
        
        print("✅ Robot simulation: Working")
        return True
        
    except Exception as e:
        print(f"❌ Robot simulation test failed: {e}")
        return False

def test_robot_hardware():
    """测试真实机器人硬件"""
    print("🔌 Testing robot hardware...")
    
    try:
        from lerobot.robots.so100_follower import SO100Follower, SO100FollowerConfig
        
        # Check for common robot ports
        robot_ports = ["/dev/ttyACM0", "/dev/ttyACM1", "/dev/ttyUSB0"]
        
        for port in robot_ports:
            if os.path.exists(port):
                print(f"✅ Found potential robot port: {port}")
                # Don't actually connect to avoid conflicts
                return True
        
        print("⚠️  No robot ports found (this is OK for simulation)")
        return False
        
    except ImportError:
        print("⚠️  Robot hardware modules not available (simulation only)")
        return False
    except Exception as e:
        print(f"❌ Robot hardware test failed: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 Demo Component Test Suite")
    print("="*50)
    
    tests = [
        ("Camera", test_camera),
        ("YOLO", test_yolo),
        ("Audio", test_audio),
        ("Robot Simulation", test_robot_simulation),
        ("Robot Hardware", test_robot_hardware),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} Test")
        print("-" * 30)
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Results Summary")
    print("="*50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} : {status}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    if results.get("Camera"):
        print("✅ Camera ready - can run interactive demo")
    else:
        print("⚠️  No camera - use automatic demo mode")
    
    if results.get("YOLO"):
        print("✅ YOLO ready - object detection available")
    else:
        print("❌ YOLO failed - check ultralytics installation")
    
    if results.get("Audio"):
        print("✅ Audio ready - sound alerts available")
    else:
        print("⚠️  Audio issues - will use visual alerts")
    
    if results.get("Robot Hardware"):
        print("✅ Robot hardware detected - can use real robot")
    else:
        print("🎮 Robot hardware not found - use simulation mode")
    
    # Overall recommendation
    working_components = sum(1 for r in results.values() if r)
    total_components = len(results)
    
    print(f"\n🎯 Overall: {working_components}/{total_components} components working")
    
    if working_components >= 3:
        print("🚀 Ready to run demo! Try: python demo_simple.py")
    elif working_components >= 2:
        print("⚠️  Some issues detected, but demo should still work")
    else:
        print("❌ Multiple issues - check installation and hardware")

if __name__ == "__main__":
    main()
