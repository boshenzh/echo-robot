import cv2
import time
import argparse
import os
import sys
from ultralytics import YOLO

# Add utils directory to path for coordinate transformation
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
try:
    from coordinate_transform import CoordinateTransformer
except ImportError:
    print("⚠️  Coordinate transformation not available. Run without calibration.")
    CoordinateTransformer = None

def auto_detect_camera():
    """
    Automatically detect available camera IDs
    自动检测可用的摄像头ID
    """
    print("🔍 Auto-detecting cameras...")
    available_cameras = []
    
    # Test camera IDs 0-10
    for camera_id in range(11):
        cap = cv2.VideoCapture(camera_id)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_cameras.append(camera_id)
                print(f"✅ Camera {camera_id} detected")
            cap.release()
        else:
            cap.release()
    
    if not available_cameras:
        print("❌ No cameras detected")
        return None
    
    print(f"📷 Available cameras: {available_cameras}")
    return available_cameras[0]  # Return first available camera

def main():
    """
    实时摄像头YOLO目标检测，集成摄像头标定和坐标转换
    Real-time camera YOLO detection with camera calibration and coordinate transformation
    """
    
    parser = argparse.ArgumentParser(description='Camera YOLO Detection with Calibration')
    parser.add_argument('--camera-id', type=int, default=None, help='Camera ID (auto-detect if not specified)')
    parser.add_argument('--model', type=str, default='yolov8n.pt', help='YOLO model path')
    parser.add_argument('--conf-threshold', type=float, default=0.5, help='Confidence threshold')
    parser.add_argument('--use-calibration', action='store_true', help='Use camera calibration for coordinate transformation')
    parser.add_argument('--show-coordinates', action='store_true', help='Show world coordinates for detected objects')
    
    args = parser.parse_args()
    
    # Auto-detect camera if not specified
    camera_id = args.camera_id
    if camera_id is None:
        camera_id = auto_detect_camera()
        if camera_id is None:
            return
    
    # 加载YOLO模型
    print(f"🤖 Loading YOLO model: {args.model}")
    model = YOLO(args.model)
    print("✅ YOLO model loaded successfully!")
    
    # Initialize coordinate transformer if available and requested
    transformer = None
    if args.use_calibration and CoordinateTransformer:
        transformer = CoordinateTransformer()
        if transformer.is_calibrated:
            print("✅ Camera calibration loaded")
        else:
            print("⚠️  Camera calibration not found. Run: python camera_calibration.py --calibrate")
            transformer = None
    
    # 初始化摄像头
    print(f"📷 Initializing camera {camera_id}...")
    cap = cv2.VideoCapture(camera_id)
    
    # 检查摄像头是否成功打开
    if not cap.isOpened():
        print(f"❌ Error: Could not open camera {camera_id}")
        return
    
    # 设置摄像头参数
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    # Get actual camera resolution
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"📐 Camera resolution: {width}x{height}")
    
    print("🎯 Camera initialized successfully!")
    print("Controls 控制说明:")
    print("  'q' or ESC: Quit 退出")
    print("  's': Save current frame 保存当前帧")
    print("  'c': Toggle coordinate display 切换坐标显示")
    print("  'r': Reset detection statistics 重置检测统计")
    
    # 用于计算FPS
    prev_time = time.time()
    fps_counter = 0
    fps_display = 0
    
    # Detection statistics
    detection_count = 0
    show_coords = args.show_coordinates
    
    try:
        while True:
            # 读取摄像头帧
            ret, frame = cap.read()
            if not ret:
                print("❌ Error: Failed to capture frame")
                break
            
            # YOLO推理
            results = model(frame, device='cpu', verbose=False)
            
            # 绘制检测结果
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # 获取边界框坐标
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        
                        # 获取置信度和类别
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        label = model.names[cls]
                        
                        # 只显示置信度大于阈值的检测结果
                        if conf > args.conf_threshold:
                            detection_count += 1
                            
                            # 计算边界框中心点
                            center_x = (x1 + x2) // 2
                            center_y = (y1 + y2) // 2
                            
                            # 绘制边界框
                            color = (0, 255, 0)  # Green for bottle/object
                            if 'bottle' in label.lower():
                                color = (0, 255, 255)  # Yellow for bottles
                            
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                            
                            # 绘制中心点
                            cv2.circle(frame, (center_x, center_y), 5, color, -1)
                            
                            # 准备标签文本
                            label_text = f'{label} {conf:.2f}'
                            
                            # 如果有坐标转换，添加世界坐标
                            if transformer and show_coords:
                                world_x, world_y, world_z = transformer.pixel_to_world_simple(center_x, center_y)
                                label_text += f'\nWorld: ({world_x:.1f}, {world_y:.1f})mm'
                            
                            # 绘制标签
                            lines = label_text.split('\n')
                            y_offset = y1
                            
                            for i, line in enumerate(lines):
                                label_size = cv2.getTextSize(line, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                                
                                # 绘制标签背景
                                bg_y1 = y_offset - label_size[1] - 10
                                bg_y2 = y_offset
                                cv2.rectangle(frame, (x1, bg_y1), (x1 + label_size[0], bg_y2), color, -1)
                                
                                # 绘制标签文字
                                cv2.putText(frame, line, (x1, y_offset - 5),
                                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                                
                                y_offset = bg_y1
            
            # 计算并显示FPS
            current_time = time.time()
            fps_counter += 1
            
            if current_time - prev_time >= 1.0:  # 每秒更新一次FPS显示
                fps_display = fps_counter
                fps_counter = 0
                prev_time = current_time
            
            # 显示信息
            info_y = 30
            cv2.putText(frame, f'FPS: {fps_display}', (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            info_y += 30
            cv2.putText(frame, f'Camera: {camera_id}', (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            info_y += 25
            cv2.putText(frame, f'Detections: {detection_count}', (10, info_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            if transformer:
                info_y += 25
                calib_status = "Calibrated" if transformer.is_calibrated else "Not Calibrated"
                cv2.putText(frame, f'Camera: {calib_status}', (10, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0) if transformer.is_calibrated else (0, 0, 255), 2)
            
            if show_coords:
                info_y += 25
                cv2.putText(frame, 'Coordinates: ON', (10, info_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # 显示画面
            cv2.imshow('Camera YOLO Detection with Calibration', frame)
            
            # 检查按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q'键或ESC键退出
                break
            elif key == ord('s'):  # 's'键保存当前帧
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f'yolo_detection_{timestamp}.jpg'
                cv2.imwrite(filename, frame)
                print(f"💾 Image saved as {filename}")
            elif key == ord('c'):  # 'c'键切换坐标显示
                show_coords = not show_coords
                print(f"🎯 Coordinate display: {'ON' if show_coords else 'OFF'}")
            elif key == ord('r'):  # 'r'键重置统计
                detection_count = 0
                print("🔄 Detection statistics reset")
    
    except KeyboardInterrupt:
        print("⏹️  Program interrupted by user")
    
    finally:
        # 释放资源
        cap.release()
        cv2.destroyAllWindows()
        print("📷 Camera released and windows closed")

if __name__ == "__main__":
    main()
