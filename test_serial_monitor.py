#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
串口监控脚本 - 测试 start button 功能
用于接收来自 T5AI 开发板的数据
"""

import serial
import time
import sys

def monitor_serial(port='/dev/cu.wchusbserial56D70345441', baudrate=115200):
    """监控串口数据"""
    try:
        # 打开串口
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"串口 {port} 已打开，波特率: {baudrate}")
        print("等待 start button 按下... (按 Ctrl+C 退出)")
        print("-" * 50)
        
        while True:
            if ser.in_waiting > 0:
                # 读取数据
                data = ser.readline().decode('utf-8').strip()
                if data:
                    print(f"[{time.strftime('%H:%M:%S')}] 收到: {data}")
                    
                    # 检查是否是 start button 消息
                    if data == "true":
                        print("🎉 检测到 Start 按钮被按下!")
                        print("✅ 串口通信功能正常!")
                        print("-" * 50)
                    elif data == "false":
                        print("🔄 检测到 Stop 按钮被按下!")
                        print("-" * 50)
                    
            time.sleep(0.1)  # 短暂休眠，避免CPU占用过高
            
    except serial.SerialException as e:
        print(f"串口错误: {e}")
        print("请检查:")
        print("1. 设备是否正确连接")
        print("2. 串口是否被其他程序占用")
        print("3. 串口名称是否正确")
    except KeyboardInterrupt:
        print("\n监控已停止")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口已关闭")

if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = '/dev/cu.wchusbserial56D70345441'
    
    print("=== echome_smart 串口监控工具 ===")
    print(f"监控串口: {port}")
    print("测试步骤:")
    print("1. 确保设备已烧录最新固件")
    print("2. 在设备上进入导航页面")
    print("3. 点击 'Start' 按钮")
    print("4. 观察串口输出")
    print("=" * 40)
    
    monitor_serial(port) 