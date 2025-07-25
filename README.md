# Echo Robot - Vision Branch

## Overview
This branch aims to develop a vision-based bottle pushing task on the robot arm LeRobot SO-100. The project integrates computer vision, object detection, trajectory planning, and inverse kinematics to enable autonomous bottle manipulation.

## Project Goals
The main objective is to create an autonomous system that can:
- Detect bottles in real-time using computer vision
- Plan safe trajectories for bottle pushing tasks
- Execute precise robotic arm movements using inverse kinematics
- Provide a complete pipeline from perception to action

## Implementation Steps

### 1. Vision and Object Detection
**File: `test_camera_yolo.py`**
- [x] Implement real-time YOLO-based bottle detection
- [ ] Auto-detect camera ID and handle multiple cameras
- [ ] Calibrate camera parameters for accurate positioning
- [ ] Extract 2D bottle position with confidence scores
- [ ] Handle edge cases (multiple bottles, occlusion, lighting variations)

**Key Features:**
- Real-time video processing
- Robust bottle detection using YOLOv8
- Camera auto-discovery and configuration
- 2D coordinate extraction with pixel-to-world mapping

### 2. Trajectory Generation
**File: `trajectory_planner.py` (to be created)**
- [ ] Convert 2D bottle position to 3D world coordinates
- [ ] Generate safe end-effector trajectories for pushing motion
- [ ] Implement collision avoidance algorithms
- [ ] Optimize path planning for efficiency and safety
- [ ] Add trajectory visualization tools

**Key Features:**
- 2D to 3D coordinate transformation
- Physics-based trajectory planning
- Collision detection and avoidance
- Smooth motion profiles
- Configurable push parameters (distance, angle, speed)

### 3. Inverse Kinematics and Control
**File: `inverse_kinematics.py` (to be created)**
- [ ] Implement inverse kinematics solver for LeRobot SO-100
- [ ] Joint angle calculation from end-effector positions
- [ ] Motion planning and execution
- [ ] Integration with MuJoCo simulation for testing
- [ ] Real robot deployment and validation

**Key Features:**
- Mathematical IK solver
- Joint limit constraints
- Smooth interpolation between poses
- Simulation testing environment
- Real-time robot control interface

## System Architecture

```
Camera Input → YOLO Detection → 2D Position
                     ↓
Coordinate Transform → 3D Position → Trajectory Planning
                     ↓
Inverse Kinematics → Joint Angles → Robot Control
                     ↓
MuJoCo Simulation ←→ Real Robot Execution
```

## Environment Setup

### Prerequisites
- Python 3.10+
- CUDA-capable GPU (recommended)
- Camera hardware
- LeRobot SO-100 arm

### Installation
1. Clone the repository and switch to vision branch:
```bash
git clone https://github.com/boshenzh/echo-robot.git
cd echo-robot
git checkout vision
```

2. Create conda environment:
```bash
conda env create -f environment_lerobot_yolo.yml
conda activate lerobot-yolo
```

3. Install additional dependencies:
```bash
pip install -r requirements_lerobot_yolo.txt
```

## Usage

### Testing Camera and YOLO Detection
```bash
python test_camera_yolo.py
```

### Running Simulation (MuJoCo)
```bash
python simulate_bottle_push.py --bottle-position x y --visualize
```

### Executing Real Robot Task
```bash
python robot_bottle_push.py --camera-id 0 --safety-mode
```

## File Structure
```
echo-robot/
├── test_camera_yolo.py           # Camera testing and YOLO detection
├── trajectory_planner.py         # 3D trajectory generation (TBD)
├── inverse_kinematics.py         # IK solver and robot control (TBD)
├── simulate_bottle_push.py       # MuJoCo simulation (TBD)
├── robot_bottle_push.py          # Main execution script (TBD)
├── config/
│   ├── camera_params.yaml        # Camera calibration parameters
│   ├── robot_config.yaml         # Robot specifications and limits
│   └── yolo_config.yaml          # YOLO model configuration
├── models/
│   └── yolo_bottle_model.pt      # Trained YOLO model for bottles
└── utils/
    ├── camera_utils.py           # Camera helper functions
    ├── coordinate_transform.py   # 2D/3D coordinate utilities
    └── visualization.py          # Plotting and visualization tools
```

## Development Status

### Completed ✅
- Project setup and environment configuration
- Basic YOLO integration framework

### In Progress 🚧
- Camera auto-detection and calibration
- Real-time bottle detection optimization

### Planned 📋
- 3D trajectory generation
- Inverse kinematics implementation
- MuJoCo simulation integration
- Real robot testing and validation

## Testing Strategy

1. **Unit Tests**: Individual component testing (camera, YOLO, IK solver)
2. **Integration Tests**: End-to-end pipeline validation
3. **Simulation Tests**: Safe testing in MuJoCo environment
4. **Hardware Tests**: Real robot validation with safety protocols

## Safety Considerations

- Emergency stop mechanisms
- Joint limit enforcement
- Collision detection
- Safe workspace boundaries
- Human-robot interaction protocols

## Contributing

1. Follow the established file structure
2. Add comprehensive documentation
3. Include unit tests for new features
4. Test in simulation before hardware deployment
5. Maintain safety-first development approach

## Dependencies

Key packages (see `requirements_lerobot_yolo.txt` for complete list):
- `ultralytics==8.3.169` (YOLO)
- `opencv-python==4.12.0` (Computer Vision)
- `torch==2.7.1` (Deep Learning)
- `open3d==0.19.0` (3D Processing)
- `numpy`, `scipy`, `matplotlib` (Scientific Computing)

## License

[Add your license information here]

## Contact

[Add contact information for the project team]

---

# Echo Robot - 视觉分支

## 概述
本分支旨在为LeRobot SO-100机械臂开发基于视觉的瓶子推动任务。该项目集成了计算机视觉、目标检测、轨迹规划和逆运动学，以实现自主的瓶子操作。

## 项目目标
主要目标是创建一个自主系统，能够：
- 使用计算机视觉实时检测瓶子
- 为瓶子推动任务规划安全轨迹
- 使用逆运动学执行精确的机械臂运动
- 提供从感知到动作的完整流水线

## 实现步骤

### 1. 视觉和目标检测
**文件：`test_camera_yolo.py`**
- [x] 实现基于YOLO的实时瓶子检测
- [ ] 自动检测摄像头ID并处理多摄像头
- [ ] 校准摄像头参数以实现精确定位
- [ ] 提取带置信度分数的2D瓶子位置
- [ ] 处理边缘情况（多个瓶子、遮挡、光照变化）

**主要特性：**
- 实时视频处理
- 使用YOLOv8进行稳健的瓶子检测
- 摄像头自动发现和配置
- 像素到世界坐标映射的2D坐标提取

### 2. 轨迹生成
**文件：`trajectory_planner.py`（待创建）**
- [ ] 将2D瓶子位置转换为3D世界坐标
- [ ] 为推动运动生成安全的末端执行器轨迹
- [ ] 实现碰撞避免算法
- [ ] 优化路径规划以提高效率和安全性
- [ ] 添加轨迹可视化工具

**主要特性：**
- 2D到3D坐标转换
- 基于物理的轨迹规划
- 碰撞检测和避免
- 平滑运动轮廓
- 可配置的推动参数（距离、角度、速度）

### 3. 逆运动学和控制
**文件：`inverse_kinematics.py`（待创建）**
- [ ] 为LeRobot SO-100实现逆运动学求解器
- [ ] 从末端执行器位置计算关节角度
- [ ] 运动规划和执行
- [ ] 与MuJoCo仿真集成进行测试
- [ ] 真实机器人部署和验证

**主要特性：**
- 数学IK求解器
- 关节限制约束
- 姿态间的平滑插值
- 仿真测试环境
- 实时机器人控制接口

## 系统架构

```
摄像头输入 → YOLO检测 → 2D位置
                     ↓
坐标变换 → 3D位置 → 轨迹规划
                     ↓
逆运动学 → 关节角度 → 机器人控制
                     ↓
MuJoCo仿真 ←→ 真实机器人执行
```

## 环境设置

### 先决条件
- Python 3.10+
- 支持CUDA的GPU（推荐）
- 摄像头硬件
- LeRobot SO-100机械臂

### 安装
1. 克隆仓库并切换到视觉分支：
```bash
git clone https://github.com/boshenzh/echo-robot.git
cd echo-robot
git checkout vision
```

2. 创建conda环境：
```bash
conda env create -f environment_lerobot_yolo.yml
conda activate lerobot-yolo
```

3. 安装额外依赖：
```bash
pip install -r requirements_lerobot_yolo.txt
```

## 使用方法

### 测试摄像头和YOLO检测
```bash
python test_camera_yolo.py
```

### 运行仿真（MuJoCo）
```bash
python simulate_bottle_push.py --bottle-position x y --visualize
```

### 执行真实机器人任务
```bash
python robot_bottle_push.py --camera-id 0 --safety-mode
```

## 文件结构
```
echo-robot/
├── test_camera_yolo.py           # 摄像头测试和YOLO检测
├── trajectory_planner.py         # 3D轨迹生成（待开发）
├── inverse_kinematics.py         # IK求解器和机器人控制（待开发）
├── simulate_bottle_push.py       # MuJoCo仿真（待开发）
├── robot_bottle_push.py          # 主执行脚本（待开发）
├── config/
│   ├── camera_params.yaml        # 摄像头标定参数
│   ├── robot_config.yaml         # 机器人规格和限制
│   └── yolo_config.yaml          # YOLO模型配置
├── models/
│   └── yolo_bottle_model.pt      # 瓶子训练的YOLO模型
└── utils/
    ├── camera_utils.py           # 摄像头辅助函数
    ├── coordinate_transform.py   # 2D/3D坐标实用程序
    └── visualization.py          # 绘图和可视化工具
```

## 开发状态

### 已完成 ✅
- 项目设置和环境配置
- 基础YOLO集成框架

### 进行中 🚧
- 摄像头自动检测和校准
- 实时瓶子检测优化

### 计划中 📋
- 3D轨迹生成
- 逆运动学实现
- MuJoCo仿真集成
- 真实机器人测试和验证

## 测试策略

1. **单元测试**：单个组件测试（摄像头、YOLO、IK求解器）
2. **集成测试**：端到端流水线验证
3. **仿真测试**：在MuJoCo环境中进行安全测试
4. **硬件测试**：带安全协议的真实机器人验证

## 安全考虑

- 紧急停止机制
- 关节限制执行
- 碰撞检测
- 安全工作空间边界
- 人机交互协议

## 贡献指南

1. 遵循既定的文件结构
2. 添加全面的文档
3. 为新功能包含单元测试
4. 在硬件部署前进行仿真测试
5. 保持安全第一的开发方法

## 依赖项

主要包（完整列表见`requirements_lerobot_yolo.txt`）：
- `ultralytics==8.3.169`（YOLO）
- `opencv-python==4.12.0`（计算机视觉）
- `torch==2.7.1`（深度学习）
- `open3d==0.19.0`（3D处理）
- `numpy`、`scipy`、`matplotlib`（科学计算）

## 许可证

[在此添加您的许可证信息]

## 联系方式

[在此添加项目团队的联系信息]
