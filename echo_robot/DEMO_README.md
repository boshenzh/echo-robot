# Robot Demo Scripts 🤖

This directory contains integrated demo scripts that combine camera vision, YOLO object detection, robot arm control, and audio feedback.

## 📋 Demo Features

1. **📷 Camera + YOLO Detection**: Real-time bottle detection using YOLOv8
2. **🤖 Robot Trajectory**: Push/pull movements (forward 10cm, then backward)
3. **🔊 Audio Alerts**: Sound notification before robot movement
4. **🎮 Multiple Modes**: Interactive and automatic operation

## 🎪 Available Demo Scripts

### 1. `demo_simple.py` - Lightweight Demo ⭐ RECOMMENDED
- **Simple audio**: Uses system beep commands
- **Minimal dependencies**: OpenCV + YOLO only
- **Fast setup**: Ready to run immediately
- **Simulation mode**: Works without robot hardware

### 2. `demo_integrated.py` - Advanced Demo
- **Enhanced audio**: Uses pygame for better sound quality  
- **More features**: Advanced audio management
- **Additional dependencies**: Requires pygame installation

## 🚀 Quick Start

### Step 1: Install Dependencies
```bash
# Install basic requirements
pip install opencv-python ultralytics numpy

# For enhanced audio (optional)
pip install pygame

# Or install all at once
pip install -r demo_requirements.txt
```

### Step 2: Install System Audio (Linux only)
```bash
# For audio alerts on Linux
sudo apt-get install alsa-utils
```

### Step 3: Run the Demo
```bash
# Recommended: Simple demo
python demo_simple.py

# Or advanced demo
python demo_integrated.py
```

## 🎮 Demo Modes

### Interactive Mode (Default)
- Live camera feed with YOLO detection
- Manual trigger with `'p'` key
- Automatic detection when bottles are found
- Visual feedback in OpenCV window

### Automatic Mode
- Predefined number of cycles
- Timed intervals between pushes
- No camera required
- Great for testing robot movements

## 🔧 Configuration Options

When you run the demo, you'll be prompted to configure:

1. **Camera Selection**:
   - Enter camera ID (0, 1, 2) or press Enter for auto-detection
   - Most webcams use ID 0

2. **Robot Mode**:
   - **Simulation**: Works without robot hardware (recommended for testing)
   - **Real Robot**: Connects to physical SO100/SO101 robot

3. **Demo Type**:
   - **Interactive**: Camera + manual triggers
   - **Automatic**: Timed cycles without camera

## 🎯 Robot Trajectory Details

The demo executes a simple push-and-pull sequence:

```
Initial Position: (0.0, 0.16)  # Robot arm start position
    ↓
🔊 Audio Alert: 0.8s beep at 800Hz
    ↓  
Forward Push: → (0.1, 0.16)   # Push 10cm forward
    ↓
Hold Position: 1.0s pause
    ↓
Backward Retreat: ← (0.0, 0.16)  # Return to start
```

## 🎛️ Controls (Interactive Mode)

| Key | Action |
|-----|--------|
| `p` | Manual push trigger |
| `s` | Save current camera frame |
| `q` or `ESC` | Quit demo |

## 🤖 Robot Hardware Setup

If using a real robot (SO100/SO101):

1. **Connect Robot**: USB cable to `/dev/ttyACM0` (or other port)
2. **Set Permissions**: `sudo chmod 666 /dev/ttyACM0`
3. **Choose Port**: Enter correct port when prompted
4. **Calibration**: Optional calibration step for accuracy

## 🔊 Audio System

The demo provides audio feedback before each robot movement:

- **Purpose**: Safety alert before robot motion
- **Sound**: 800Hz beep for 0.8 seconds
- **Fallback**: Visual "BEEP!" message if audio fails
- **Methods**: 
  - Linux: `speaker-test` command
  - Pygame: Generated sine wave (if installed)
  - Fallback: Terminal bell character

## 🐛 Troubleshooting

### Camera Issues
```bash
# Check available cameras
ls /dev/video*

# Test camera manually
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera 0:', cap.isOpened())"
```

### Audio Issues
```bash
# Test system audio
speaker-test -t sine -f 800 -l 1

# Check audio devices
aplay -l
```

### Robot Connection Issues
```bash
# Check USB devices
lsusb

# Check permissions
ls -la /dev/ttyACM*

# Fix permissions if needed
sudo chmod 666 /dev/ttyACM0
```

### YOLO Model Issues
If YOLOv8 model download fails:
```bash
# Download manually
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
```

## 📁 File Structure

```
echo-robot/
├── demo_simple.py          # Lightweight demo (recommended)
├── demo_integrated.py      # Advanced demo with enhanced features
├── demo_requirements.txt   # Python dependencies
├── DEMO_README.md         # This file
├── test_camera_yolo.py    # Original camera test script
├── lerobot_yolo.py        # Original robot control script
└── yolov8n.pt            # YOLO model (auto-downloaded)
```

## 🎓 Understanding the Code

### Key Components

1. **AudioManager/play_beep_sound()**: Handles audio alerts
2. **RobotController/SimpleRobotController**: Robot movement control
3. **CameraYOLOSystem/SimpleCameraYOLO**: Camera + YOLO detection
4. **Main Integration**: Combines all components with user interface

### Trajectory Planning
- Uses inverse kinematics from `lerobot_yolo.py`
- Simple 2-joint arm model
- Workspace boundary checking
- Smooth motion interpolation

### Safety Features
- Audio alerts before movement
- Simulation mode for testing
- Error handling and graceful fallbacks
- Manual trigger controls

## 🔄 Next Steps

- **Customize Trajectory**: Modify push distance and speed
- **Add More Objects**: Detect other objects besides bottles
- **Enhanced Audio**: Add different sounds for different actions
- **Multiple Targets**: Handle multiple detected objects
- **Advanced Planning**: Add more complex movement patterns

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all dependencies are installed
3. Test components individually (camera, audio, robot)
4. Use simulation mode first before trying real hardware

Happy robotic demoing! 🎉
