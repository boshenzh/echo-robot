import cv2
import time
from ultralytics import YOLO

def main():
    """实时摄像头YOLO目标检测可视化"""
    
    # 加载YOLO模型
    model = YOLO('yolov8n.pt')   # 或者你自己的模型路径
    print("YOLO model loaded successfully!")
    
    # 初始化摄像头
    cap = cv2.VideoCapture(2)
    
    # 检查摄像头是否成功打开
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    # 设置摄像头参数
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("Camera initialized. Press 'q' to quit.")
    
    # 用于计算FPS
    prev_time = time.time()
    fps_counter = 0
    fps_display = 0
    
    try:
        while True:
            # 读取摄像头帧
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame")
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
                        
                        # 只显示置信度大于0.5的检测结果
                        if conf > 0.5:
                            # 绘制边界框
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            
                            # 绘制标签和置信度
                            label_text = f'{label} {conf:.2f}'
                            label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                            
                            # 绘制标签背景
                            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                                        (x1 + label_size[0], y1), (0, 255, 0), -1)
                            
                            # 绘制标签文字
                            cv2.putText(frame, label_text, (x1, y1 - 5),
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            
            # 计算并显示FPS
            current_time = time.time()
            fps_counter += 1
            
            if current_time - prev_time >= 1.0:  # 每秒更新一次FPS显示
                fps_display = fps_counter
                fps_counter = 0
                prev_time = current_time
            
            # 在画面上显示FPS
            cv2.putText(frame, f'FPS: {fps_display}', (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # 显示画面
            cv2.imshow('Real-time YOLO Detection', frame)
            
            # 检查退出键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 'q'键或ESC键退出
                break
            elif key == ord('s'):  # 's'键保存当前帧
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f'yolo_detection_{timestamp}.jpg'
                cv2.imwrite(filename, frame)
                print(f"Image saved as {filename}")
    
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    
    finally:
        # 释放资源
        cap.release()
        cv2.destroyAllWindows()
        print("Camera released and windows closed")

if __name__ == "__main__":
    main()
