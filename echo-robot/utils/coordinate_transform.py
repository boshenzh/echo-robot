#!/usr/bin/env python3
"""
Coordinate Transformation Utilities for Echo Robot Vision System
坐标变换工具 - 像素坐标到世界坐标转换

This module provides utilities for converting between pixel coordinates
and real-world coordinates for accurate robot positioning.
"""

import numpy as np
import json
import cv2
import os

class CoordinateTransformer:
    """Handle coordinate transformations between pixel and world coordinates"""
    
    def __init__(self, calibration_file='config/camera_params.json'):
        """
        Initialize coordinate transformer
        初始化坐标变换器
        
        Args:
            calibration_file: Path to camera calibration parameters
        """
        self.calibration_file = calibration_file
        self.camera_matrix = None
        self.dist_coeffs = None
        self.is_calibrated = False
        
        # Robot workspace parameters (adjust based on your setup)
        # 机器人工作空间参数（根据实际设置调整）
        self.workspace_config = {
            'camera_height': 500.0,      # mm, height of camera above table
            'table_z': 0.0,              # mm, table height in world coordinates
            'robot_base_x': 0.0,         # mm, robot base position
            'robot_base_y': 0.0,         # mm, robot base position
            'pixel_to_mm_ratio': 1.0     # mm per pixel (calibrated value)
        }
        
        self.load_calibration()
    
    def load_calibration(self):
        """Load camera calibration parameters 加载摄像头标定参数"""
        if os.path.exists(self.calibration_file):
            try:
                with open(self.calibration_file, 'r') as f:
                    calib_data = json.load(f)
                
                self.camera_matrix = np.array(calib_data['camera_matrix'])
                self.dist_coeffs = np.array(calib_data['distortion_coeffs'])
                self.is_calibrated = True
                
                print(f"✅ Camera calibration loaded from {self.calibration_file}")
                return True
                
            except Exception as e:
                print(f"❌ Error loading calibration: {e}")
                return False
        else:
            print(f"❌ Calibration file not found: {self.calibration_file}")
            print("Please run camera calibration first: python camera_calibration.py --calibrate")
            return False
    
    def undistort_point(self, pixel_x, pixel_y):
        """
        Remove lens distortion from pixel coordinates
        去除镜头畸变
        
        Args:
            pixel_x, pixel_y: Distorted pixel coordinates
            
        Returns:
            undistorted_x, undistorted_y: Undistorted pixel coordinates
        """
        if not self.is_calibrated:
            return pixel_x, pixel_y
        
        # Convert to the format expected by OpenCV
        points = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
        
        # Undistort points
        undistorted = cv2.undistortPoints(points, self.camera_matrix, self.dist_coeffs, P=self.camera_matrix)
        
        return undistorted[0][0][0], undistorted[0][0][1]
    
    def pixel_to_world_simple(self, pixel_x, pixel_y, assume_table_height=True):
        """
        Convert pixel coordinates to world coordinates using simple projection
        使用简单投影将像素坐标转换为世界坐标
        
        Args:
            pixel_x, pixel_y: Pixel coordinates
            assume_table_height: If True, assume object is on table surface
            
        Returns:
            world_x, world_y, world_z: World coordinates in mm
        """
        if not self.is_calibrated:
            print("❌ Camera not calibrated. Using approximate conversion.")
            # Fallback approximate conversion
            world_x = (pixel_x - 640) * 0.5  # Approximate for 1280x720 resolution
            world_y = (pixel_y - 360) * 0.5
            world_z = 0.0
            return world_x, world_y, world_z
        
        # Undistort pixel coordinates
        undist_x, undist_y = self.undistort_point(pixel_x, pixel_y)
        
        # Camera intrinsic parameters
        fx = self.camera_matrix[0, 0]
        fy = self.camera_matrix[1, 1]
        cx = self.camera_matrix[0, 2]
        cy = self.camera_matrix[1, 2]
        
        # Convert to normalized coordinates
        x_norm = (undist_x - cx) / fx
        y_norm = (undist_y - cy) / fy
        
        if assume_table_height:
            # Assume object is on table surface
            z_world = self.workspace_config['table_z']
            camera_height = self.workspace_config['camera_height']
            
            # Calculate world coordinates assuming camera looks straight down
            # Scale factor based on camera height
            scale = camera_height
            world_x = x_norm * scale + self.workspace_config['robot_base_x']
            world_y = y_norm * scale + self.workspace_config['robot_base_y']
            world_z = z_world
        else:
            # Default depth assumption
            scale = 300.0  # mm, approximate distance
            world_x = x_norm * scale
            world_y = y_norm * scale
            world_z = 0.0
        
        return world_x, world_y, world_z
    
    def world_to_pixel(self, world_x, world_y, world_z=0.0):
        """
        Convert world coordinates to pixel coordinates
        将世界坐标转换为像素坐标
        
        Args:
            world_x, world_y, world_z: World coordinates in mm
            
        Returns:
            pixel_x, pixel_y: Pixel coordinates
        """
        if not self.is_calibrated:
            print("❌ Camera not calibrated. Using approximate conversion.")
            pixel_x = world_x * 2 + 640  # Approximate conversion
            pixel_y = world_y * 2 + 360
            return pixel_x, pixel_y
        
        # Camera intrinsic parameters
        fx = self.camera_matrix[0, 0]
        fy = self.camera_matrix[1, 1]
        cx = self.camera_matrix[0, 2]
        cy = self.camera_matrix[1, 2]
        
        # Assume camera height for projection
        camera_height = self.workspace_config['camera_height']
        
        # Project to normalized coordinates
        x_norm = (world_x - self.workspace_config['robot_base_x']) / camera_height
        y_norm = (world_y - self.workspace_config['robot_base_y']) / camera_height
        
        # Convert to pixel coordinates
        pixel_x = x_norm * fx + cx
        pixel_y = y_norm * fy + cy
        
        return pixel_x, pixel_y
    
    def calibrate_workspace(self, reference_points):
        """
        Calibrate workspace using known reference points
        使用已知参考点校准工作空间
        
        Args:
            reference_points: List of (pixel_x, pixel_y, world_x, world_y) tuples
        """
        if len(reference_points) < 4:
            print("❌ Need at least 4 reference points for workspace calibration")
            return False
        
        # Extract pixel and world coordinates
        pixel_coords = np.array([[p[0], p[1]] for p in reference_points], dtype=np.float32)
        world_coords = np.array([[p[2], p[3]] for p in reference_points], dtype=np.float32)
        
        # Calculate homography matrix
        homography, _ = cv2.findHomography(pixel_coords, world_coords)
        
        if homography is not None:
            self.homography_matrix = homography
            print("✅ Workspace calibration successful")
            
            # Save workspace calibration
            workspace_calib = {
                'homography_matrix': homography.tolist(),
                'reference_points': reference_points
            }
            
            with open('config/workspace_calibration.json', 'w') as f:
                json.dump(workspace_calib, f, indent=2)
            
            return True
        else:
            print("❌ Workspace calibration failed")
            return False
    
    def pixel_to_world_homography(self, pixel_x, pixel_y):
        """
        Convert pixel to world coordinates using homography
        使用单应矩阵将像素坐标转换为世界坐标
        """
        if not hasattr(self, 'homography_matrix'):
            return self.pixel_to_world_simple(pixel_x, pixel_y)
        
        # Apply homography transformation
        pixel_point = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
        world_point = cv2.perspectiveTransform(pixel_point, self.homography_matrix)
        
        return world_point[0][0][0], world_point[0][0][1], 0.0
    
    def update_workspace_config(self, **kwargs):
        """
        Update workspace configuration parameters
        更新工作空间配置参数
        """
        self.workspace_config.update(kwargs)
        print(f"✅ Workspace config updated: {kwargs}")
    
    def get_transformation_info(self):
        """Get information about current transformation setup"""
        info = {
            'calibrated': self.is_calibrated,
            'workspace_config': self.workspace_config,
            'has_homography': hasattr(self, 'homography_matrix')
        }
        
        if self.is_calibrated:
            info['camera_matrix'] = self.camera_matrix.tolist()
            info['distortion_coeffs'] = self.dist_coeffs.tolist()
        
        return info

def test_coordinate_transformation():
    """Test coordinate transformation functions"""
    print("🧪 Testing Coordinate Transformation")
    
    transformer = CoordinateTransformer()
    
    # Test some sample points
    test_points = [
        (640, 360),   # Image center
        (320, 180),   # Top-left quadrant
        (960, 540),   # Bottom-right quadrant
    ]
    
    print("\nPixel to World Coordinate Conversion:")
    print("像素坐标 -> 世界坐标转换:")
    for pixel_x, pixel_y in test_points:
        world_x, world_y, world_z = transformer.pixel_to_world_simple(pixel_x, pixel_y)
        print(f"  Pixel ({pixel_x:4.0f}, {pixel_y:4.0f}) -> World ({world_x:6.1f}, {world_y:6.1f}, {world_z:6.1f}) mm")
    
    print(f"\nTransformation Info:")
    info = transformer.get_transformation_info()
    print(f"  Calibrated: {info['calibrated']}")
    print(f"  Camera Height: {info['workspace_config']['camera_height']} mm")
    print(f"  Has Homography: {info['has_homography']}")

if __name__ == "__main__":
    test_coordinate_transformation()
