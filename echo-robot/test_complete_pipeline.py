#!/usr/bin/env python3
"""
Complete Echo Robot Pipeline Demo
完整的Echo机器人流水线演示

This script demonstrates the complete pipeline:
1. Camera calibration validation
2. YOLO bottle detection
3. Coordinate transformation using calibrated camera
4. 3D trajectory planning
5. Robot control integration

Run this to test the complete system without actually moving the robot.
"""

import cv2
import numpy as np
import json
import math
from ultralytics import YOLO
from trajectory_planner import TrajectoryPlanner

def test_camera_calibration():
    """Test camera calibration loading"""
    print("1️⃣ Testing Camera Calibration")
    print("-" * 40)
    
    try:
        with open('config/camera_params.json', 'r') as f:
            params = json.load(f)
        
        print("✅ Camera calibration parameters loaded:")
        print(f"   Calibration Date: {params.get('calibration_date', 'Unknown')}")
        print(f"   Square Size: {params.get('square_size', 'Unknown')}mm")
        print(f"   Reprojection Error: {params.get('reprojection_error', 'Unknown')} pixels")
        
        camera_matrix = np.array(params['camera_matrix'])
        print(f"   Camera Matrix:")
        print(f"     fx: {camera_matrix[0,0]:.2f}, fy: {camera_matrix[1,1]:.2f}")
        print(f"     cx: {camera_matrix[0,2]:.2f}, cy: {camera_matrix[1,2]:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Failed to load camera calibration: {e}")
        return False

def test_yolo_detection():
    """Test YOLO model loading and detection capability"""
    print("\n2️⃣ Testing YOLO Detection")
    print("-" * 40)
    
    try:
        model = YOLO("yolov8n.pt")
        print("✅ YOLO model loaded successfully")
        
        # Test model classes
        if 'bottle' in model.names.values():
            print("✅ 'bottle' class found in model")
        else:
            print("⚠️  'bottle' class not found, available classes:")
            for i, name in model.names.items():
                if 'cup' in name or 'bottle' in name or 'can' in name:
                    print(f"   {i}: {name}")
        
        return model
    except Exception as e:
        print(f"❌ Failed to load YOLO model: {e}")
        return None

def test_trajectory_planning():
    """Test trajectory planning"""
    print("\n3️⃣ Testing Trajectory Planning")
    print("-" * 40)
    
    try:
        planner = TrajectoryPlanner()
        
        # Test with multiple bottle positions
        test_bottles = [
            {'world_x': 0.15, 'world_y': 0.0, 'world_z': 0.0, 'confidence': 0.9},
            {'world_x': 0.18, 'world_y': 0.05, 'world_z': 0.0, 'confidence': 0.8},
            {'world_x': 0.20, 'world_y': -0.08, 'world_z': 0.0, 'confidence': 0.7},
        ]
        
        for i, bottle in enumerate(test_bottles):
            print(f"\n   Test {i+1}: Bottle at ({bottle['world_x']}, {bottle['world_y']}, {bottle['world_z']})")
            
            # Test different push directions
            push_directions = [0, math.pi/4, math.pi/2]  # 0°, 45°, 90°
            
            for angle in push_directions:
                trajectory = planner.generate_push_trajectory(bottle, angle)
                angle_deg = math.degrees(angle)
                print(f"     ✅ Generated {len(trajectory)} waypoints for {angle_deg:.0f}° push")
        
        return True
    except Exception as e:
        print(f"❌ Trajectory planning failed: {e}")
        return False

def test_coordinate_transformation():
    """Test pixel to world coordinate transformation"""
    print("\n4️⃣ Testing Coordinate Transformation")
    print("-" * 40)
    
    try:
        planner = TrajectoryPlanner()
        
        # Test pixel coordinates (assuming 640x480 image)
        test_pixels = [
            (320, 240),  # Center
            (160, 240),  # Left
            (480, 240),  # Right
            (320, 120),  # Top
            (320, 360),  # Bottom
        ]
        
        print("   Pixel → World coordinate transformations:")
        for px, py in test_pixels:
            world_x, world_y = planner.pixel_to_world(px, py)
            if world_x is not None:
                print(f"     ({px:3d}, {py:3d}) → ({world_x:.3f}, {world_y:.3f})")
            else:
                print(f"     ({px:3d}, {py:3d}) → Failed")
        
        return True
    except Exception as e:
        print(f"❌ Coordinate transformation failed: {e}")
        return False

def test_live_detection(camera_id=0, duration=10):
    """Test live bottle detection"""
    print(f"\n5️⃣ Testing Live Detection (Camera {camera_id})")
    print("-" * 40)
    print(f"   Testing for {duration} seconds. Press 'q' to quit early.")
    
    try:
        # Initialize camera
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Cannot open camera {camera_id}")
            return False
        
        # Initialize YOLO and planner
        model = YOLO("yolov8n.pt")
        planner = TrajectoryPlanner()
        
        start_time = cv2.getTickCount()
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            # Detect bottles
            bottles = planner.detect_bottles(frame, model)
            
            # Draw detections
            results = model(frame)
            annotated_frame = results[0].plot()
            
            # Add info overlay
            cv2.putText(annotated_frame, f"Bottles in workspace: {len(bottles)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Draw workspace center
            h, w = frame.shape[:2]
            cv2.circle(annotated_frame, (w//2, h//2), 5, (0, 255, 255), -1)
            cv2.putText(annotated_frame, "Center", (w//2 + 10, h//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            # Show bottle coordinates
            for i, bottle in enumerate(bottles):
                px, py = int(bottle['pixel_x']), int(bottle['pixel_y'])
                wx, wy = bottle['world_x'], bottle['world_y']
                cv2.putText(annotated_frame, f"({wx:.3f}, {wy:.3f})", 
                           (px, py - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
            
            cv2.imshow("Live Bottle Detection", annotated_frame)
            
            # Check for quit or timeout
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            elapsed = (cv2.getTickCount() - start_time) / cv2.getTickFrequency()
            if elapsed > duration:
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        print("✅ Live detection test completed")
        return True
        
    except Exception as e:
        print(f"❌ Live detection failed: {e}")
        return False

def test_integration_pipeline():
    """Test the complete integration pipeline"""
    print("\n6️⃣ Testing Complete Integration Pipeline")
    print("-" * 40)
    
    try:
        # Simulate detected bottle
        mock_bottle = {
            'pixel_x': 350,
            'pixel_y': 280,
            'world_x': 0.17,
            'world_y': 0.04,
            'world_z': 0.0,
            'confidence': 0.85,
            'bbox': (320, 240, 380, 320)
        }
        
        print(f"   📍 Mock bottle detected at pixel ({mock_bottle['pixel_x']}, {mock_bottle['pixel_y']})")
        print(f"   🌍 World coordinates: ({mock_bottle['world_x']:.3f}, {mock_bottle['world_y']:.3f}, {mock_bottle['world_z']:.3f})")
        
        # Generate trajectory
        planner = TrajectoryPlanner()
        push_angle = math.radians(30)  # 30-degree push
        trajectory = planner.generate_push_trajectory(mock_bottle, push_angle)
        
        print(f"   🛤️  Generated trajectory with {len(trajectory)} waypoints")
        
        # Apply smoothing
        smooth_trajectory = planner.smooth_trajectory(trajectory)
        print("   🔧 Applied trajectory smoothing")
        
        # Simulate execution timing
        total_duration = sum(wp['duration'] for wp in smooth_trajectory)
        print(f"   ⏱️  Estimated execution time: {total_duration:.1f} seconds")
        
        # Check workspace safety
        workspace_safe = True
        for wp in smooth_trajectory:
            coords = wp['world_coords']
            if not (planner.workspace_limits['x_min'] <= coords['x'] <= planner.workspace_limits['x_max'] and
                    planner.workspace_limits['y_min'] <= coords['y'] <= planner.workspace_limits['y_max'] and
                    planner.workspace_limits['z_min'] <= coords['z'] <= planner.workspace_limits['z_max']):
                workspace_safe = False
                break
        
        if workspace_safe:
            print("   ✅ All waypoints within safe workspace")
        else:
            print("   ⚠️  Some waypoints outside workspace limits")
        
        # Visualize if requested
        print("\n   Would you like to visualize this trajectory? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response == 'y':
                planner.visualize_trajectory(smooth_trajectory)
        except:
            pass  # Handle case where input is not available
        
        return True
        
    except Exception as e:
        print(f"❌ Integration pipeline failed: {e}")
        return False

def main():
    """Run complete system test"""
    print("🚀 Echo Robot Complete System Test")
    print("=" * 50)
    print("This test validates all components of the vision-based robot control system")
    print()
    
    # Run all tests
    tests = [
        ("Camera Calibration", test_camera_calibration),
        ("YOLO Detection", test_yolo_detection),
        ("Coordinate Transformation", test_coordinate_transformation),
        ("Trajectory Planning", test_trajectory_planning),
        ("Integration Pipeline", test_integration_pipeline),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if test_name == "YOLO Detection":
                # YOLO test returns model, not just boolean
                result = test_func()
                results[test_name] = result is not None
            else:
                results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Optional live test
    print("\n" + "=" * 50)
    print("🎥 Live Detection Test (Optional)")
    print("Would you like to run a live camera test? (y/n): ", end="")
    try:
        response = input().strip().lower()
        if response == 'y':
            camera_id = input("Enter camera ID (default 0): ").strip()
            camera_id = int(camera_id) if camera_id else 0
            results["Live Detection"] = test_live_detection(camera_id)
    except:
        pass
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("-" * 30)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        if not passed:
            all_passed = False
    
    print("-" * 30)
    if all_passed:
        print("🎉 ALL TESTS PASSED! System ready for robot integration.")
        print("\nNext steps:")
        print("1. Run 'python vision_trajectory_control.py' to control the robot")
        print("2. Use mode 1 for autonomous bottle pushing")
        print("3. Use mode 2 for manual trajectory testing")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        print("Make sure camera calibration is completed and YOLO model is available.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
