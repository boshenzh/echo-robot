# Camera Calibration Quick Start Guide
# 摄像头标定快速入门指南

## Overview 概述

This guide will help you calibrate your camera for precise 2D to 3D coordinate transformation in the bottle pushing task.

本指南将帮助您校准摄像头，实现精确的2D到3D坐标转换，用于瓶子推动任务。

## Step 1: Detect Your Camera 步骤1：检测摄像头

First, find out which cameras are available:

首先，检测可用的摄像头：

```bash
# Detect all available cameras
python utils/camera_utils.py --detect

# Test a specific camera
python utils/camera_utils.py --test 0
```

## Step 2: Camera Calibration 步骤2：摄像头标定

### Prepare Calibration Pattern 准备标定图案

You'll need a checkerboard calibration pattern:
- 9x6 inner corners (9x6内角点)
- 25mm square size (25毫米方格尺寸)
- Print on flat, rigid surface (打印在平坦、坚硬的表面上)

### Run Calibration 运行标定

```bash
# Full calibration process (collect images + calibrate)
python camera_calibration.py --camera-id 0 --calibrate

# Or collect images first, then calibrate separately
python camera_calibration.py --camera-id 0 --collect --num-images 20
python camera_calibration.py --camera-id 0 --calibrate
```

### Calibration Instructions 标定说明

1. Hold the checkerboard pattern in front of the camera
2. Move it to different positions and angles
3. Press SPACE when pattern is detected (green corners)
4. Collect 15-20 good images
5. The script will automatically calculate calibration parameters

1. 将棋盘格标定板放在摄像头前
2. 移动到不同位置和角度
3. 检测到图案时按空格键（绿色角点）
4. 收集15-20张高质量图像
5. 脚本将自动计算标定参数

## Step 3: Test Calibration 步骤3：测试标定

```bash
# Test calibration results
python camera_calibration.py --camera-id 0 --test
```

This will show side-by-side original and undistorted images.

这将显示原始图像和去畸变图像的对比。

## Step 4: Use Calibrated Camera 步骤4：使用标定后的摄像头

```bash
# Run YOLO detection with calibration
python test_camera_yolo.py --camera-id 0 --use-calibration --show-coordinates

# Auto-detect camera and show coordinates
python test_camera_yolo.py --use-calibration --show-coordinates
```

## Output Files 输出文件

After calibration, you'll have:
标定后，您将得到：

- `config/camera_params.json` - Camera intrinsic parameters (摄像头内参)
- `calibration_images/` - Calibration images (标定图像)

## Camera Parameters 摄像头参数

The calibration file contains:
标定文件包含：

```json
{
  "camera_matrix": [[fx, 0, cx], [0, fy, cy], [0, 0, 1]],
  "distortion_coeffs": [k1, k2, p1, p2, k3],
  "reprojection_error": 0.5,
  "calibration_date": "2025-07-25T..."
}
```

- fx, fy: Focal lengths (焦距)
- cx, cy: Principal point (主点)
- k1, k2, k3: Radial distortion (径向畸变)
- p1, p2: Tangential distortion (切向畸变)

## Coordinate Transformation 坐标转换

Once calibrated, you can convert pixel coordinates to world coordinates:

标定完成后，您可以将像素坐标转换为世界坐标：

```python
from utils.coordinate_transform import CoordinateTransformer

transformer = CoordinateTransformer()
world_x, world_y, world_z = transformer.pixel_to_world_simple(pixel_x, pixel_y)
```

## Troubleshooting 故障排除

### Poor Calibration Results 标定结果差

- **High reprojection error (>1.0 pixels)**: Collect more images, ensure checkerboard is flat
- **检测不到棋盘格**: Check lighting, focus, pattern size
- **摄像头无法打开**: Try different camera IDs, check USB connections

### Camera Detection Issues 摄像头检测问题

```bash
# List all video devices (Linux)
ls /dev/video*

# Test camera manually
python -c "import cv2; cap=cv2.VideoCapture(0); print('Camera 0:', cap.isOpened())"
```

### Coordinate Transformation Issues 坐标转换问题

- Verify camera height and workspace parameters
- Check if calibration file exists and is valid
- Ensure proper lighting conditions

## Advanced Configuration 高级配置

### Workspace Calibration 工作空间标定

For more accurate coordinate transformation, calibrate your workspace:

```python
from utils.coordinate_transform import CoordinateTransformer

transformer = CoordinateTransformer()

# Define reference points: (pixel_x, pixel_y, world_x_mm, world_y_mm)
reference_points = [
    (320, 240, -100, -100),  # Top-left corner
    (960, 240, 100, -100),   # Top-right corner
    (320, 480, -100, 100),   # Bottom-left corner
    (960, 480, 100, 100),    # Bottom-right corner
]

transformer.calibrate_workspace(reference_points)
```

### Camera Height Configuration 摄像头高度配置

```python
transformer.update_workspace_config(
    camera_height=500.0,  # mm above table
    table_z=0.0,         # table height
    robot_base_x=0.0,    # robot position
    robot_base_y=0.0
)
```

## Integration with Robot Control 与机器人控制集成

Once calibrated, the coordinate transformation can be used for:

标定完成后，坐标转换可用于：

1. **Bottle Detection**: Convert detected bottle center to world coordinates
2. **Trajectory Planning**: Plan robot end-effector path in world coordinates  
3. **Collision Avoidance**: Check workspace boundaries
4. **Precision Control**: Accurate positioning for pushing tasks

1. **瓶子检测**: 将检测到的瓶子中心转换为世界坐标
2. **轨迹规划**: 在世界坐标系中规划机器人末端执行器路径
3. **碰撞避免**: 检查工作空间边界
4. **精确控制**: 推动任务的精确定位
