#!/usr/bin/env python3
"""
智能专注力管理与机械臂控制集成系统
主程序 - 持续监听trigger信号并管理系统状态

触发信号类型：
1. start:<duration> - 开始专注会话，指定持续时间（分钟）
2. finish - 结束当前会话，保存数据并复位
3. 专注力下降时自动触发机械臂
"""

import subprocess
import sys
import os
import time
import threading
import json
import signal
import serial
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from collections import deque
import random

@dataclass
class SessionData:
    """会话数据记录"""
    start_time: float
    end_time: Optional[float] = None
    duration_minutes: int = 0
    attention_history: List[float] = field(default_factory=list)
    stress_history: List[float] = field(default_factory=list)
    break_times: List[float] = field(default_factory=list)
    robot_triggers: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_metrics(self, attention: float, stress: float):
        """添加指标数据"""
        self.attention_history.append(attention)
        self.stress_history.append(stress)
    
    def add_break(self, timestamp: float):
        """记录休息时间"""
        self.break_times.append(timestamp)
    
    def add_robot_trigger(self, reason: str, attention: float, stress: float):
        """记录机械臂触发事件"""
        self.robot_triggers.append({
            'timestamp': time.time(),
            'reason': reason,
            'attention': attention,
            'stress': stress
        })

@dataclass
class SystemState:
    """系统状态"""
    is_running: bool = False
    in_session: bool = False
    session_start_time: float = 0
    session_duration: int = 0  # 分钟
    current_attention: float = 0.8
    current_stress: float = 0.2
    robot_busy: bool = False
    last_robot_trigger: float = 0
    simulation_mode: bool = True

class EEGSimulator:
    """EEG数据模拟器"""
    def __init__(self):
        self.base_attention = 0.8
        self.base_stress = 0.2
        self.time_factor = 0
        self.noise_level = 0.05
        
    def update(self, elapsed_minutes: float):
        """根据经过时间更新模拟数据"""
        # 注意力随时间下降
        attention_decay = 0.01 * elapsed_minutes
        self.base_attention = max(0.3, 0.85 - attention_decay)
        
        # 压力随时间上升
        stress_increase = 0.015 * elapsed_minutes
        self.base_stress = min(0.9, 0.2 + stress_increase)
        
        # 添加随机噪声
        attention = self.base_attention + random.uniform(-self.noise_level, self.noise_level)
        stress = self.base_stress + random.uniform(-self.noise_level, self.noise_level)
        
        return max(0, min(1, attention)), max(0, min(1, stress))

class IntegratedSystem:
    """集成系统主类"""
    
    def __init__(self, simulation_mode=True):
        self.state = SystemState(simulation_mode=simulation_mode)
        self.current_session = None
        self.session_history = []
        self.ser = None
        self.monitoring_thread = None
        self.robot_process = None
        
        # EEG模拟器
        self.eeg_simulator = EEGSimulator() if simulation_mode else None
        
        # 配置参数
        self.config = {
            'serial_port': '/dev/ttyACM0',
            'baud_rate': 115200,
            'monitor_interval': 1.0,  # 监控间隔（秒）
            'attention_threshold': 0.5,  # 注意力阈值
            'stress_threshold': 0.7,  # 压力阈值
            'robot_cooldown': 300,  # 机械臂触发冷却时间（5分钟）
            'data_dir': 'session_data'  # 数据保存目录
        }
        
        # 创建数据目录
        os.makedirs(self.config['data_dir'], exist_ok=True)
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        print("\n🛑 收到停止信号...")
        self.cleanup()
        sys.exit(0)
    
    def initialize_serial(self) -> bool:
        """初始化串口连接"""
        try:
            if self.state.simulation_mode:
                print("🎮 模拟模式 - 跳过串口初始化")
                return True
                
            print(f"📡 连接串口 {self.config['serial_port']}...")
            self.ser = serial.Serial(
                self.config['serial_port'], 
                self.config['baud_rate'], 
                timeout=0.1
            )
            print("✅ 串口连接成功")
            return True
        except Exception as e:
            print(f"❌ 串口连接失败: {e}")
            return False
    
    def listen_for_triggers(self):
        """主循环 - 监听trigger信号"""
        print("👂 开始监听trigger信号...")
        print("=" * 60)
        print("支持的命令:")
        print("  start:<分钟数> - 开始专注会话")
        print("  finish - 结束当前会话")
        print("  status - 查看当前状态")
        print("  quit - 退出程序")
        print("=" * 60)
        
        self.state.is_running = True
        
        while self.state.is_running:
            try:
                # 获取trigger信号
                trigger = self._get_trigger()
                
                if trigger:
                    self._process_trigger(trigger)
                
                # 短暂延时
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 错误: {e}")
    
    def _get_trigger(self) -> Optional[str]:
        """获取trigger信号"""
        if self.state.simulation_mode:
            # 模拟模式 - 从控制台读取
            import select
            import sys
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline().strip()
                return line if line else None
        else:
            # 实机模式 - 从串口读取
            if self.ser and self.ser.in_waiting > 0:
                try:
                    data = self.ser.readline().decode('utf-8').strip()
                    return data
                except:
                    pass
        return None
    
    def _process_trigger(self, trigger: str):
        """处理trigger信号"""
        print(f"\n📨 收到信号: '{trigger}'")
        
        if trigger.startswith('start:'):
            # 开始会话
            try:
                duration = int(trigger.split(':')[1])
                self.start_session(duration)
            except:
                print("❌ 无效的开始命令，格式: start:<分钟数>")
                
        elif trigger == 'finish':
            # 结束会话
            self.finish_session()
            
        elif trigger == 'status':
            # 显示状态
            self.show_status()
            
        elif trigger == 'quit':
            # 退出程序
            print("👋 退出程序...")
            self.state.is_running = False
            
        else:
            print(f"❓ 未知命令: '{trigger}'")
    
    def start_session(self, duration_minutes: int):
        """开始专注会话"""
        if self.state.in_session:
            print("⚠️  已有会话进行中，请先结束当前会话")
            return
        
        print(f"🚀 开始{duration_minutes}分钟专注会话")
        
        # 创建新会话
        self.current_session = SessionData(
            start_time=time.time(),
            duration_minutes=duration_minutes
        )
        
        # 更新状态
        self.state.in_session = True
        self.state.session_start_time = time.time()
        self.state.session_duration = duration_minutes
        
        # 重置EEG模拟器
        if self.eeg_simulator:
            self.eeg_simulator = EEGSimulator()
        
        # 启动监控线程
        self.start_monitoring()
        
        print("✅ 会话已开始，正在监控专注状态...")
    
    def start_monitoring(self):
        """启动监控线程"""
        def monitor_loop():
            while self.state.in_session:
                try:
                    # 计算经过时间
                    elapsed = time.time() - self.state.session_start_time
                    elapsed_minutes = elapsed / 60
                    
                    # 检查是否超时
                    if elapsed_minutes >= self.state.session_duration:
                        print(f"\n⏰ 会话时间到({self.state.session_duration}分钟)")
                        self.finish_session()
                        break
                    
                    # 获取EEG数据
                    if self.state.simulation_mode:
                        attention, stress = self.eeg_simulator.update(elapsed_minutes)
                    else:
                        # TODO: 从实际EEG设备获取数据
                        attention, stress = 0.8, 0.2
                    
                    # 更新状态
                    self.state.current_attention = attention
                    self.state.current_stress = stress
                    
                    # 记录数据
                    if self.current_session:
                        self.current_session.add_metrics(attention, stress)
                    
                    # 检查是否需要触发机械臂
                    self._check_robot_trigger(attention, stress)
                    
                    # 显示实时状态（每10秒）
                    if int(elapsed) % 10 == 0:
                        remaining = self.state.session_duration - elapsed_minutes
                        print(f"\r⏱️  {elapsed_minutes:.1f}/{self.state.session_duration}分钟 | "
                              f"注意力: {attention:.2f} | 压力: {stress:.2f} | "
                              f"剩余: {remaining:.1f}分钟", end='', flush=True)
                    
                    time.sleep(self.config['monitor_interval'])
                    
                except Exception as e:
                    print(f"\n❌ 监控错误: {e}")
                    break
        
        self.monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitoring_thread.start()
    
    def _check_robot_trigger(self, attention: float, stress: float):
        """检查是否需要触发机械臂"""
        if self.state.robot_busy:
            return
            
        # 检查冷却时间
        if time.time() - self.state.last_robot_trigger < self.config['robot_cooldown']:
            return
        
        # 触发条件
        trigger_reason = None
        
        if attention < self.config['attention_threshold']:
            trigger_reason = f"注意力过低({attention:.2f})"
        elif stress > self.config['stress_threshold']:
            trigger_reason = f"压力过高({stress:.2f})"
        elif attention < 0.6 and stress > 0.6:
            trigger_reason = "综合状态不佳"
        
        if trigger_reason:
            print(f"\n🤖 触发机械臂: {trigger_reason}")
            self.trigger_robot(trigger_reason, attention, stress)
    
    def trigger_robot(self, reason: str, attention: float, stress: float):
        """触发机械臂动作"""
        self.state.robot_busy = True
        self.state.last_robot_trigger = time.time()
        
        # 记录触发事件
        if self.current_session:
            self.current_session.add_robot_trigger(reason, attention, stress)
            self.current_session.add_break(time.time())
        
        if self.state.simulation_mode:
            # 模拟模式
            print("🎮 [模拟] 机械臂执行递送任务...")
            time.sleep(3)  # 模拟执行时间
            print("✅ [模拟] 递送完成")
        else:
            # 实机模式
            self._execute_robot_delivery()
        
        self.state.robot_busy = False
    
    def _execute_robot_delivery(self):
        """执行实际的机械臂递送"""
        try:
            # 向机械臂发送触发信号
            if self.ser:
                self.ser.write(b'true\n')
                print("📤 已发送机械臂触发信号")
            
            # TODO: 启动机械臂控制程序或等待完成信号
            
        except Exception as e:
            print(f"❌ 机械臂执行错误: {e}")
    
    def finish_session(self):
        """结束当前会话"""
        if not self.state.in_session:
            print("⚠️  当前没有进行中的会话")
            return
        
        print("\n📝 结束会话...")
        
        # 更新会话数据
        if self.current_session:
            self.current_session.end_time = time.time()
            self.session_history.append(self.current_session)
            
            # 保存数据
            self.save_session_data()
            
            # 生成可视化
            self.generate_visualization()
        
        # 重置状态
        self.state.in_session = False
        self.current_session = None
        
        # 重置机械臂
        self.reset_robot()
        
        print("✅ 会话已结束")
    
    def save_session_data(self):
        """保存会话数据"""
        if not self.current_session:
            return
            
        timestamp = datetime.fromtimestamp(self.current_session.start_time).strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.config['data_dir'], f'session_{timestamp}.json')
        
        data = {
            'start_time': self.current_session.start_time,
            'end_time': self.current_session.end_time,
            'duration_minutes': self.current_session.duration_minutes,
            'attention_history': self.current_session.attention_history,
            'stress_history': self.current_session.stress_history,
            'break_times': self.current_session.break_times,
            'robot_triggers': self.current_session.robot_triggers,
            'statistics': {
                'avg_attention': np.mean(self.current_session.attention_history),
                'avg_stress': np.mean(self.current_session.stress_history),
                'min_attention': np.min(self.current_session.attention_history),
                'max_stress': np.max(self.current_session.stress_history),
                'break_count': len(self.current_session.break_times),
                'robot_trigger_count': len(self.current_session.robot_triggers)
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 数据已保存: {filename}")
    
    def generate_visualization(self):
        """生成会话可视化"""
        if not self.current_session or not self.current_session.attention_history:
            return
        
        timestamp = datetime.fromtimestamp(self.current_session.start_time).strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.config['data_dir'], f'session_{timestamp}.png')
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
        
        # 时间轴
        time_points = np.linspace(0, self.current_session.duration_minutes, 
                                 len(self.current_session.attention_history))
        
        # 注意力图
        ax1.plot(time_points, self.current_session.attention_history, 'b-', label='注意力')
        ax1.axhline(y=self.config['attention_threshold'], color='r', linestyle='--', 
                   label=f'阈值({self.config["attention_threshold"]})')
        ax1.set_ylabel('注意力水平')
        ax1.set_ylim(0, 1)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 压力图
        ax2.plot(time_points, self.current_session.stress_history, 'r-', label='压力')
        ax2.axhline(y=self.config['stress_threshold'], color='r', linestyle='--',
                   label=f'阈值({self.config["stress_threshold"]})')
        ax2.set_ylabel('压力水平')
        ax2.set_xlabel('时间（分钟）')
        ax2.set_ylim(0, 1)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 标记机械臂触发点
        for trigger in self.current_session.robot_triggers:
            trigger_time = (trigger['timestamp'] - self.current_session.start_time) / 60
            ax1.axvline(x=trigger_time, color='g', linestyle=':', alpha=0.5)
            ax2.axvline(x=trigger_time, color='g', linestyle=':', alpha=0.5)
        
        # 设置标题
        session_time = datetime.fromtimestamp(self.current_session.start_time).strftime('%Y-%m-%d %H:%M')
        plt.suptitle(f'专注会话分析 - {session_time}')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()
        
        print(f"📊 可视化已保存: {filename}")
    
    def reset_robot(self):
        """重置机械臂到零位置"""
        print("🔄 重置机械臂...")
        
        if self.state.simulation_mode:
            print("✅ [模拟] 机械臂已重置到零位置")
        else:
            # TODO: 发送重置命令到机械臂
            if self.ser:
                self.ser.write(b'reset\n')
    
    def show_status(self):
        """显示当前状态"""
        print("\n📊 系统状态:")
        print(f"  模式: {'模拟' if self.state.simulation_mode else '实机'}")
        print(f"  会话状态: {'进行中' if self.state.in_session else '空闲'}")
        
        if self.state.in_session:
            elapsed = (time.time() - self.state.session_start_time) / 60
            remaining = self.state.session_duration - elapsed
            print(f"  进度: {elapsed:.1f}/{self.state.session_duration}分钟")
            print(f"  剩余: {remaining:.1f}分钟")
            print(f"  注意力: {self.state.current_attention:.2f}")
            print(f"  压力: {self.state.current_stress:.2f}")
            
            if self.current_session:
                print(f"  休息次数: {len(self.current_session.break_times)}")
                print(f"  机械臂触发: {len(self.current_session.robot_triggers)}次")
        
        print(f"  历史会话: {len(self.session_history)}个")
        print()
    
    def cleanup(self):
        """清理资源"""
        # 结束当前会话
        if self.state.in_session:
            self.finish_session()
        
        # 关闭串口
        if self.ser and self.ser.is_open:
            self.ser.close()
        
        print("✅ 清理完成")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='智能专注力管理与机械臂控制系统')
    parser.add_argument('--real', action='store_true', help='使用实机模式（默认为模拟模式）')
    parser.add_argument('--port', type=str, default='/dev/ttyACM0', help='串口设备')
    
    args = parser.parse_args()
    
    print("🧠 智能专注力管理与机械臂控制系统")
    print("=" * 60)
    
    # 创建系统实例
    system = IntegratedSystem(simulation_mode=not args.real)
    
    if args.real:
        system.config['serial_port'] = args.port
    
    # 初始化
    if not args.real or system.initialize_serial():
        # 开始监听
        try:
            system.listen_for_triggers()
        except KeyboardInterrupt:
            print("\n\n👋 用户中断")
        finally:
            system.cleanup()
    else:
        print("❌ 系统初始化失败")

if __name__ == "__main__":
    main()