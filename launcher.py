#!/usr/bin/env python3
"""
智能专注力管理与机械臂控制集成启动器
集成脑机接口监测和机械臂自动控制

功能：
1. 启动脑机监测系统 (web_focus_app.py)
2. 监控用户专注状态
3. 当需要休息时自动启动机械臂递送饮料
"""

import subprocess
import sys
import os
import time
import threading
import queue
import json
import signal
import requests
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class SystemState:
    """系统状态"""
    bci_running: bool = False
    robot_running: bool = False
    last_break_time: float = 0
    break_count: int = 0
    session_start_time: float = 0
    current_attention: float = 0
    current_stress: float = 0
    should_take_break: bool = False

class IntegratedLauncher:
    """集成启动器"""
    
    def __init__(self):
        self.state = SystemState()
        self.processes = {}
        self.monitoring_thread = None
        self.should_stop = False
        
        # 配置参数
        self.config = {
            'bci_url': 'http://localhost:8080',
            'check_interval': 5.0,  # 检查间隔（秒）
            'min_break_interval': 1800,  # 最小休息间隔（30分钟）
            'attention_threshold': 0.3,  # 注意力阈值
            'stress_threshold': 0.7,  # 压力阈值
            'break_duration': 300,  # 休息时长（5分钟）
            'robot_port': '/dev/ttyACM0',  # 机械臂端口
            'enable_robot': True,  # 是否启用机械臂
            'simulation_mode': False  # 模拟模式
        }
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        print("\n🛑 收到停止信号，正在关闭系统...")
        self.stop_all()
        sys.exit(0)
    
    def start_bci_system(self) -> bool:
        """启动脑机接口监测系统"""
        try:
            print("🧠 启动脑机接口监测系统...")
            
            # 构建启动命令
            python_cmd = sys.executable
            bci_script = os.path.join(os.path.dirname(__file__), 'web_focus_app.py')
            
            if not os.path.exists(bci_script):
                print(f"❌ 找不到脑机监测脚本: {bci_script}")
                return False
            
            # 启动进程
            process = subprocess.Popen(
                [python_cmd, bci_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            self.processes['bci'] = process
            
            # 等待服务启动
            print("⏳ 等待脑机服务启动...")
            for i in range(30):  # 最多等待30秒
                if self._check_bci_service():
                    self.state.bci_running = True
                    print("✅ 脑机监测系统启动成功")
                    
                    # 自动开始监测会话
                    self._start_focus_session()
                    return True
                time.sleep(1)
            
            print("❌ 脑机监测系统启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 启动脑机系统错误: {e}")
            return False
    
    def _check_bci_service(self) -> bool:
        """检查脑机服务是否可用"""
        try:
            response = requests.get(f"{self.config['bci_url']}/api/status", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _start_focus_session(self) -> bool:
        """开始专注会话"""
        try:
            print("📝 开始专注会话...")
            
            session_config = {
                'min_duration': 25,  # 25分钟最小专注时间
                'max_duration': 90,  # 90分钟最大专注时间
                'enable_music': True,
                'enable_break_advisor': True,
                'enable_notifications': True
            }
            
            response = requests.post(
                f"{self.config['bci_url']}/api/start_session",
                json=session_config,
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.state.session_start_time = time.time()
                    print("✅ 专注会话已开始")
                    return True
            
            print("❌ 开始专注会话失败")
            return False
            
        except Exception as e:
            print(f"❌ 开始会话错误: {e}")
            return False
    
    def start_monitoring(self):
        """开始监控循环"""
        print("👁️ 开始监控用户状态...")
        
        def monitoring_loop():
            while not self.should_stop:
                try:
                    # 获取当前状态
                    status = self._get_bci_status()
                    
                    if status:
                        # 更新状态
                        self.state.current_attention = status.get('status', {}).get('attention', 0)
                        self.state.current_stress = status.get('status', {}).get('stress', 0)
                        
                        # 检查是否需要休息
                        if self._should_trigger_break(status):
                            print(f"💡 检测到需要休息: 注意力={self.state.current_attention:.2f}, 压力={self.state.current_stress:.2f}")
                            self._trigger_break()
                    
                    time.sleep(self.config['check_interval'])
                    
                except Exception as e:
                    print(f"监控错误: {e}")
                    time.sleep(10)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def _get_bci_status(self) -> Optional[Dict[str, Any]]:
        """获取脑机接口状态"""
        try:
            response = requests.get(f"{self.config['bci_url']}/api/status", timeout=3)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"获取状态错误: {e}")
        return None
    
    def _should_trigger_break(self, status: Dict[str, Any]) -> bool:
        """判断是否应该触发休息"""
        current_time = time.time()
        
        # 检查最小休息间隔
        if current_time - self.state.last_break_time < self.config['min_break_interval']:
            return False
        
        # 获取状态数据
        attention = status.get('status', {}).get('attention', 1)
        stress = status.get('status', {}).get('stress', 0)
        duration = status.get('status', {}).get('duration', 0)
        
        # 休息判断规则
        need_break = False
        reasons = []
        
        # 规则1: 低注意力
        if attention < self.config['attention_threshold']:
            need_break = True
            reasons.append(f"注意力过低({attention:.2f})")
        
        # 规则2: 高压力
        if stress > self.config['stress_threshold']:
            need_break = True
            reasons.append(f"压力过高({stress:.2f})")
        
        # 规则3: 持续时间过长
        if duration > 3600:  # 超过1小时
            need_break = True
            reasons.append(f"持续专注时间过长({duration/60:.0f}分钟)")
        
        # 规则4: 综合判断
        if attention < 0.5 and stress > 0.5:
            need_break = True
            reasons.append("综合状态不佳")
        
        if need_break and reasons:
            print(f"🚨 触发休息原因: {', '.join(reasons)}")
        
        return need_break
    
    def _trigger_break(self):
        """触发休息流程"""
        try:
            print("☕ 触发休息流程...")
            
            # 更新状态
            self.state.should_take_break = True
            self.state.last_break_time = time.time()
            self.state.break_count += 1
            
            # 通知脑机系统
            self._notify_break_start()
            
            # 启动机械臂
            if self.config['enable_robot'] and not self.config['simulation_mode']:
                self._start_robot_delivery()
            else:
                print("🎭 模拟模式: 机械臂递送饮料")
                self._simulate_robot_delivery()
            
            # 等待休息结束
            print(f"⏱️ 休息 {self.config['break_duration']/60:.0f} 分钟...")
            time.sleep(self.config['break_duration'])
            
            # 恢复工作
            self._resume_work()
            
        except Exception as e:
            print(f"❌ 触发休息错误: {e}")
        finally:
            self.state.should_take_break = False
    
    def _notify_break_start(self):
        """通知脑机系统开始休息"""
        try:
            requests.post(
                f"{self.config['bci_url']}/api/take_break",
                json={'duration': self.config['break_duration'] / 60},
                timeout=3
            )
            print("📢 已通知脑机系统开始休息")
        except Exception as e:
            print(f"通知错误: {e}")
    
    def _start_robot_delivery(self):
        """启动机械臂递送"""
        try:
            print("🤖 启动机械臂递送系统...")
            
            # 构建机械臂脚本路径
            robot_script = os.path.join(
                os.path.dirname(__file__), 
                'echo-robot', 
                'lerobot_yolo.py'
            )
            
            if not os.path.exists(robot_script):
                print(f"❌ 找不到机械臂控制脚本: {robot_script}")
                return
            
            # 启动机械臂进程
            python_cmd = sys.executable
            env = os.environ.copy()
            
            # 设置环境变量
            env['ROBOT_PORT'] = self.config['robot_port']
            env['ROBOT_MODE'] = 'delivery'  # 递送模式
            
            process = subprocess.Popen(
                [python_cmd, robot_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env,
                bufsize=1
            )
            
            self.processes['robot'] = process
            self.state.robot_running = True
            
            print("✅ 机械臂系统已启动")
            
            # 监控机械臂输出
            self._monitor_robot_output(process)
            
        except Exception as e:
            print(f"❌ 启动机械臂错误: {e}")
    
    def _monitor_robot_output(self, process):
        """监控机械臂输出"""
        def output_reader(proc):
            try:
                for line in iter(proc.stdout.readline, ''):
                    if line:
                        print(f"[机械臂] {line.strip()}")
                    if "任务完成" in line or "Task completed" in line:
                        break
            except Exception as e:
                print(f"读取输出错误: {e}")
        
        reader_thread = threading.Thread(
            target=output_reader, 
            args=(process,),
            daemon=True
        )
        reader_thread.start()
    
    def _simulate_robot_delivery(self):
        """模拟机械臂递送"""
        steps = [
            "🔍 检测水杯位置...",
            "🦾 移动到抓取位置...",
            "✋ 抓取水杯...",
            "🚶 移动到用户位置...",
            "📍 放置水杯...",
            "🏠 返回初始位置..."
        ]
        
        for step in steps:
            print(f"[模拟] {step}")
            time.sleep(2)
        
        print("✅ [模拟] 饮料递送完成")
    
    def _resume_work(self):
        """恢复工作"""
        try:
            print("💪 休息结束，恢复工作状态...")
            
            # 停止机械臂
            if 'robot' in self.processes:
                self._stop_process('robot')
            
            # 通知脑机系统恢复
            requests.post(
                f"{self.config['bci_url']}/api/resume_session",
                timeout=3
            )
            
            print("✅ 已恢复工作状态")
            
        except Exception as e:
            print(f"恢复工作错误: {e}")
    
    def _stop_process(self, name: str):
        """停止指定进程"""
        if name in self.processes:
            process = self.processes[name]
            if process.poll() is None:  # 进程还在运行
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            del self.processes[name]
            print(f"✅ 已停止进程: {name}")
    
    def stop_all(self):
        """停止所有系统"""
        print("🛑 停止所有系统...")
        self.should_stop = True
        
        # 停止监控线程
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        # 停止所有进程
        for name in list(self.processes.keys()):
            self._stop_process(name)
        
        print("✅ 所有系统已停止")
    
    def run(self):
        """运行集成系统"""
        print("🚀 启动智能专注力管理与机械臂控制集成系统")
        print("=" * 60)
        
        try:
            # 启动脑机系统
            if not self.start_bci_system():
                print("❌ 无法启动脑机系统")
                return
            
            # 开始监控
            self.start_monitoring()
            
            # 显示状态信息
            print("\n📊 系统状态:")
            print(f"   脑机监测: {'运行中' if self.state.bci_running else '未运行'}")
            print(f"   机械臂: {'启用' if self.config['enable_robot'] else '禁用'}")
            print(f"   监控间隔: {self.config['check_interval']}秒")
            print(f"   最小休息间隔: {self.config['min_break_interval']/60:.0f}分钟")
            print(f"   注意力阈值: {self.config['attention_threshold']}")
            print(f"   压力阈值: {self.config['stress_threshold']}")
            print("\n📋 按 Ctrl+C 停止系统\n")
            
            # 主循环
            while not self.should_stop:
                # 显示实时状态
                if int(time.time()) % 30 == 0:  # 每30秒显示一次
                    print(f"\r⏰ {datetime.now().strftime('%H:%M:%S')} | "
                          f"注意力: {self.state.current_attention:.2f} | "
                          f"压力: {self.state.current_stress:.2f} | "
                          f"休息次数: {self.state.break_count}", end='', flush=True)
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 用户中断")
        except Exception as e:
            print(f"\n❌ 系统错误: {e}")
        finally:
            self.stop_all()

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='智能专注力管理与机械臂控制集成系统')
    parser.add_argument('--simulation', action='store_true', help='模拟模式（不启动真实机械臂）')
    parser.add_argument('--no-robot', action='store_true', help='禁用机械臂功能')
    parser.add_argument('--port', type=str, default='/dev/ttyACM0', help='机械臂串口')
    parser.add_argument('--break-interval', type=int, default=30, help='最小休息间隔（分钟）')
    
    args = parser.parse_args()
    
    # 创建启动器
    launcher = IntegratedLauncher()
    
    # 应用命令行参数
    if args.simulation:
        launcher.config['simulation_mode'] = True
        print("🎭 运行在模拟模式")
    
    if args.no_robot:
        launcher.config['enable_robot'] = False
        print("🚫 机械臂功能已禁用")
    
    launcher.config['robot_port'] = args.port
    launcher.config['min_break_interval'] = args.break_interval * 60
    
    # 运行系统
    launcher.run()

if __name__ == "__main__":
    main()