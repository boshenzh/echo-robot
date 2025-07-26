import time
import json
import threading
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import queue
import numpy as np

@dataclass
class FocusSession:
    """专注会话数据结构"""
    session_id: str
    start_time: datetime
    target_duration_min: int
    target_duration_max: int
    current_duration: float = 0
    status: str = "active"  # active, paused, completed, interrupted
    break_count: int = 0
    focus_score: float = 0
    stress_level: float = 0
    interruption_points: List[Tuple[float, str]] = None
    
    def __post_init__(self):
        if self.interruption_points is None:
            self.interruption_points = []

@dataclass
class EEGState:
    """EEG状态数据结构"""
    timestamp: float
    attention: float
    stress: float
    t7_value: float
    t8_value: float
    focus_trend: str = "stable"  # rising, falling, stable
    stress_trend: str = "stable"
    should_break: bool = False
    break_reason: str = ""

class FocusAnalyzer:
    """专注力分析器"""
    
    def __init__(self, window_size=300):  # 5分钟窗口
        self.window_size = window_size
        self.attention_history = deque(maxlen=window_size)
        self.stress_history = deque(maxlen=window_size)
        self.timestamp_history = deque(maxlen=window_size)
        
        # 分析参数
        self.low_attention_threshold = 0.4
        self.high_stress_threshold = 0.6
        self.trend_window = 60  # 1分钟趋势分析
        self.volatility_threshold = 0.3
        
    def add_data_point(self, attention: float, stress: float) -> EEGState:
        """添加新的数据点并分析状态"""
        current_time = time.time()
        
        self.attention_history.append(attention)
        self.stress_history.append(stress)
        self.timestamp_history.append(current_time)
        
        # 计算趋势
        attention_trend = self._calculate_trend(self.attention_history)
        stress_trend = self._calculate_trend(self.stress_history)
        
        # 判断是否应该中断
        should_break, break_reason = self._should_take_break(attention, stress)
        
        return EEGState(
            timestamp=current_time,
            attention=attention,
            stress=stress,
            t7_value=0,  # 将在更新时设置
            t8_value=0,  # 将在更新时设置
            focus_trend=attention_trend,
            stress_trend=stress_trend,
            should_break=should_break,
            break_reason=break_reason
        )
    
    def _calculate_trend(self, data_history: deque) -> str:
        """计算趋势方向"""
        if len(data_history) < self.trend_window:
            return "stable"
        
        recent_data = list(data_history)[-self.trend_window:]
        
        # 使用线性回归计算趋势
        x = np.arange(len(recent_data))
        y = np.array(recent_data)
        
        if len(y) < 2:
            return "stable"
            
        # 计算斜率
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.001:
            return "rising"
        elif slope < -0.001:
            return "falling"
        else:
            return "stable"
    
    def _should_take_break(self, attention: float, stress: float) -> Tuple[bool, str]:
        """判断是否应该休息"""
        reasons = []
        
        # 规则1: 专注度低且压力高
        if attention < self.low_attention_threshold and stress > self.high_stress_threshold:
            reasons.append("低专注高压力")
        
        # 规则2: 专注度持续下降
        if (len(self.attention_history) >= self.trend_window and 
            self._calculate_trend(self.attention_history) == "falling"):
            recent_attention = list(self.attention_history)[-30:]  # 最近30秒
            if len(recent_attention) > 0 and np.mean(recent_attention) < 0.5:
                reasons.append("专注度持续下降")
        
        # 规则3: 压力持续上升
        if (len(self.stress_history) >= self.trend_window and 
            self._calculate_trend(self.stress_history) == "rising" and 
            stress > 0.7):
            reasons.append("压力持续上升")
        
        # 规则4: 注意力波动过大
        if len(self.attention_history) >= 60:  # 至少1分钟数据
            recent_attention = list(self.attention_history)[-60:]
            volatility = np.std(recent_attention)
            if volatility > self.volatility_threshold:
                reasons.append("注意力波动过大")
        
        should_break = len(reasons) > 0
        break_reason = "; ".join(reasons) if reasons else ""
        
        return should_break, break_reason
    
    def get_focus_score(self) -> float:
        """计算当前专注力评分 (0-1)"""
        if len(self.attention_history) == 0:
            return 0
        
        recent_attention = list(self.attention_history)[-60:]  # 最近1分钟
        recent_stress = list(self.stress_history)[-60:]
        
        if len(recent_attention) == 0:
            return 0
        
        # 专注力评分算法
        avg_attention = np.mean(recent_attention)
        avg_stress = np.mean(recent_stress)
        attention_stability = 1 - np.std(recent_attention)  # 稳定性越高越好
        
        # 综合评分
        focus_score = (avg_attention * 0.5 + 
                      (1 - avg_stress) * 0.3 + 
                      attention_stability * 0.2)
        
        return max(0, min(1, focus_score))

class SessionTimer:
    """会话计时器"""
    
    def __init__(self, min_duration: int, max_duration: int):
        self.min_duration = min_duration * 60  # 转换为秒
        self.max_duration = max_duration * 60
        self.start_time = time.time()
        self.pause_time = 0
        self.total_pause_duration = 0
        self.is_paused = False
        
    def get_elapsed_time(self) -> float:
        """获取已用时间（秒）"""
        current_time = time.time()
        if self.is_paused:
            return self.pause_time - self.start_time - self.total_pause_duration
        else:
            return current_time - self.start_time - self.total_pause_duration
    
    def pause(self):
        """暂停计时"""
        if not self.is_paused:
            self.pause_time = time.time()
            self.is_paused = True
    
    def resume(self):
        """恢复计时"""
        if self.is_paused:
            self.total_pause_duration += time.time() - self.pause_time
            self.is_paused = False
    
    def is_in_target_range(self) -> bool:
        """是否在目标时间范围内"""
        elapsed = self.get_elapsed_time()
        return self.min_duration <= elapsed <= self.max_duration
    
    def should_force_break(self) -> bool:
        """是否应该强制休息（达到最大时间）"""
        return self.get_elapsed_time() >= self.max_duration
    
    def can_suggest_break(self) -> bool:
        """是否可以建议休息（达到最小时间）"""
        return self.get_elapsed_time() >= self.min_duration

class FocusManagerSystem:
    """专注力管理系统核心类"""
    
    def __init__(self, eeg_system=None):
        self.eeg_system = eeg_system
        self.current_session = None
        self.analyzer = FocusAnalyzer()
        self.timer = None
        
        # 状态追踪
        self.is_monitoring = False
        self.last_break_suggestion = 0
        self.break_suggestion_cooldown = 300  # 5分钟冷却期
        
        # 数据队列
        self.state_queue = queue.Queue()
        self.notification_queue = queue.Queue()
        
        # 配置
        self.config = self._load_config()
        
        # 线程管理
        self.monitoring_thread = None
        self.analysis_thread = None
        
    def _load_config(self) -> Dict:
        """加载配置"""
        default_config = {
            "break_suggestion_enabled": True,
            "force_break_enabled": True,
            "music_enabled": True,
            "notification_sound": True,
            "analysis_interval": 1.0,  # 秒
            "min_break_duration": 5,   # 分钟
            "max_continuous_work": 90  # 分钟
        }
        
        try:
            with open('config/focus_settings.json', 'r') as f:
                config = json.load(f)
                default_config.update(config)
        except FileNotFoundError:
            pass
        
        return default_config
    
    def start_focus_session(self, min_duration: int, max_duration: int) -> str:
        """开始专注会话"""
        session_id = f"focus_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = FocusSession(
            session_id=session_id,
            start_time=datetime.now(),
            target_duration_min=min_duration,
            target_duration_max=max_duration
        )
        
        self.timer = SessionTimer(min_duration, max_duration)
        self.analyzer = FocusAnalyzer()  # 重置分析器
        
        # 开始监控
        self.is_monitoring = True
        self._start_monitoring_threads()
        
        print(f"🎯 专注会话开始: {session_id}")
        print(f"⏱️ 目标时间: {min_duration}-{max_duration} 分钟")
        
        return session_id
    
    def _start_monitoring_threads(self):
        """启动监控线程"""
        # EEG数据处理线程
        self.monitoring_thread = threading.Thread(
            target=self._eeg_monitoring_loop,
            name="EEGMonitoring"
        )
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        # 状态分析线程
        self.analysis_thread = threading.Thread(
            target=self._analysis_loop,
            name="StateAnalysis"
        )
        self.analysis_thread.daemon = True
        self.analysis_thread.start()
    
    def _eeg_monitoring_loop(self):
        """EEG数据监控循环"""
        while self.is_monitoring:
            try:
                if self.eeg_system and hasattr(self.eeg_system, 'metrics_queue'):
                    # 从EEG系统获取数据
                    if not self.eeg_system.metrics_queue.empty():
                        metrics_data = self.eeg_system.metrics_queue.get_nowait()
                        
                        if len(metrics_data) >= 4:
                            attention = metrics_data[1]
                            stress = metrics_data[3]
                            
                            # 分析状态
                            eeg_state = self.analyzer.add_data_point(attention, stress)
                            
                            # 更新会话状态
                            if self.current_session:
                                self.current_session.current_duration = self.timer.get_elapsed_time()
                                self.current_session.focus_score = self.analyzer.get_focus_score()
                                self.current_session.stress_level = stress
                            
                            # 将状态放入队列
                            self.state_queue.put(eeg_state)
                
                time.sleep(self.config['analysis_interval'])
                
            except Exception as e:
                print(f"EEG监控错误: {e}")
                time.sleep(1)
    
    def _analysis_loop(self):
        """状态分析循环"""
        while self.is_monitoring:
            try:
                if not self.state_queue.empty():
                    eeg_state = self.state_queue.get_nowait()
                    
                    # 检查是否需要建议休息
                    current_time = time.time()
                    if (eeg_state.should_break and 
                        self.timer.can_suggest_break() and
                        current_time - self.last_break_suggestion > self.break_suggestion_cooldown):
                        
                        self._suggest_break(eeg_state.break_reason)
                        self.last_break_suggestion = current_time
                    
                    # 检查是否需要强制休息
                    if self.timer.should_force_break():
                        self._force_break("达到最大专注时间")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"分析循环错误: {e}")
                time.sleep(1)
    
    def _suggest_break(self, reason: str):
        """建议休息"""
        if not self.config['break_suggestion_enabled']:
            return
        
        notification = {
            'type': 'break_suggestion',
            'reason': reason,
            'timestamp': time.time(),
            'elapsed_time': self.timer.get_elapsed_time(),
            'can_continue': True
        }
        
        self.notification_queue.put(notification)
        
        if self.current_session:
            self.current_session.interruption_points.append(
                (self.timer.get_elapsed_time(), f"建议休息: {reason}")
            )
        
        print(f"💡 建议休息: {reason}")
    
    def _force_break(self, reason: str):
        """强制休息"""
        if not self.config['force_break_enabled']:
            return
        
        notification = {
            'type': 'force_break',
            'reason': reason,
            'timestamp': time.time(),
            'elapsed_time': self.timer.get_elapsed_time(),
            'can_continue': False
        }
        
        self.notification_queue.put(notification)
        
        if self.current_session:
            self.current_session.status = "completed"
            self.current_session.interruption_points.append(
                (self.timer.get_elapsed_time(), f"强制结束: {reason}")
            )
        
        print(f"⏰ 强制休息: {reason}")
        self.end_session()
    
    def pause_session(self):
        """暂停会话"""
        if self.timer and self.current_session:
            self.timer.pause()
            self.current_session.status = "paused"
            print("⏸️ 会话已暂停")
    
    def resume_session(self):
        """恢复会话"""
        if self.timer and self.current_session:
            self.timer.resume()
            self.current_session.status = "active"
            print("▶️ 会话已恢复")
    
    def end_session(self):
        """结束会话"""
        self.is_monitoring = False
        
        if self.current_session:
            self.current_session.current_duration = self.timer.get_elapsed_time() if self.timer else 0
            self.current_session.status = "completed"
            
            # 保存会话数据
            self._save_session_data(self.current_session)
        
        print("✅ 专注会话结束")
    
    def _save_session_data(self, session: FocusSession):
        """保存会话数据"""
        try:
            session_data = {
                'session_id': session.session_id,
                'start_time': session.start_time.isoformat(),
                'target_duration_min': session.target_duration_min,
                'target_duration_max': session.target_duration_max,
                'actual_duration': session.current_duration,
                'final_focus_score': session.focus_score,
                'final_stress_level': session.stress_level,
                'break_count': session.break_count,
                'interruption_points': session.interruption_points,
                'status': session.status
            }
            
            filename = f"focus_session_{session.session_id}.json"
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=4)
            
            print(f"💾 会话数据已保存: {filename}")
            
        except Exception as e:
            print(f"保存会话数据错误: {e}")
    
    def get_current_status(self) -> Dict:
        """获取当前状态"""
        if not self.current_session or not self.timer:
            return {'status': 'inactive'}
        
        return {
            'status': 'active',
            'session_id': self.current_session.session_id,
            'elapsed_time': self.timer.get_elapsed_time(),
            'target_min': self.current_session.target_duration_min,
            'target_max': self.current_session.target_duration_max,
            'focus_score': self.current_session.focus_score,
            'stress_level': self.current_session.stress_level,
            'break_count': self.current_session.break_count,
            'can_suggest_break': self.timer.can_suggest_break(),
            'should_force_break': self.timer.should_force_break(),
            'is_paused': self.timer.is_paused if self.timer else False
        }
    
    def get_pending_notifications(self) -> List[Dict]:
        """获取待处理的通知"""
        notifications = []
        while not self.notification_queue.empty():
            try:
                notification = self.notification_queue.get_nowait()
                notifications.append(notification)
            except queue.Empty:
                break
        return notifications

# 测试代码
if __name__ == "__main__":
    print("🧠 专注力管理系统测试")
    
    # 创建系统实例
    focus_system = FocusManagerSystem()
    
    try:
        # 开始一个15-20分钟的专注会话
        session_id = focus_system.start_focus_session(15, 20)
        
        # 模拟运行
        for i in range(10):
            status = focus_system.get_current_status()
            print(f"状态: {status}")
            
            notifications = focus_system.get_pending_notifications()
            for notif in notifications:
                print(f"通知: {notif}")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        focus_system.end_session()
        print("✅ 测试完成")