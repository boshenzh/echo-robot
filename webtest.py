# 在文件顶部添加缺少的导入
import asyncio
import json
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request  # 添加 request
from flask_socketio import SocketIO, emit
import queue
from collections import deque

# 导入您现有的EEG系统
from eeg_monitor_system import EEGMonitorSystem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'eeg_monitor_secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class WebEEGMonitor:
    """Web版EEG监控器"""
    
    def __init__(self):
        self.eeg_system = EEGMonitorSystem()
        self.clients = set()
        self.running = False
        self.start_time = None
        
        # 实时数据缓存
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
        
    def start_monitoring(self):
        """启动监控"""
        if self.running:
            print("⚠️ 监控已经在运行中")
            return True
            
        try:
            print("🚀 尝试启动EEG监控...")
            if self.eeg_system.start_system():
                self.running = True
                self.start_time = time.time()
                
                # 启动数据处理线程
                data_thread = threading.Thread(target=self.data_processor, name="EEGDataProcessor")
                data_thread.daemon = True
                data_thread.start()
                
                print("✅ EEG监控启动成功")
                return True
            else:
                print("❌ EEG系统启动失败")
                return False
                
        except Exception as e:
            print(f"❌ 启动监控时出错: {e}")
            return False
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.running:
            print("⚠️ 监控未运行")
            return
            
        print("🛑 停止EEG监控...")
        self.running = False
        
        try:
            self.eeg_system.stop_system()
            print("✅ 监控已停止")
        except Exception as e:
            print(f"⚠️ 停止时出错: {e}")
    
    def data_processor(self):
        """处理EEG数据并准备发送到前端"""
        print("📡 开始数据处理线程...")
        
        while self.running:
            try:
                # 从EEG系统获取数据
                if hasattr(self.eeg_system, 'data_queue') and not self.eeg_system.data_queue.empty():
                    eeg_data = self.eeg_system.data_queue.get_nowait()
                    
                    # 格式化EEG数据
                    formatted_eeg = {
                        'timestamp': time.time(),
                        'T7': eeg_data[2] if len(eeg_data) > 2 else 0,
                        'T8': eeg_data[3] if len(eeg_data) > 3 else 0,
                        'counter': eeg_data[0] if len(eeg_data) > 0 else 0
                    }
                    
                    self.real_time_data['eeg'].append(formatted_eeg)
                    
                if hasattr(self.eeg_system, 'metrics_queue') and not self.eeg_system.metrics_queue.empty():
                    metrics_data = self.eeg_system.metrics_queue.get_nowait()
                    
                    # 格式化指标数据
                    formatted_metrics = {
                        'timestamp': time.time(),
                        'attention_active': metrics_data[0] if len(metrics_data) > 0 else False,
                        'attention': metrics_data[1] if len(metrics_data) > 1 else 0,
                        'stress_active': metrics_data[2] if len(metrics_data) > 2 else False,
                        'stress': metrics_data[3] if len(metrics_data) > 3 else 0
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
                
                time.sleep(0.01)  # 10ms 延迟
                
            except Exception as e:
                print(f"数据处理错误: {e}")
                time.sleep(0.1)

# 全局监控器实例
web_monitor = WebEEGMonitor()

# 广播数据线程
def broadcast_data():
    """向所有连接的客户端广播数据"""
    print("📡 启动数据广播线程...")
    
    while True:
        try:
            if web_monitor.running and web_monitor.clients:
                # 准备发送的数据
                broadcast_data = {
                    'type': 'realtime_update',
                    'eeg_data': list(web_monitor.real_time_data['eeg'])[-50:],  # 最近50个点
                    'metrics_data': list(web_monitor.real_time_data['metrics'])[-20:],  # 最近20个点
                    'status': web_monitor.real_time_data['status'],
                    'timestamp': time.time()
                }
                
                # 发送到所有客户端
                socketio.emit('data_update', broadcast_data)
            
            time.sleep(0.1)  # 每100ms发送一次
            
        except Exception as e:
            print(f"广播错误: {e}")
            time.sleep(1)

# 启动广播线程
broadcast_thread = threading.Thread(target=broadcast_data, name="DataBroadcaster")
broadcast_thread.daemon = True
broadcast_thread.start()

# Flask路由
@app.route('/')
def dashboard():
    """主仪表板页面"""
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """获取当前状态"""
    return jsonify({
        'running': web_monitor.running,
        'status': web_monitor.real_time_data['status']
    })

@app.route('/api/start')
def start_monitoring_api():
    """启动监控API"""
    try:
        success = web_monitor.start_monitoring()
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
    """停止监控API"""
    try:
        web_monitor.stop_monitoring()
        return jsonify({
            'success': True,
            'message': 'Monitoring stopped successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error stopping monitoring: {str(e)}'
        }), 500

# WebSocket事件处理
@socketio.on('connect')
def on_connect():
    """客户端连接事件"""
    try:
        # 获取客户端会话ID
        client_sid = request.sid
        web_monitor.clients.add(client_sid)
        
        client_count = len(web_monitor.clients)
        print(f"📱 客户端连接: {client_sid} (总计: {client_count})")
        
        # 发送当前状态
        emit('status_update', {
            'running': web_monitor.running,
            'status': web_monitor.real_time_data['status']
        })
        
    except Exception as e:
        print(f"客户端连接错误: {e}")

@socketio.on('disconnect')
def on_disconnect():
    """客户端断开连接事件"""
    try:
        client_sid = request.sid
        web_monitor.clients.discard(client_sid)
        
        client_count = len(web_monitor.clients)
        print(f"📱 客户端断开: {client_sid} (总计: {client_count})")
        
    except Exception as e:
        print(f"客户端断开错误: {e}")

@socketio.on('ping')
def handle_ping():
    """处理客户端ping"""
    emit('pong')

if __name__ == '__main__':
    print("🚀 启动EEG Web监控服务器...")
    print("📡 服务器地址:")
    print("   - 本地: http://localhost:8080")
    print("   - 网络: http://30.201.218.167:8080")
    print("📋 按 Ctrl+C 停止服务器")
    print("⚠️ 注意: 启动监控前请确保EMOTIV设备已连接")
    
    try:
        # 使用更稳定的配置
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=8080, 
            debug=False,  # 关闭调试模式避免重复启动
            use_reloader=False  # 禁用自动重载
        )
    except KeyboardInterrupt:
        print("\n👋 用户中断，停止服务器...")
        web_monitor.stop_monitoring()
    except Exception as e:
        print(f"❌ 服务器错误: {e}")
    finally:
        print("✅ 服务器已停止")