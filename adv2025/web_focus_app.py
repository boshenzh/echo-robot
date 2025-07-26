import time
import json
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import queue
from collections import deque
import random
import math

# 导入我们的核心模块
try:
    from eeg_monitor_system import EEGMonitorSystem
except ImportError:
    EEGMonitorSystem = None
    print("⚠️ EEG监控系统模块未找到")

try:
    from focus_manager_system import FocusManagerSystem
except ImportError:
    FocusManagerSystem = None
    print("⚠️ 专注管理系统模块未找到")

try:
    from intelligent_break_advisor import IntelligentBreakAdvisor, BreakType
except ImportError:
    IntelligentBreakAdvisor = None
    BreakType = None
    print("⚠️ 智能休息建议模块未找到")

try:
    from music_recommendation_engine import MusicRecommendationEngine
except ImportError:
    MusicRecommendationEngine = None
    print("⚠️ 音乐推荐引擎模块未找到")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'focus_app_secret_2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class IntegratedFocusApp:
    """集成专注力应用"""
    
    def __init__(self):
        # 初始化各个子系统
        try:
            if EEGMonitorSystem:
                self.eeg_system = EEGMonitorSystem()
                print("✅ EEG监控系统初始化成功")
            else:
                self.eeg_system = None
                print("⚠️ EEG系统未可用，将使用模拟数据")
        except Exception as e:
            print(f"⚠️ EEG系统初始化失败: {e}")
            self.eeg_system = None
        
        # 初始化其他子系统（如果可用）
        if FocusManagerSystem:
            try:
                self.focus_manager = FocusManagerSystem(self.eeg_system)
            except:
                self.focus_manager = None
        else:
            self.focus_manager = None
            
        if IntelligentBreakAdvisor:
            try:
                self.break_advisor = IntelligentBreakAdvisor()
            except:
                self.break_advisor = None
        else:
            self.break_advisor = None
            
        if MusicRecommendationEngine:
            try:
                self.music_engine = MusicRecommendationEngine()
            except:
                self.music_engine = None
        else:
            self.music_engine = None
        
        # 应用状态
        self.clients = set()
        self.app_running = False
        self.current_session_config = None
        
        # 实时数据缓存 - 使用与webtest.py相同的格式
        self.real_time_data = {
            'eeg': deque(maxlen=500),
            'metrics': deque(maxlen=100),
            'status': {
                'attention': 0,
                'stress': 0,
                'duration': 0,
                'eeg_count': 0,
                'metrics_count': 0
            }
        }
        
        # 数据处理相关
        self.start_time = None
        self.monitoring_thread = None
        
        # 广播线程
        self.broadcast_thread = None
        self.start_broadcast_thread()
    
    def start_broadcast_thread(self):
        """启动数据广播线程 - 使用与webtest.py相同的格式"""
        def broadcast_loop():
            print("📡 启动数据广播线程...")
            
            while True:
                try:
                    if self.app_running and self.clients:
                        # 使用与webtest.py完全相同的数据格式
                        broadcast_data = {
                            'type': 'realtime_update',
                            'eeg_data': list(self.real_time_data['eeg'])[-50:],  # 最近50个点
                            'metrics_data': list(self.real_time_data['metrics'])[-20:],  # 最近20个点
                            'status': self.real_time_data['status'].copy(),
                            'timestamp': time.time()
                        }
                        
                        # 添加智能休息建议
                        if self.break_advisor and len(self.real_time_data['metrics']) > 0:
                            latest_metrics = self.real_time_data['metrics'][-1]
                            try:
                                # 计算专注评分
                                attention = latest_metrics.get('attention', 0)
                                stress = latest_metrics.get('stress', 0)
                                focus_score = attention * 0.7 + (1 - stress) * 0.3
                                
                                # 获取会话时长
                                session_duration = self.real_time_data['status'].get('duration', 0)
                                
                                # 分析并获取休息建议
                                break_recommendation = self.break_advisor.analyze_and_recommend(
                                    attention, stress, focus_score, session_duration
                                )
                                
                                if break_recommendation:
                                    broadcast_data['break_suggestion'] = {
                                        'type': break_recommendation.break_type.value,
                                        'duration': break_recommendation.recommended_duration,
                                        'urgency': break_recommendation.urgency_level,
                                        'reason': break_recommendation.reason,
                                        'activities': break_recommendation.suggested_activities,
                                        'confidence': break_recommendation.confidence_score
                                    }
                                    
                            except Exception as advisor_error:
                                print(f"休息建议分析错误: {advisor_error}")
                        
                        # 添加音乐推荐
                        if self.music_engine and self.current_session_config and self.current_session_config.get('enable_music', False):
                            try:
                                # 生成音乐推荐
                                music_recommendation = self._generate_music_recommendation()
                                if music_recommendation:
                                    broadcast_data['music_status'] = {
                                        'recommendation': music_recommendation
                                    }
                            except Exception as music_error:
                                print(f"音乐推荐错误: {music_error}")
                        
                        # 发送到所有客户端 - 使用dashboard.html期望的事件名称
                        socketio.emit('data_update', broadcast_data)
                    
                    time.sleep(0.1)  # 每100ms发送一次
                    
                except Exception as e:
                    print(f"广播错误: {e}")
                    time.sleep(1)
        
        self.broadcast_thread = threading.Thread(target=broadcast_loop, daemon=True)
        self.broadcast_thread.start()
    
    def _generate_music_recommendation(self):
        """生成音乐推荐"""
        try:
            if not self.real_time_data['metrics']:
                return None
                
            latest_metrics = self.real_time_data['metrics'][-1]
            attention = latest_metrics.get('attention', 0.5)
            stress = latest_metrics.get('stress', 0.5)
            
            # 基于当前状态推荐音乐
            if stress > 0.7:
                music_type = "relaxation"
                reason = "检测到高压力，建议播放放松音乐"
                volume = 0.4  # 较低音量
            elif attention < 0.4:
                music_type = "focus_ambient"
                reason = "注意力较低，建议播放专注环境音"
                volume = 0.6
            elif attention > 0.8:
                music_type = "classical"
                reason = "专注状态良好，建议播放古典音乐"
                volume = 0.5
            else:
                music_type = "nature_sounds"
                reason = "状态平稳，建议播放自然声音"
                volume = 0.5
            
            # 模拟音乐曲目
            tracks = [
                {
                    "title": f"专注音乐 - {music_type}",
                    "artist": "AI音乐助手",
                    "duration": "30:00"
                }
            ]
            
            return {
                "tracks": tracks,
                "reason": reason,
                "adaptive_volume": volume,
                "music_type": music_type
            }
            
        except Exception as e:
            print(f"生成音乐推荐错误: {e}")
            return None
    
    def start_focus_session(self, min_duration: int, max_duration: int, 
                           enable_music: bool = True, enable_break_advisor: bool = True,
                           enable_notifications: bool = True, enable_data_logging: bool = False,
                           enable_adaptive_breaks: bool = False):
        """开始专注会话"""
        try:
            print(f"🎯 启动专注会话: {min_duration}-{max_duration}分钟")
            
            # 记录会话开始时间
            start_time = time.time()
            
            self.current_session_config = {
                'min_duration': min_duration,
                'max_duration': max_duration,
                'enable_music': enable_music,
                'enable_break_advisor': enable_break_advisor,
                'enable_notifications': enable_notifications,
                'enable_data_logging': enable_data_logging,
                'enable_adaptive_breaks': enable_adaptive_breaks,
                'start_time': start_time,  # 添加开始时间
                'start_time_iso': datetime.fromtimestamp(start_time).isoformat()  # 可读格式
            }
            
            # 尝试启动EEG系统
            if self.eeg_system:
                try:
                    if self.eeg_system.start_system():
                        print("✅ EEG监控系统启动成功")
                        self.app_running = True
                        self.start_time = start_time  # 使用统一的开始时间
                        self._start_monitoring_loop()
                    else:
                        print("⚠️ EEG系统启动失败，使用模拟模式")
                        self._start_simulation_mode()
                except Exception as eeg_error:
                    print(f"⚠️ EEG系统启动异常: {eeg_error}")
                    self._start_simulation_mode()
            else:
                print("⚠️ EEG系统不可用，使用模拟模式")
                self._start_simulation_mode()
            
            return {
                'success': True, 
                'message': '专注会话已启动',
                'session_config': self.current_session_config
            }
            
        except Exception as e:
            print(f"❌ 启动专注会话错误: {e}")
            return {'success': False, 'message': f'启动失败: {str(e)}'}
    
    def _start_simulation_mode(self):
        """启动模拟数据模式 - 使用与webtest.py相同的数据格式"""
        print("🎭 启动模拟数据模式")
        self.app_running = True
        
        # 如果没有设置开始时间，设置为当前时间
        if not self.start_time:
            self.start_time = time.time()
        
        def simulation_loop():
            import random
            import math
            
            while self.app_running:
                try:
                    current_time = time.time()
                    elapsed = current_time - self.start_time
                    
                    # 生成模拟EEG数据 - 与webtest.py格式完全一致
                    t7_value = 4000 + 200 * math.sin(elapsed * 2) + random.uniform(-50, 50)
                    t8_value = 4100 + 150 * math.cos(elapsed * 1.5) + random.uniform(-50, 50)
                    
                    formatted_eeg = {
                        'timestamp': current_time,
                        'T7': t7_value,
                        'T8': t8_value,
                        'counter': int(elapsed * 128)  # 模拟128Hz采样率
                    }
                    
                    self.real_time_data['eeg'].append(formatted_eeg)
                    
                    # 生成模拟指标数据 - 与webtest.py格式完全一致
                    base_attention = 0.6 + 0.3 * math.sin(elapsed * 0.1)
                    base_stress = 0.4 + 0.2 * math.cos(elapsed * 0.15)
                    
                    formatted_metrics = {
                        'timestamp': current_time,
                        'attention_active': True,
                        'attention': max(0, min(1, base_attention + random.uniform(-0.1, 0.1))),
                        'stress_active': True,
                        'stress': max(0, min(1, base_stress + random.uniform(-0.1, 0.1)))
                    }
                    
                    self.real_time_data['metrics'].append(formatted_metrics)
                    
                    # 更新状态 - 与webtest.py格式完全一致
                    self.real_time_data['status'].update({
                        'attention': formatted_metrics['attention'],
                        'stress': formatted_metrics['stress'],
                        'eeg_count': len(self.real_time_data['eeg']),
                        'metrics_count': len(self.real_time_data['metrics']),
                        'duration': elapsed
                    })
                    
                    time.sleep(0.05)  # 20Hz更新频率
                    
                except Exception as e:
                    print(f"模拟数据生成错误: {e}")
                    time.sleep(0.5)
        
        self.monitoring_thread = threading.Thread(target=simulation_loop, daemon=True)
        self.monitoring_thread.start()

    def _start_monitoring_loop(self):
        """启动真实EEG数据监控循环 - 优先使用真实数据"""
        def monitoring_loop():
            print("📡 开始EEG数据处理线程...")
            real_data_available = False
            
            while self.app_running:
                try:
                    data_received = False
                    
                    # 优先尝试获取真实EEG数据
                    if (hasattr(self.eeg_system, 'data_queue') and 
                        self.eeg_system.data_queue and 
                        not self.eeg_system.data_queue.empty()):
                        
                        try:
                            eeg_data = self.eeg_system.data_queue.get_nowait()
                            real_data_available = True
                            data_received = True
                            
                            # 格式化真实EEG数据
                            if eeg_data and len(eeg_data) >= 4:
                                formatted_eeg = {
                                    'timestamp': time.time(),
                                    'T7': float(eeg_data[2]) if len(eeg_data) > 2 else 0.0,
                                    'T8': float(eeg_data[3]) if len(eeg_data) > 3 else 0.0,
                                    'counter': int(eeg_data[0]) if len(eeg_data) > 0 else 0
                                }
                                
                                self.real_time_data['eeg'].append(formatted_eeg)
                                print(f"📊 收到真实EEG数据: T7={formatted_eeg['T7']:.1f}, T8={formatted_eeg['T8']:.1f}")
                                
                        except (queue.Empty, IndexError, ValueError, TypeError) as e:
                            pass
                    
                    # 优先尝试获取真实指标数据
                    if (hasattr(self.eeg_system, 'metrics_queue') and 
                        self.eeg_system.metrics_queue and 
                        not self.eeg_system.metrics_queue.empty()):
                        
                        try:
                            metrics_data = self.eeg_system.metrics_queue.get_nowait()
                            real_data_available = True
                            data_received = True
                            
                            # 格式化真实指标数据
                            if metrics_data and len(metrics_data) >= 4:
                                formatted_metrics = {
                                    'timestamp': time.time(),
                                    'attention_active': bool(metrics_data[0]) if len(metrics_data) > 0 else False,
                                    'attention': float(metrics_data[1]) if len(metrics_data) > 1 else 0.0,
                                    'stress_active': bool(metrics_data[2]) if len(metrics_data) > 2 else False,
                                    'stress': float(metrics_data[3]) if len(metrics_data) > 3 else 0.0
                                }
                                
                                self.real_time_data['metrics'].append(formatted_metrics)
                                
                                # 更新状态
                                self.real_time_data['status'].update({
                                    'attention': formatted_metrics['attention'],
                                    'stress': formatted_metrics['stress'],
                                    'eeg_count': len(self.real_time_data['eeg']),
                                    'metrics_count': len(self.real_time_data['metrics']),
                                    'duration': time.time() - self.start_time if self.start_time else 0
                                })
                                
                                print(f"🎯 收到真实指标数据: 专注度={formatted_metrics['attention']:.3f}, 压力={formatted_metrics['stress']:.3f}")
                                
                        except (queue.Empty, IndexError, ValueError, TypeError):
                            pass
                    
                    # 如果没有收到真实数据，使用模拟数据补充
                    if not data_received and not real_data_available:
                        # 生成模拟数据
                        current_time = time.time()
                        elapsed = current_time - self.start_time if self.start_time else 0
                        
                        import random
                        import math
                        
                        # 模拟EEG数据
                        t7_value = 4000 + 200 * math.sin(elapsed * 2) + random.uniform(-50, 50)
                        t8_value = 4100 + 150 * math.cos(elapsed * 1.5) + random.uniform(-50, 50)
                        
                        formatted_eeg = {
                            'timestamp': current_time,
                            'T7': t7_value,
                            'T8': t8_value,
                            'counter': int(elapsed * 128)
                        }
                        
                        self.real_time_data['eeg'].append(formatted_eeg)
                        
                        # 模拟指标数据
                        base_attention = 0.6 + 0.3 * math.sin(elapsed * 0.1)
                        base_stress = 0.4 + 0.2 * math.cos(elapsed * 0.15)
                        
                        formatted_metrics = {
                            'timestamp': current_time,
                            'attention_active': True,
                            'attention': max(0, min(1, base_attention + random.uniform(-0.1, 0.1))),
                            'stress_active': True,
                            'stress': max(0, min(1, base_stress + random.uniform(-0.1, 0.1)))
                        }
                        
                        self.real_time_data['metrics'].append(formatted_metrics)
                        
                        # 更新状态
                        self.real_time_data['status'].update({
                            'attention': formatted_metrics['attention'],
                            'stress': formatted_metrics['stress'],
                            'eeg_count': len(self.real_time_data['eeg']),
                            'metrics_count': len(self.real_time_data['metrics']),
                            'duration': elapsed
                        })
                        
                        # 每10次模拟数据显示一次提示
                        if len(self.real_time_data['metrics']) % 10 == 0:
                            print(f"🎭 使用模拟数据 (#{len(self.real_time_data['metrics'])})")
                    
                    time.sleep(0.01)  # 10ms 延迟
                    
                except Exception as e:
                    print(f"EEG数据处理错误: {e}")
                    time.sleep(0.1)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_session(self):
        """停止会话"""
        try:
            self.app_running = False
            
            # 停止各个子系统
            if self.eeg_system:
                try:
                    self.eeg_system.stop_system()
                except Exception as e:
                    print(f"停止EEG系统警告: {e}")
            
            if self.focus_manager:
                try:
                    self.focus_manager.end_session()
                except Exception as e:
                    print(f"停止专注管理器警告: {e}")
            
            if self.music_engine:
                try:
                    self.music_engine.stop_playlist()
                except Exception as e:
                    print(f"停止音乐引擎警告: {e}")
            
            # 清理数据
            self.current_session_config = None
            self.start_time = None
            
            print("✅ 专注会话已结束")
            
            return {'success': True, 'message': '会话已停止'}
            
        except Exception as e:
            print(f"停止会话错误: {e}")
            return {'success': False, 'message': f'停止失败: {str(e)}'}
    
    def get_current_status(self):
        """获取当前状态 - 返回与webtest.py兼容的格式"""
        try:
            status_data = {
                'running': self.app_running,  # 改为running，与dashboard.html兼容
                'status': self.real_time_data['status'].copy(),
                'session_config': self.current_session_config,
                'clients_connected': len(self.clients)
            }
            return status_data
        except Exception as e:
            print(f"获取状态错误: {e}")
            return {
                'running': False,
                'status': {
                    'attention': 0,
                    'stress': 0,
                    'duration': 0,
                    'eeg_count': 0,
                    'metrics_count': 0
                },
                'session_config': None,
                'clients_connected': 0
            }

# 全局应用实例
focus_app = IntegratedFocusApp()

# Flask 路由
@app.route('/')
def dashboard():
    """主界面"""
    return render_template('focus_dashboard.html')

@app.route('/test')
def test_dashboard():
    """测试仪表板页面"""
    return render_template('test_dashboard.html')

@app.route('/setup')
def setup():
    """会话设置界面"""
    return render_template('session_setup.html')

@app.route('/api/status')
def get_status():
    """获取应用状态"""
    try:
        status = focus_app.get_current_status()
        safe_status = make_json_safe(status)
        return jsonify(safe_status)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """开始专注会话"""
    try:
        data = request.get_json() or {}
        min_duration = data.get('min_duration', 15)
        max_duration = data.get('max_duration', 20)
        enable_music = data.get('enable_music', True)
        enable_break_advisor = data.get('enable_break_advisor', True)
        enable_notifications = data.get('enable_notifications', True)
        enable_data_logging = data.get('enable_data_logging', False)
        enable_adaptive_breaks = data.get('enable_adaptive_breaks', False)
        
        result = focus_app.start_focus_session(
            min_duration, max_duration, enable_music, enable_break_advisor,
            enable_notifications, enable_data_logging, enable_adaptive_breaks
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'启动失败: {str(e)}'
        }), 500

@app.route('/api/stop_session', methods=['POST'])
def stop_session():
    """停止会话"""
    try:
        result = focus_app.stop_session()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'停止失败: {str(e)}'
        }), 500

@app.route('/api/pause_session', methods=['POST'])
def pause_session():
    """暂停会话"""
    try:
        # 简单的暂停实现
        if focus_app.app_running:
            focus_app.app_running = False
            return jsonify({
                'success': True,
                'message': '会话已暂停'
            })
        else:
            return jsonify({
                'success': False,
                'message': '没有正在运行的会话'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'暂停失败: {str(e)}'
        }), 500

@app.route('/api/resume_session', methods=['POST'])
def resume_session():
    """恢复会话"""
    try:
        # 简单的恢复实现
        if not focus_app.app_running and focus_app.current_session_config:
            focus_app.app_running = True
            return jsonify({
                'success': True,
                'message': '会话已恢复'
            })
        else:
            return jsonify({
                'success': False,
                'message': '无法恢复会话'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'恢复失败: {str(e)}'
        }), 500

@app.route('/api/take_break', methods=['POST'])
def take_break():
    """休息建议"""
    try:
        data = request.get_json() or {}
        duration = data.get('duration', 5)
        
        # 简单的休息实现
        return jsonify({
            'success': True,
            'message': f'休息 {duration} 分钟建议已记录'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'休息请求失败: {str(e)}'
        }), 500

@app.route('/api/start_music', methods=['POST'])
def start_music():
    """开始音乐播放"""
    try:
        if focus_app.music_engine:
            # 如果有音乐引擎，尝试启动
            try:
                focus_app.music_engine.start_playlist()
                return jsonify({
                    'success': True,
                    'message': '音乐播放已启动'
                })
            except Exception as music_error:
                return jsonify({
                    'success': False,
                    'message': f'音乐播放失败: {str(music_error)}'
                })
        else:
            return jsonify({
                'success': False,
                'message': '音乐引擎不可用'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'音乐启动失败: {str(e)}'
        }), 500

@app.route('/api/stop_music', methods=['POST'])
def stop_music():
    """停止音乐播放"""
    try:
        if focus_app.music_engine:
            try:
                focus_app.music_engine.stop_playlist()
                return jsonify({
                    'success': True,
                    'message': '音乐播放已停止'
                })
            except Exception as music_error:
                return jsonify({
                    'success': False,
                    'message': f'音乐停止失败: {str(music_error)}'
                })
        else:
            return jsonify({
                'success': True,
                'message': '音乐引擎不可用，无需停止'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'音乐停止失败: {str(e)}'
        }), 500

# 简化的API路由，兼容webtest.py格式
@app.route('/api/start')
def start_monitoring_api():
    """启动监控API - 兼容webtest.py格式"""
    try:
        success = focus_app.start_focus_session(15, 20, True, True)['success']
        return jsonify({
            'success': success,
            'message': 'Monitoring started successfully' if success else 'Failed to start monitoring'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error starting monitoring: {str(e)}'
        }), 500

@app.route('/api/stop')
def stop_monitoring_api():
    """停止监控API - 兼容webtest.py格式"""
    try:
        success = focus_app.stop_session()['success']
        return jsonify({
            'success': success,
            'message': 'Monitoring stopped successfully' if success else 'Failed to stop monitoring'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping monitoring: {str(e)}'
        }), 500

# WebSocket 事件 - 与webtest.py完全一致的格式
@socketio.on('connect')
def on_connect():
    """客户端连接事件"""
    try:
        # 获取客户端会话ID
        client_sid = request.sid
        focus_app.clients.add(client_sid)
        
        client_count = len(focus_app.clients)
        print(f"📱 客户端连接: {client_sid} (总计: {client_count})")
        
        # 发送当前状态 - 使用与webtest.py相同的格式
        emit('status_update', {
            'running': focus_app.app_running,
            'status': focus_app.real_time_data['status'].copy()
        })
        
    except Exception as e:
        print(f"客户端连接错误: {e}")

@socketio.on('disconnect')  
def on_disconnect():
    """客户端断开连接事件"""
    try:
        client_sid = request.sid
        focus_app.clients.discard(client_sid)
        
        client_count = len(focus_app.clients)
        print(f"📱 客户端断开: {client_sid} (总计: {client_count})")
        
    except Exception as e:
        print(f"客户端断开错误: {e}")

@socketio.on('ping')
def handle_ping():
    """处理客户端ping"""
    try:
        emit('pong', {'timestamp': time.time()})
    except Exception as e:
        print(f"Ping处理错误: {e}")

def make_json_safe(obj):
    """将对象转换为JSON安全格式"""
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, deque):
        return list(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'value'):  # 枚举类型
        return obj.value
    elif hasattr(obj, '__dataclass_fields__'):  # 数据类
        return {field.name: make_json_safe(getattr(obj, field.name)) 
                for field in obj.__dataclass_fields__.values()}
    elif hasattr(obj, '__dict__'):
        return make_json_safe(obj.__dict__)
    else:
        return obj

if __name__ == '__main__':
    print("🚀 启动智能专注力管理应用")
    print("📡 服务器地址:")
    print("   - 本地: http://localhost:8080")
    print("   - 设置: http://localhost:8080/setup")
    print("📋 按 Ctrl+C 停止服务器")
    
    try:
        # 使用更稳定的配置
        socketio.run(
            app,
            host='0.0.0.0',
            port=8080,
            debug=False,  # 关闭调试模式避免重复启动
            allow_unsafe_werkzeug=True,
            use_reloader=False  # 禁用自动重载避免重复启动
        )
    except KeyboardInterrupt:
        print("\n👋 用户中断，正在关闭...")
        focus_app.stop_session()
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
    finally:
        print("✅ 应用已停止")