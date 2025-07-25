

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
- [x] 自动检测摄像头ID并处理多摄像头
- [x] 校准摄像头参数以实现精确定位


**主要特性：**
- 实时视频处理
- 使用YOLOv8进行稳健的瓶子检测
- 摄像头自动发现和配置
- 像素到世界坐标映射的2D坐标提取

### 2. 轨迹生成
**文件：`trajectory_planner.py`（待创建）**
- [ ] 为推动运动生成安全的末端执行器轨迹
- [ ] 优化路径规划以提高效率和安全性
- [ ] 添加轨迹可视化工具

**主要特性：**
- 基于物理的轨迹规划
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

### 摄像头检测和校准
```bash
# 自动检测可用摄像头
python camera_calibration.py --auto-detect

# 测试摄像头实时画面
python camera_calibration.py --camera-id 0 --live-test

# 进行摄像头标定（需要9x6棋盘格标定板）
python camera_calibration.py --camera-id 0 --calibrate

# 测试标定效果
python camera_calibration.py --camera-id 0 --test
```

### 测试摄像头和YOLO检测
```bash
# 基础YOLO检测
python test_camera_yolo.py

# 使用标定参数显示世界坐标
python test_camera_yolo.py --use-calibration --show-coordinates
```
### 轨迹规划器单独测试
```bash
# 测试轨迹规划算法和可视化
python trajectory_planner.py
```

### 启动完整系统
```bash
# 运行集成的视觉轨迹控制系统
python vision_trajectory_control.py
```
TODO:
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
├── camera_calibration.py         # 摄像头标定脚本
├── trajectory_planner.py         # 3D轨迹生成（待开发）
├── inverse_kinematics.py         # IK求解器和机器人控制（待开发）
├── simulate_bottle_push.py       # MuJoCo仿真（待开发）
├── robot_bottle_push.py          # 主执行脚本（待开发）
├── CAMERA_CALIBRATION_GUIDE.md   # 摄像头标定详细指南
├── config/
│   ├── camera_params.json        # 摄像头标定参数
│   ├── robot_config.yaml         # 机器人规格和限制
│   └── yolo_config.yaml          # YOLO模型配置
├── models/
│   └── yolo_bottle_model.pt      # 瓶子训练的YOLO模型
├── utils/
│   ├── camera_utils.py           # 摄像头辅助函数
│   ├── coordinate_transform.py   # 2D/3D坐标实用程序
│   └── visualization.py          # 绘图和可视化工具
└── calibration_images/           # 标定图像存储目录
```

## 开发状态

### 已完成 ✅
- 项目设置和环境配置
- 基础YOLO集成框架
- 摄像头自动检测和校准
- 摄像头参数标定系统

### 进行中 🚧
- 实时瓶子检测优化
- 坐标转换精度提升

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
