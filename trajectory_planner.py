#!/usr/bin/env python3
"""
Trajectory Planner for LeRobot SO-100
3D轨迹规划器

This module handles:
1. 3D trajectory generation for bottle pushing
2. Inverse kinematics calculations
3. Trajectory smoothing and optimization
4. Safety boundary checking
5. Camera calibration integration
"""

import numpy as np
import math
import json
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import cv2

class TrajectoryPlanner:
    def __init__(self):
        """Initialize trajectory planner"""
        # Robot parameters (LeRobot SO-100)
        self.l1 = 0.1159  # First link length (m)
        self.l2 = 0.1350  # Second link length (m)
        
        # Workspace boundaries (safety limits)
        self.workspace = {
            'x_min': 0.10, 'x_max': 0.25,
            'y_min': -0.12, 'y_max': 0.12,
            'z_min': 0.05, 'z_max': 0.20
        }
        
        # Push parameters
        self.push_distance = 0.05  # Distance to push bottle (m)
        self.approach_height = 0.12  # Height for approach (m)
        self.contact_height = 0.08   # Height for contact (m)
        self.safe_height = 0.15     # Safe travel height (m)
        
        # Camera calibration
        self.camera_params = None
        self.load_camera_params()
        
        print("✅ Trajectory planner initialized")
    
    def load_camera_params(self):
        """Load camera calibration parameters"""
        try:
            config_path = 'config/camera_params.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.camera_params = json.load(f)
                print(f"📂 Camera calibration loaded: {config_path}")
                return True
            else:
                print("⚠️  No camera calibration found - using default parameters")
                return False
        except Exception as e:
            print(f"❌ Failed to load camera calibration: {e}")
            return False
    
    def detect_bottles(self, frame, model):
        """Detect bottles in camera frame and convert to world coordinates"""
        bottles = []
        
        try:
            # Run YOLO detection
            results = model(frame)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class and confidence
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        class_name = model.names[cls]
                        
                        # Check if it's a bottle (or similar object)
                        if ('bottle' in class_name.lower() or 
                            'cup' in class_name.lower() or
                            'can' in class_name.lower()) and conf > 0.3:
                            
                            # Get bounding box
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            
                            # Calculate center point
                            center_x = int((x1 + x2) / 2)
                            center_y = int((y1 + y2) / 2)
                            
                            # Convert to world coordinates
                            world_x, world_y = self.pixel_to_world(center_x, center_y)
                            
                            # Check if within workspace
                            if self.is_in_workspace(world_x, world_y, 0.0):
                                bottle = {
                                    'pixel_x': center_x,
                                    'pixel_y': center_y,
                                    'world_x': world_x,
                                    'world_y': world_y,
                                    'world_z': 0.0,  # Assume on table surface
                                    'confidence': conf,
                                    'class': class_name,
                                    'bbox': [x1, y1, x2, y2]
                                }
                                bottles.append(bottle)
            
            if bottles:
                print(f"🔍 Detected {len(bottles)} bottles in workspace")
            
        except Exception as e:
            print(f"❌ Bottle detection failed: {e}")
        
        return bottles
    
    def pixel_to_world(self, pixel_x, pixel_y):
        """Convert pixel coordinates to world coordinates"""
        try:
            if not self.camera_params:
                # Use simple approximation if no calibration available
                # This is a rough estimate and should be replaced with proper calibration
                world_x = 0.15 + (pixel_x - 320) * 0.0003  # Rough scaling
                world_y = (pixel_y - 240) * 0.0003
                return world_x, world_y
            
            # Use camera calibration for accurate conversion
            camera_matrix = np.array(self.camera_params['camera_matrix'])
            dist_coeffs = np.array(self.camera_params['distortion_coeffs'])
            
            # Undistort pixel point
            pixel_point = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
            undistorted = cv2.undistortPoints(pixel_point, camera_matrix, dist_coeffs, 
                                            None, camera_matrix)[0][0]
            
            # Convert to world coordinates (assuming table height = 0)
            # This requires proper camera pose calibration
            fx = camera_matrix[0, 0]
            fy = camera_matrix[1, 1]
            cx = camera_matrix[0, 2]
            cy = camera_matrix[1, 2]
            
            # Simple projection (assumes camera looking down at table)
            # Real implementation would need camera pose relative to robot base
            table_height = 0.75  # Estimated table height (m)
            world_x = (undistorted[0] - cx) * table_height / fx
            world_y = (undistorted[1] - cy) * table_height / fy
            
            # Adjust for robot coordinate system
            world_x = 0.15 + world_x * 0.3  # Scale and offset
            world_y = world_y * 0.3
            
            return world_x, world_y
            
        except Exception as e:
            print(f"Warning: Pixel to world conversion failed: {e}")
            # Fallback to simple approximation
            world_x = 0.15 + (pixel_x - 320) * 0.0003
            world_y = (pixel_y - 240) * 0.0003
            return world_x, world_y
    
    def is_in_workspace(self, x, y, z):
        """Check if coordinates are within robot workspace"""
        return (self.workspace['x_min'] <= x <= self.workspace['x_max'] and
                self.workspace['y_min'] <= y <= self.workspace['y_max'] and
                self.workspace['z_min'] <= z <= self.workspace['z_max'])
    
    def inverse_kinematics(self, x, y, z=None):
        """Calculate inverse kinematics for 2D planar arm"""
        try:
            # For 2D case (z not used for SO-100 planar arm)
            distance = math.sqrt(x*x + y*y)
            
            # Check if target is reachable
            if distance > (self.l1 + self.l2) or distance < abs(self.l1 - self.l2):
                return None
            
            # Calculate joint angles using cosine rule
            cos_q2 = (distance*distance - self.l1*self.l1 - self.l2*self.l2) / (2 * self.l1 * self.l2)
            cos_q2 = max(-1, min(1, cos_q2))  # Clamp to valid range
            
            q2 = math.acos(cos_q2)  # Elbow up configuration
            
            # Calculate first joint angle
            alpha = math.atan2(y, x)
            beta = math.atan2(self.l2 * math.sin(q2), self.l1 + self.l2 * math.cos(q2))
            q1 = alpha - beta
            
            # Convert to degrees
            joint_angles = {
                'shoulder_pan': math.degrees(math.atan2(y, x)),  # Base rotation
                'shoulder_lift': math.degrees(q1),               # First joint
                'elbow_flex': math.degrees(q2),                  # Second joint
                'wrist_flex': 0.0,                               # Wrist pitch
                'wrist_roll': 0.0,                               # Wrist roll
                'gripper': 0.0                                   # Gripper
            }
            
            return joint_angles
            
        except Exception as e:
            print(f"❌ IK calculation failed: {e}")
            return None
    
    def generate_push_trajectory(self, bottle, push_angle=0):
        """Generate trajectory for pushing a bottle"""
        try:
            # Start position
            start_x, start_y = bottle['world_x'], bottle['world_y']
            
            # Calculate push direction
            push_dir_x = math.cos(push_angle)
            push_dir_y = math.sin(push_angle)
            
            # Define waypoints for bottle pushing
            waypoints = []
            
            # 1. Home position (current position)
            home_pos = {'x': 0.15, 'y': 0.0, 'z': self.safe_height}
            waypoints.append({
                'name': 'start',
                'world_coords': home_pos,
                'duration': 2.0
            })
            
            # 2. Above bottle (safe approach)
            above_bottle = {'x': start_x, 'y': start_y, 'z': self.approach_height}
            waypoints.append({
                'name': 'above_bottle',
                'world_coords': above_bottle,
                'duration': 2.0
            })
            
            # 3. Approach position (before contact)
            approach_offset = 0.03  # 3cm before bottle
            approach_x = start_x - push_dir_x * approach_offset
            approach_y = start_y - push_dir_y * approach_offset
            approach_pos = {'x': approach_x, 'y': approach_y, 'z': self.contact_height}
            waypoints.append({
                'name': 'approach',
                'world_coords': approach_pos,
                'duration': 1.5
            })
            
            # 4. Pre-contact position
            precontact_offset = 0.01  # 1cm before bottle
            precontact_x = start_x - push_dir_x * precontact_offset
            precontact_y = start_y - push_dir_y * precontact_offset
            precontact_pos = {'x': precontact_x, 'y': precontact_y, 'z': self.contact_height}
            waypoints.append({
                'name': 'pre_contact',
                'world_coords': precontact_pos,
                'duration': 1.0
            })
            
            # 5. Contact position (touch bottle)
            contact_pos = {'x': start_x, 'y': start_y, 'z': self.contact_height}
            waypoints.append({
                'name': 'contact',
                'world_coords': contact_pos,
                'duration': 0.5
            })
            
            # 6. Push through (push bottle)
            push_x = start_x + push_dir_x * self.push_distance
            push_y = start_y + push_dir_y * self.push_distance
            push_pos = {'x': push_x, 'y': push_y, 'z': self.contact_height}
            waypoints.append({
                'name': 'push_through',
                'world_coords': push_pos,
                'duration': 2.0
            })
            
            # 7. Retract (lift up)
            retract_pos = {'x': push_x, 'y': push_y, 'z': self.approach_height}
            waypoints.append({
                'name': 'retract',
                'world_coords': retract_pos,
                'duration': 1.5
            })
            
            # 8. Return home
            waypoints.append({
                'name': 'return_home',
                'world_coords': home_pos,
                'duration': 3.0
            })
            
            # Calculate joint angles for each waypoint
            for waypoint in waypoints:
                coords = waypoint['world_coords']
                joint_angles = self.inverse_kinematics(coords['x'], coords['y'], coords['z'])
                
                if joint_angles is None:
                    print(f"❌ IK failed for waypoint {waypoint['name']}")
                    return None
                
                waypoint['joint_angles'] = joint_angles
            
            return waypoints
            
        except Exception as e:
            print(f"❌ Trajectory generation failed: {e}")
            return None
    
    def smooth_trajectory(self, trajectory):
        """Apply smoothing to trajectory waypoints"""
        if not trajectory:
            return trajectory
        
        # Simple smoothing - interpolate velocities
        smoothed = trajectory.copy()
        
        for i in range(1, len(smoothed) - 1):
            prev_wp = smoothed[i-1]
            curr_wp = smoothed[i]
            next_wp = smoothed[i+1]
            
            # Smooth duration based on distance
            prev_coords = prev_wp['world_coords']
            curr_coords = curr_wp['world_coords']
            next_coords = next_wp['world_coords']
            
            # Calculate distances
            dist_prev = math.sqrt(
                (curr_coords['x'] - prev_coords['x'])**2 +
                (curr_coords['y'] - prev_coords['y'])**2 +
                (curr_coords['z'] - prev_coords['z'])**2
            )
            
            dist_next = math.sqrt(
                (next_coords['x'] - curr_coords['x'])**2 +
                (next_coords['y'] - curr_coords['y'])**2 +
                (next_coords['z'] - curr_coords['z'])**2
            )
            
            # Adjust duration based on distance
            max_speed = 0.1  # m/s
            smoothed[i]['duration'] = max(0.5, max(dist_prev, dist_next) / max_speed)
        
        return smoothed
    
    def visualize_trajectory(self, trajectory, save_plot=False):
        """Visualize 3D trajectory"""
        if not trajectory:
            return
        
        try:
            fig = plt.figure(figsize=(12, 8))
            
            # 3D plot
            ax1 = fig.add_subplot(121, projection='3d')
            
            # Extract coordinates
            x_coords = [wp['world_coords']['x'] for wp in trajectory]
            y_coords = [wp['world_coords']['y'] for wp in trajectory]
            z_coords = [wp['world_coords']['z'] for wp in trajectory]
            
            # Plot trajectory path
            ax1.plot(x_coords, y_coords, z_coords, 'b-', linewidth=2, label='Trajectory')
            ax1.scatter(x_coords, y_coords, z_coords, c='red', s=50, label='Waypoints')
            
            # Add waypoint labels
            for i, wp in enumerate(trajectory):
                coords = wp['world_coords']
                ax1.text(coords['x'], coords['y'], coords['z'], 
                        f"{i+1}: {wp['name']}", fontsize=8)
            
            ax1.set_xlabel('X (m)')
            ax1.set_ylabel('Y (m)')
            ax1.set_zlabel('Z (m)')
            ax1.set_title('3D Trajectory Visualization')
            ax1.legend()
            
            # 2D top view
            ax2 = fig.add_subplot(122)
            ax2.plot(x_coords, y_coords, 'b-', linewidth=2, label='Trajectory')
            ax2.scatter(x_coords, y_coords, c='red', s=50, label='Waypoints')
            
            # Add workspace boundaries
            ws = self.workspace
            ax2.add_patch(plt.Rectangle((ws['x_min'], ws['y_min']), 
                                      ws['x_max']-ws['x_min'], ws['y_max']-ws['y_min'],
                                      fill=False, edgecolor='green', linestyle='--', 
                                      label='Workspace'))
            
            # Add waypoint labels
            for i, wp in enumerate(trajectory):
                coords = wp['world_coords']
                ax2.annotate(f"{i+1}", (coords['x'], coords['y']), 
                           xytext=(5, 5), textcoords='offset points', fontsize=8)
            
            ax2.set_xlabel('X (m)')
            ax2.set_ylabel('Y (m)')
            ax2.set_title('Top View')
            ax2.legend()
            ax2.grid(True)
            ax2.axis('equal')
            
            plt.tight_layout()
            
            if save_plot:
                plt.savefig('trajectory_visualization.png', dpi=150, bbox_inches='tight')
                print("📊 Trajectory plot saved as 'trajectory_visualization.png'")
            
            plt.show()
            
        except Exception as e:
            print(f"❌ Visualization failed: {e}")

def main():
    """Test the trajectory planner"""
    planner = TrajectoryPlanner()
    
    # Test bottle
    test_bottle = {
        'world_x': 0.18,
        'world_y': 0.05,
        'world_z': 0.0,
        'confidence': 0.9
    }
    
    print("🧪 Testing trajectory generation...")
    trajectory = planner.generate_push_trajectory(test_bottle, push_angle=math.pi/4)
    
    if trajectory:
        print(f"✅ Generated trajectory with {len(trajectory)} waypoints")
        
        # Smooth trajectory
        smooth_traj = planner.smooth_trajectory(trajectory)
        print(f"✅ Smoothed trajectory completed")
        
        # Visualize
        planner.visualize_trajectory(smooth_traj, save_plot=True)
    else:
        print("❌ Trajectory generation failed")

if __name__ == "__main__":
    main()
EOFcat > trajectory_planner.py << 'EOF'
#!/usr/bin/env python3
"""
Trajectory Planner for LeRobot SO-100
3D轨迹规划器

This module handles:
1. 3D trajectory generation for bottle pushing
2. Inverse kinematics calculations
3. Trajectory smoothing and optimization
4. Safety boundary checking
5. Camera calibration integration
"""

import numpy as np
import math
import json
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import cv2

class TrajectoryPlanner:
    def __init__(self):
        """Initialize trajectory planner"""
        # Robot parameters (LeRobot SO-100)
        self.l1 = 0.1159  # First link length (m)
        self.l2 = 0.1350  # Second link length (m)
        
        # Workspace boundaries (safety limits)
        self.workspace = {
            'x_min': 0.10, 'x_max': 0.25,
            'y_min': -0.12, 'y_max': 0.12,
            'z_min': 0.05, 'z_max': 0.20
        }
        
        # Push parameters
        self.push_distance = 0.05  # Distance to push bottle (m)
        self.approach_height = 0.12  # Height for approach (m)
        self.contact_height = 0.08   # Height for contact (m)
        self.safe_height = 0.15     # Safe travel height (m)
        
        # Camera calibration
        self.camera_params = None
        self.load_camera_params()
        
        print("✅ Trajectory planner initialized")
    
    def load_camera_params(self):
        """Load camera calibration parameters"""
        try:
            config_path = 'config/camera_params.json'
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.camera_params = json.load(f)
                print(f"📂 Camera calibration loaded: {config_path}")
                return True
            else:
                print("⚠️  No camera calibration found - using default parameters")
                return False
        except Exception as e:
            print(f"❌ Failed to load camera calibration: {e}")
            return False
    
    def detect_bottles(self, frame, model):
        """Detect bottles in camera frame and convert to world coordinates"""
        bottles = []
        
        try:
            # Run YOLO detection
            results = model(frame)
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class and confidence
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        class_name = model.names[cls]
                        
                        # Check if it's a bottle (or similar object)
                        if ('bottle' in class_name.lower() or 
                            'cup' in class_name.lower() or
                            'can' in class_name.lower()) and conf > 0.3:
                            
                            # Get bounding box
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            
                            # Calculate center point
                            center_x = int((x1 + x2) / 2)
                            center_y = int((y1 + y2) / 2)
                            
                            # Convert to world coordinates
                            world_x, world_y = self.pixel_to_world(center_x, center_y)
                            
                            # Check if within workspace
                            if self.is_in_workspace(world_x, world_y, 0.0):
                                bottle = {
                                    'pixel_x': center_x,
                                    'pixel_y': center_y,
                                    'world_x': world_x,
                                    'world_y': world_y,
                                    'world_z': 0.0,  # Assume on table surface
                                    'confidence': conf,
                                    'class': class_name,
                                    'bbox': [x1, y1, x2, y2]
                                }
                                bottles.append(bottle)
            
            if bottles:
                print(f"🔍 Detected {len(bottles)} bottles in workspace")
            
        except Exception as e:
            print(f"❌ Bottle detection failed: {e}")
        
        return bottles
    
    def pixel_to_world(self, pixel_x, pixel_y):
        """Convert pixel coordinates to world coordinates"""
        try:
            if not self.camera_params:
                # Use simple approximation if no calibration available
                # This is a rough estimate and should be replaced with proper calibration
                world_x = 0.15 + (pixel_x - 320) * 0.0003  # Rough scaling
                world_y = (pixel_y - 240) * 0.0003
                return world_x, world_y
            
            # Use camera calibration for accurate conversion
            camera_matrix = np.array(self.camera_params['camera_matrix'])
            dist_coeffs = np.array(self.camera_params['distortion_coeffs'])
            
            # Undistort pixel point
            pixel_point = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
            undistorted = cv2.undistortPoints(pixel_point, camera_matrix, dist_coeffs, 
                                            None, camera_matrix)[0][0]
            
            # Convert to world coordinates (assuming table height = 0)
            # This requires proper camera pose calibration
            fx = camera_matrix[0, 0]
            fy = camera_matrix[1, 1]
            cx = camera_matrix[0, 2]
            cy = camera_matrix[1, 2]
            
            # Simple projection (assumes camera looking down at table)
            # Real implementation would need camera pose relative to robot base
            table_height = 0.75  # Estimated table height (m)
            world_x = (undistorted[0] - cx) * table_height / fx
            world_y = (undistorted[1] - cy) * table_height / fy
            
            # Adjust for robot coordinate system
            world_x = 0.15 + world_x * 0.3  # Scale and offset
            world_y = world_y * 0.3
            
            return world_x, world_y
            
        except Exception as e:
            print(f"Warning: Pixel to world conversion failed: {e}")
            # Fallback to simple approximation
            world_x = 0.15 + (pixel_x - 320) * 0.0003
            world_y = (pixel_y - 240) * 0.0003
            return world_x, world_y
    
    def is_in_workspace(self, x, y, z):
        """Check if coordinates are within robot workspace"""
        return (self.workspace['x_min'] <= x <= self.workspace['x_max'] and
                self.workspace['y_min'] <= y <= self.workspace['y_max'] and
                self.workspace['z_min'] <= z <= self.workspace['z_max'])
    
    def inverse_kinematics(self, x, y, z=None):
        """Calculate inverse kinematics for 2D planar arm"""
        try:
            # For 2D case (z not used for SO-100 planar arm)
            distance = math.sqrt(x*x + y*y)
            
            # Check if target is reachable
            if distance > (self.l1 + self.l2) or distance < abs(self.l1 - self.l2):
                return None
            
            # Calculate joint angles using cosine rule
            cos_q2 = (distance*distance - self.l1*self.l1 - self.l2*self.l2) / (2 * self.l1 * self.l2)
            cos_q2 = max(-1, min(1, cos_q2))  # Clamp to valid range
            
            q2 = math.acos(cos_q2)  # Elbow up configuration
            
            # Calculate first joint angle
            alpha = math.atan2(y, x)
            beta = math.atan2(self.l2 * math.sin(q2), self.l1 + self.l2 * math.cos(q2))
            q1 = alpha - beta
            
            # Convert to degrees
            joint_angles = {
                'shoulder_pan': math.degrees(math.atan2(y, x)),  # Base rotation
                'shoulder_lift': math.degrees(q1),               # First joint
                'elbow_flex': math.degrees(q2),                  # Second joint
                'wrist_flex': 0.0,                               # Wrist pitch
                'wrist_roll': 0.0,                               # Wrist roll
                'gripper': 0.0                                   # Gripper
            }
            
            return joint_angles
            
        except Exception as e:
            print(f"❌ IK calculation failed: {e}")
            return None
    
    def generate_push_trajectory(self, bottle, push_angle=0):
        """Generate trajectory for pushing a bottle"""
        try:
            # Start position
            start_x, start_y = bottle['world_x'], bottle['world_y']
            
            # Calculate push direction
            push_dir_x = math.cos(push_angle)
            push_dir_y = math.sin(push_angle)
            
            # Define waypoints for bottle pushing
            waypoints = []
            
            # 1. Home position (current position)
            home_pos = {'x': 0.15, 'y': 0.0, 'z': self.safe_height}
            waypoints.append({
                'name': 'start',
                'world_coords': home_pos,
                'duration': 2.0
            })
            
            # 2. Above bottle (safe approach)
            above_bottle = {'x': start_x, 'y': start_y, 'z': self.approach_height}
            waypoints.append({
                'name': 'above_bottle',
                'world_coords': above_bottle,
                'duration': 2.0
            })
            
            # 3. Approach position (before contact)
            approach_offset = 0.03  # 3cm before bottle
            approach_x = start_x - push_dir_x * approach_offset
            approach_y = start_y - push_dir_y * approach_offset
            approach_pos = {'x': approach_x, 'y': approach_y, 'z': self.contact_height}
            waypoints.append({
                'name': 'approach',
                'world_coords': approach_pos,
                'duration': 1.5
            })
            
            # 4. Pre-contact position
            precontact_offset = 0.01  # 1cm before bottle
            precontact_x = start_x - push_dir_x * precontact_offset
            precontact_y = start_y - push_dir_y * precontact_offset
            precontact_pos = {'x': precontact_x, 'y': precontact_y, 'z': self.contact_height}
            waypoints.append({
                'name': 'pre_contact',
                'world_coords': precontact_pos,
                'duration': 1.0
            })
            
            # 5. Contact position (touch bottle)
            contact_pos = {'x': start_x, 'y': start_y, 'z': self.contact_height}
            waypoints.append({
                'name': 'contact',
                'world_coords': contact_pos,
                'duration': 0.5
            })
            
            # 6. Push through (push bottle)
            push_x = start_x + push_dir_x * self.push_distance
            push_y = start_y + push_dir_y * self.push_distance
            push_pos = {'x': push_x, 'y': push_y, 'z': self.contact_height}
            waypoints.append({
                'name': 'push_through',
                'world_coords': push_pos,
                'duration': 2.0
            })
            
            # 7. Retract (lift up)
            retract_pos = {'x': push_x, 'y': push_y, 'z': self.approach_height}
            waypoints.append({
                'name': 'retract',
                'world_coords': retract_pos,
                'duration': 1.5
            })
            
            # 8. Return home
            waypoints.append({
                'name': 'return_home',
                'world_coords': home_pos,
                'duration': 3.0
            })
            
            # Calculate joint angles for each waypoint
            for waypoint in waypoints:
                coords = waypoint['world_coords']
                joint_angles = self.inverse_kinematics(coords['x'], coords['y'], coords['z'])
                
                if joint_angles is None:
                    print(f"❌ IK failed for waypoint {waypoint['name']}")
                    return None
                
                waypoint['joint_angles'] = joint_angles
            
            return waypoints
            
        except Exception as e:
            print(f"❌ Trajectory generation failed: {e}")
            return None
    
    def smooth_trajectory(self, trajectory):
        """Apply smoothing to trajectory waypoints"""
        if not trajectory:
            return trajectory
        
        # Simple smoothing - interpolate velocities
        smoothed = trajectory.copy()
        
        for i in range(1, len(smoothed) - 1):
            prev_wp = smoothed[i-1]
            curr_wp = smoothed[i]
            next_wp = smoothed[i+1]
            
            # Smooth duration based on distance
            prev_coords = prev_wp['world_coords']
            curr_coords = curr_wp['world_coords']
            next_coords = next_wp['world_coords']
            
            # Calculate distances
            dist_prev = math.sqrt(
                (curr_coords['x'] - prev_coords['x'])**2 +
                (curr_coords['y'] - prev_coords['y'])**2 +
                (curr_coords['z'] - prev_coords['z'])**2
            )
            
            dist_next = math.sqrt(
                (next_coords['x'] - curr_coords['x'])**2 +
                (next_coords['y'] - curr_coords['y'])**2 +
                (next_coords['z'] - curr_coords['z'])**2
            )
            
            # Adjust duration based on distance
            max_speed = 0.1  # m/s
            smoothed[i]['duration'] = max(0.5, max(dist_prev, dist_next) / max_speed)
        
        return smoothed
    
    def visualize_trajectory(self, trajectory, save_plot=False):
        """Visualize 3D trajectory"""
        if not trajectory:
            return
        
        try:
            fig = plt.figure(figsize=(12, 8))
            
            # 3D plot
            ax1 = fig.add_subplot(121, projection='3d')
            
            # Extract coordinates
            x_coords = [wp['world_coords']['x'] for wp in trajectory]
            y_coords = [wp['world_coords']['y'] for wp in trajectory]
            z_coords = [wp['world_coords']['z'] for wp in trajectory]
            
            # Plot trajectory path
            ax1.plot(x_coords, y_coords, z_coords, 'b-', linewidth=2, label='Trajectory')
            ax1.scatter(x_coords, y_coords, z_coords, c='red', s=50, label='Waypoints')
            
            # Add waypoint labels
            for i, wp in enumerate(trajectory):
                coords = wp['world_coords']
                ax1.text(coords['x'], coords['y'], coords['z'], 
                        f"{i+1}: {wp['name']}", fontsize=8)
            
            ax1.set_xlabel('X (m)')
            ax1.set_ylabel('Y (m)')
            ax1.set_zlabel('Z (m)')
            ax1.set_title('3D Trajectory Visualization')
            ax1.legend()
            
            # 2D top view
            ax2 = fig.add_subplot(122)
            ax2.plot(x_coords, y_coords, 'b-', linewidth=2, label='Trajectory')
            ax2.scatter(x_coords, y_coords, c='red', s=50, label='Waypoints')
            
            # Add workspace boundaries
            ws = self.workspace
            ax2.add_patch(plt.Rectangle((ws['x_min'], ws['y_min']), 
                                      ws['x_max']-ws['x_min'], ws['y_max']-ws['y_min'],
                                      fill=False, edgecolor='green', linestyle='--', 
                                      label='Workspace'))
            
            # Add waypoint labels
            for i, wp in enumerate(trajectory):
                coords = wp['world_coords']
                ax2.annotate(f"{i+1}", (coords['x'], coords['y']), 
                           xytext=(5, 5), textcoords='offset points', fontsize=8)
            
            ax2.set_xlabel('X (m)')
            ax2.set_ylabel('Y (m)')
            ax2.set_title('Top View')
            ax2.legend()
            ax2.grid(True)
            ax2.axis('equal')
            
            plt.tight_layout()
            
            if save_plot:
                plt.savefig('trajectory_visualization.png', dpi=150, bbox_inches='tight')
                print("📊 Trajectory plot saved as 'trajectory_visualization.png'")
            
            plt.show()
            
        except Exception as e:
            print(f"❌ Visualization failed: {e}")

def main():
    """Test the trajectory planner"""
    planner = TrajectoryPlanner()
    
    # Test bottle
    test_bottle = {
        'world_x': 0.18,
        'world_y': 0.05,
        'world_z': 0.0,
        'confidence': 0.9
    }
    
    print("🧪 Testing trajectory generation...")
    trajectory = planner.generate_push_trajectory(test_bottle, push_angle=math.pi/4)
    
    if trajectory:
        print(f"✅ Generated trajectory with {len(trajectory)} waypoints")
        
        # Smooth trajectory
        smooth_traj = planner.smooth_trajectory(trajectory)
        print(f"✅ Smoothed trajectory completed")
        
        # Visualize
        planner.visualize_trajectory(smooth_traj, save_plot=True)
    else:
        print("❌ Trajectory generation failed")

if __name__ == "__main__":
    main()
