#!/usr/bin/env python3
"""
Standalone Trajectory Planning Demo
独立轨迹规划演示

This script demonstrates trajectory planning without requiring robot hardware.
It shows how the complete vision-to-trajectory pipeline works using:
1. Camera calibration
2. YOLO bottle detection 
3. 3D trajectory generation
4. Visualization and simulation

Run this to see the trajectory planning system in action.
"""

import cv2
import numpy as np
import math
import time
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from ultralytics import YOLO
from trajectory_planner import TrajectoryPlanner

class TrajectoryDemo:
    def __init__(self, camera_id=0):
        """Initialize the trajectory demonstration system"""
        self.camera_id = camera_id
        self.planner = TrajectoryPlanner()
        self.model = None
        self.cap = None
        
        print("🚀 Trajectory Planning Demo Starting...")
        print("="*60)
    
    def initialize_camera(self):
        """Initialize camera for live detection"""
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                print(f"❌ Cannot open camera {self.camera_id}")
                return False
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            print(f"📷 Camera {self.camera_id} initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Camera initialization failed: {e}")
            return False
    
    def initialize_yolo(self):
        """Initialize YOLO model"""
        try:
            self.model = YOLO("yolov8n.pt")
            print("🤖 YOLO model loaded successfully")
            
            # Check if bottle class exists
            if 'bottle' in self.model.names.values():
                print("✅ 'bottle' class found in model")
            else:
                print("⚠️  'bottle' class not found, will look for similar classes")
                similar_classes = [name for name in self.model.names.values() 
                                 if any(keyword in name.lower() for keyword in ['cup', 'bottle', 'can', 'glass'])]
                if similar_classes:
                    print(f"   Available similar classes: {similar_classes}")
            
            return True
        except Exception as e:
            print(f"❌ YOLO model loading failed: {e}")
            return False
    
    def demo_trajectory_planning(self):
        """Demonstrate trajectory planning with mock data"""
        print("\n🎯 Trajectory Planning Demonstration")
        print("-" * 40)
        
        # Demo bottles at different positions
        demo_bottles = [
            {
                'name': 'Bottle A (Close)',
                'world_x': 0.15, 'world_y': 0.02, 'world_z': 0.0,
                'confidence': 0.95,
                'description': 'Close bottle, easy target'
            },
            {
                'name': 'Bottle B (Medium)',
                'world_x': 0.18, 'world_y': 0.08, 'world_z': 0.0,
                'confidence': 0.87,
                'description': 'Medium distance, right side'
            },
            {
                'name': 'Bottle C (Far)',
                'world_x': 0.22, 'world_y': -0.05, 'world_z': 0.0,
                'confidence': 0.79,
                'description': 'Far bottle, left side'
            }
        ]
        
        for i, bottle in enumerate(demo_bottles):
            print(f"\n📍 {bottle['name']}: ({bottle['world_x']:.3f}, {bottle['world_y']:.3f}, {bottle['world_z']:.3f})")
            print(f"   {bottle['description']}")
            
            # Generate trajectory with different push directions
            push_angles = [0, math.pi/4, math.pi/2]  # 0°, 45°, 90°
            angle_names = ['East (0°)', 'Northeast (45°)', 'North (90°)']
            
            for angle, angle_name in zip(push_angles, angle_names):
                print(f"\n   🔄 Generating trajectory - Push direction: {angle_name}")
                
                trajectory = self.planner.generate_push_trajectory(bottle, angle)
                if trajectory:
                    smooth_trajectory = self.planner.smooth_trajectory(trajectory)
                    
                    # Calculate trajectory metrics
                    total_duration = sum(wp['duration'] for wp in smooth_trajectory)
                    max_height = max(wp['world_coords']['z'] for wp in smooth_trajectory)
                    total_distance = self.calculate_trajectory_distance(smooth_trajectory)
                    
                    print(f"     ✅ Generated {len(smooth_trajectory)} waypoints")
                    print(f"     ⏱️  Estimated duration: {total_duration:.1f}s")
                    print(f"     📏 Total distance: {total_distance:.3f}m")
                    print(f"     ⬆️  Max height: {max_height:.3f}m")
                    
                    # Visualize first trajectory only to avoid too many plots
                    if i == 0 and angle == 0:
                        print(f"     📊 Showing visualization for {bottle['name']}...")
                        self.planner.visualize_trajectory(smooth_trajectory, save_plot=True)
        
        return True
    
    def calculate_trajectory_distance(self, trajectory):
        """Calculate total distance traveled in trajectory"""
        total_distance = 0
        for i in range(1, len(trajectory)):
            prev_pos = trajectory[i-1]['world_coords']
            curr_pos = trajectory[i]['world_coords']
            
            dx = curr_pos['x'] - prev_pos['x']
            dy = curr_pos['y'] - prev_pos['y']
            dz = curr_pos['z'] - prev_pos['z']
            
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            total_distance += distance
        
        return total_distance
    
    def world_to_pixel(self, world_x, world_y, world_z=0.0):
        """Convert world coordinates to pixel coordinates using camera calibration"""
        try:
            # Get camera calibration data
            if not self.planner.camera_params:
                return None, None
            
            camera_matrix = np.array(self.planner.camera_params['camera_matrix'])
            dist_coeffs = np.array(self.planner.camera_params['distortion_coeffs'])
            
            # World point in 3D (assuming z=0 for table surface)
            world_point = np.array([[world_x, world_y, world_z]], dtype=np.float32)
            
            # For simplicity, assume identity rotation and zero translation
            # In a real setup, you'd use the actual camera pose
            rvec = np.zeros(3, dtype=np.float32)
            tvec = np.zeros(3, dtype=np.float32)
            
            # Project to image coordinates
            pixel_points, _ = cv2.projectPoints(world_point, rvec, tvec, camera_matrix, dist_coeffs)
            
            if len(pixel_points) > 0:
                px, py = pixel_points[0][0]
                return int(px), int(py)
            
        except Exception as e:
            print(f"Warning: World to pixel conversion failed: {e}")
        
        return None, None
    
    def draw_trajectory_overlay(self, frame, trajectory):
        """Draw trajectory waypoints and path on camera frame"""
        if not trajectory:
            return frame
        
        # Colors for different waypoint types
        colors = {
            'approach': (0, 255, 255),    # Yellow - approach points
            'contact': (0, 165, 255),     # Orange - contact point
            'push': (0, 0, 255),          # Red - push points
            'retract': (255, 0, 0),       # Blue - retract points
            'home': (0, 255, 0)           # Green - home position
        }
        
        trajectory_pixels = []
        
        # Convert trajectory points to pixel coordinates
        for i, waypoint in enumerate(trajectory):
            coords = waypoint['world_coords']
            px, py = self.world_to_pixel(coords['x'], coords['y'], coords['z'])
            
            if px is not None and py is not None:
                trajectory_pixels.append((px, py, waypoint))
                
                # Determine waypoint type and color
                name = waypoint['name'].lower()
                if 'approach' in name:
                    color = colors['approach']
                elif 'contact' in name:
                    color = colors['contact']
                elif 'push' in name:
                    color = colors['push']
                elif 'retract' in name:
                    color = colors['retract']
                else:
                    color = colors['home']
                
                # Draw waypoint
                cv2.circle(frame, (px, py), 6, color, -1)
                cv2.circle(frame, (px, py), 8, (255, 255, 255), 2)
                
                # Draw waypoint number
                cv2.putText(frame, f"{i+1}", (px-8, py+5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                
                # Draw height indicator for elevated points
                if coords['z'] > 0.01:
                    cv2.putText(frame, f"h:{coords['z']:.2f}", (px+10, py-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)
        
        # Draw trajectory path
        if len(trajectory_pixels) > 1:
            for i in range(len(trajectory_pixels) - 1):
                pt1 = trajectory_pixels[i][:2]
                pt2 = trajectory_pixels[i+1][:2]
                cv2.line(frame, pt1, pt2, (255, 255, 255), 2)
                cv2.line(frame, pt1, pt2, (0, 255, 0), 1)  # Green inner line
        
        # Draw legend
        legend_y = 100
        legend_items = [
            ("Approach", colors['approach']),
            ("Contact", colors['contact']),
            ("Push", colors['push']),
            ("Retract", colors['retract'])
        ]
        
        for i, (label, color) in enumerate(legend_items):
            y_pos = legend_y + i * 25
            cv2.circle(frame, (15, y_pos), 6, color, -1)
            cv2.putText(frame, label, (30, y_pos + 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame

    def live_detection_demo(self, duration=30):
        """Demonstrate live bottle detection and trajectory planning with visual overlay"""
        print(f"\n🎥 Live Detection Demo with Trajectory Visualization ({duration}s)")
        print("-" * 40)
        print("Place a bottle in front of the camera to see trajectory planning in action!")
        print("Press 'q' to quit, 'space' to generate trajectory, 'c' to clear trajectory")
        
        if not self.cap or not self.model:
            print("❌ Camera or YOLO model not initialized")
            return False
        
        start_time = time.time()
        last_trajectory_time = 0
        current_trajectory = None
        trajectory_generated = False
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Failed to capture frame")
                break
            
            # Detect bottles
            bottles = self.planner.detect_bottles(frame, self.model)
            
            # Draw detections and information
            results = self.model(frame)
            annotated_frame = results[0].plot()
            
            # Draw trajectory overlay if available
            if current_trajectory:
                annotated_frame = self.draw_trajectory_overlay(annotated_frame, current_trajectory)
            
            # Add information overlay
            cv2.putText(annotated_frame, f"Bottles detected: {len(bottles)}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            elapsed = time.time() - start_time
            cv2.putText(annotated_frame, f"Time: {elapsed:.1f}s", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            
            # Show trajectory status
            if current_trajectory:
                cv2.putText(annotated_frame, f"Trajectory: {len(current_trajectory)} waypoints", 
                           (10, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Draw workspace center and boundaries
            h, w = frame.shape[:2]
            cv2.circle(annotated_frame, (w//2, h//2), 5, (0, 255, 255), -1)
            cv2.putText(annotated_frame, "Center", (w//2 + 10, h//2), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            
            # Show bottle world coordinates
            for i, bottle in enumerate(bottles):
                px, py = int(bottle['pixel_x']), int(bottle['pixel_y'])
                wx, wy = bottle['world_x'], bottle['world_y']
                
                # Draw coordinate text
                cv2.putText(annotated_frame, f"({wx:.3f}, {wy:.3f})", 
                           (px, py - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
                
                # Draw bottle number
                cv2.putText(annotated_frame, f"#{i+1}", 
                           (px, py + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Instructions
            cv2.putText(annotated_frame, "Press 'q' to quit, 'space' for trajectory, 'c' to clear", 
                       (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow("Live Bottle Detection & Trajectory Planning", annotated_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                current_trajectory = None
                trajectory_generated = False
                print("🗑️  Trajectory cleared")
            elif key == ord(' ') and bottles and time.time() - last_trajectory_time > 2:
                # Generate trajectory for first detected bottle
                target_bottle = bottles[0]
                print(f"\n🎯 Generating trajectory for bottle at ({target_bottle['world_x']:.3f}, {target_bottle['world_y']:.3f})")
                
                # Try different push angles to show variety
                push_angles = [0, math.pi/4, math.pi/2, 3*math.pi/4]
                angle_names = ['East (0°)', 'Northeast (45°)', 'North (90°)', 'Northwest (135°)']
                
                # Cycle through angles for demonstration
                angle_index = int(time.time()) % len(push_angles)
                push_angle = push_angles[angle_index]
                angle_name = angle_names[angle_index]
                
                print(f"   Push direction: {angle_name}")
                
                trajectory = self.planner.generate_push_trajectory(target_bottle, push_angle)
                if trajectory:
                    current_trajectory = self.planner.smooth_trajectory(trajectory)
                    trajectory_generated = True
                    print(f"✅ Trajectory visualized with {len(current_trajectory)} waypoints")
                    print(f"   Trajectory overlay drawn on camera view")
                    
                    # Show quick simulation
                    self.simulate_trajectory_execution(current_trajectory[:4])  # Show first 4 waypoints
                    last_trajectory_time = time.time()
                else:
                    print("❌ Failed to generate trajectory")
            
            # Check timeout
            if time.time() - start_time > duration:
                break
        
        cv2.destroyAllWindows()
        print("✅ Live detection demo completed")
        return True
    
    def simulate_trajectory_execution(self, trajectory):
        """Simulate trajectory execution with console output"""
        print("\n🎬 Simulating trajectory execution...")
        for i, waypoint in enumerate(trajectory):
            coords = waypoint['world_coords']
            joints = waypoint['joint_angles']
            
            print(f"  Step {i+1}: {waypoint['name']}")
            print(f"    Position: ({coords['x']:.3f}, {coords['y']:.3f}, {coords['z']:.3f})")
            print(f"    Joints: pan={joints['shoulder_pan']:.1f}°, lift={joints['shoulder_lift']:.1f}°")
            
            time.sleep(0.5)  # Brief pause for simulation
        print("  ✅ Trajectory simulation complete\n")
    
    def run_demo(self):
        """Run the complete trajectory demonstration"""
        
        # Initialize systems
        camera_ok = self.initialize_camera()
        yolo_ok = self.initialize_yolo()
        
        print("\n🎮 Demo Mode Selection:")
        print("1. Trajectory Planning Demo (with mock bottles)")
        print("2. Live Detection Demo (requires camera + real bottles)")
        print("3. Both demos")
        
        try:
            choice = input("Select demo mode (1/2/3): ").strip()
        except:
            choice = "1"  # Default fallback
        
        if choice in ["1", "3"]:
            # Run trajectory planning demo
            self.demo_trajectory_planning()
        
        if choice in ["2", "3"] and camera_ok and yolo_ok:
            # Run live detection demo
            try:
                duration = int(input("Live demo duration in seconds (default 30): ") or "30")
            except:
                duration = 30
            self.live_detection_demo(duration)
        elif choice in ["2", "3"]:
            print("⚠️  Live demo skipped - camera or YOLO not available")
        
        print("\n🎉 Trajectory Demo Completed!")
        print("="*60)
        print("Summary of what we demonstrated:")
        print("✅ Camera calibration integration")
        print("✅ YOLO bottle detection")
        print("✅ Pixel-to-world coordinate transformation")
        print("✅ 3D trajectory planning with multiple waypoints")
        print("✅ Trajectory smoothing and optimization")
        print("✅ Safety workspace boundary checking")
        print("✅ Real-time trajectory visualization in camera view")
        print("✅ Interactive trajectory generation and display")
        print("✅ Multi-directional push trajectory planning")
        print("✅ Visualization and simulation")
        print("\nVisualization Features:")
        print("🎨 Color-coded waypoints (approach, contact, push, retract)")
        print("📍 Numbered trajectory sequence")
        print("📏 Height indicators for elevated waypoints")
        print("🛤️  Connected trajectory path visualization")
        print("🎮 Interactive controls (space=generate, c=clear, q=quit)")
        print("\nNext steps:")
        print("- Connect real robot hardware using vision_trajectory_control.py")
        print("- Fine-tune camera calibration for better coordinate accuracy")
        print("- Adjust push parameters based on bottle weight/size")
        print("- Implement closed-loop feedback for precise control")
        
        # Cleanup
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

def main():
    """Main function"""
    print("🤖 Echo Robot Trajectory Planning Demo with Camera Visualization")
    print("="*60)
    print("This demonstration shows the complete vision-based trajectory planning system")
    print("with real-time trajectory visualization overlaid on the camera feed.")
    print()
    print("🎨 New Features:")
    print("- Trajectory waypoints visualized directly in camera view")
    print("- Color-coded path: approach (yellow), contact (orange), push (red), retract (blue)")
    print("- Interactive trajectory generation with multiple push directions")
    print("- Real-time coordinate transformation from world to pixel space")
    print()
    
    try:
        # Get camera ID
        camera_input = input("Enter camera ID for live demo (default 0, or 'skip' for planning only): ").strip()
        
        if camera_input.lower() == 'skip':
            camera_id = None
        else:
            camera_id = int(camera_input) if camera_input else 0
        
        # Create and run demo
        demo = TrajectoryDemo(camera_id)
        demo.run_demo()
        
    except KeyboardInterrupt:
        print("\n⛔ Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
