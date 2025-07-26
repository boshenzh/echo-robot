#!/usr/bin/env python3
"""
简单的串口trigger监听测试
仅用于测试串口通信是否正常工作
"""

import serial
import time

def test_serial_trigger():
    """测试串口trigger监听"""
    print("串口trigger监听测试")
    print("="*30)
    
    try:
        # 连接串口
        print("正在连接串口 /dev/ttyACM0...")
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
        print("✅ 串口连接成功!")
        print(f"串口信息: {ser.name}")
        print(f"波特率: {ser.baudrate}")
        print("等待接收 'true' 信号...")
        print("="*30)
        
        # 监听循环
        while True:
            try:
                # 检查是否有数据
                if ser.in_waiting > 0:
                    # 读取数据
                    data = ser.readline().decode('utf-8').strip()
                    print(f"收到数据: '{data}'")
                    
                    # 检查是否是trigger信号
                    if data == 'true':
                        print("🎯 收到trigger信号!")
                        print("触发动作: 机械臂移动到预设位置")
                        print("-" * 30)
                    elif data:
                        print(f"收到其他数据: '{data}'")
                
                # 短暂延时，避免CPU占用过高
                time.sleep(0.01)
                
            except KeyboardInterrupt:
                print("\n用户中断程序")
                break
            except Exception as e:
                print(f"读取数据时出错: {e}")
                break
                
    except serial.SerialException as e:
        print(f"❌ 串口连接失败: {e}")
        print("请检查:")
        print("1. 串口设备是否存在")
        print("2. 是否有权限访问串口")
        print("3. 串口是否被其他程序占用")
    except Exception as e:
        print(f"❌ 程序出错: {e}")
    finally:
        # 关闭串口
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口已关闭")
        print("程序结束")

if __name__ == "__main__":
    test_serial_trigger() 
