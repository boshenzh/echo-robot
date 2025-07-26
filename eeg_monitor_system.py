import websocket
import json
import ssl
import time
import csv
import threading
import queue
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端
import matplotlib.pyplot as plt
from collections import deque
import numpy as np
import pandas as pd

# 修复字体问题 - 只使用系统默认字体
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# Cortex API 配置
cortex_url = "wss://localhost:6868"
client_id = "5PQNigMKSEFMObbxlKLIWZycuBE3VzWknPUzDaWt"
client_secret = "GOlCkjxftNGLbdkTDOeIEsSdC2niQl0MEjgJYIQRDQelI011EanfEfMsYJh9bu4NuYIrPa9ZV7gbeFEUCyahuSGJMT251ZD4PQ7gDS7uLzRQcCGOzBhifVWwA630sk2R"

class DataManager:
    """Data Manager - handles data saving and management"""
    
    def __init__(self, base_filename="eeg_session"):
        self.base_filename = base_filename
        self.session_start_time = datetime.now()
        self.session_id = self.session_start_time.strftime("%Y%m%d_%H%M%S")
        
        # Create data files
        self.eeg_file = f"{base_filename}_eeg_{self.session_id}.csv"
        self.metrics_file = f"{base_filename}_metrics_{self.session_id}.csv"
        self.summary_file = f"{base_filename}_summary_{self.session_id}.json"
        
        # Initialize CSV files
        self.init_csv_files()
        print(f"📁 Data files created:")
        print(f"   EEG data: {self.eeg_file}")
        print(f"   Metrics data: {self.metrics_file}")
        
    def init_csv_files(self):
        """Initialize CSV files"""
        # EEG data file header
        with open(self.eeg_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'counter', 'interpolated', 'T7', 'T8', 'raw_cq', 'marker_hardware', 'markers'])
        
        # Metrics file header
        with open(self.metrics_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'attention_active', 'attention', 'stress_active', 'cognitive_stress'])
    
    def save_eeg_data(self, eeg_data):
        """Save EEG data"""
        timestamp = datetime.now().isoformat()
        with open(self.eeg_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp] + eeg_data)
    
    def save_metrics_data(self, metrics_data):
        """Save metrics data"""
        timestamp = datetime.now().isoformat()
        with open(self.metrics_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp] + metrics_data)
    
    def save_session_summary(self, summary_data):
        """Save session summary"""
        with open(self.summary_file, 'w') as f:
            json.dump(summary_data, f, indent=4, default=str)

class OfflineVisualizer:
    """Offline Visualizer - creates periodic plot snapshots"""
    
    def __init__(self, data_queue, metrics_queue):
        self.data_queue = data_queue
        self.metrics_queue = metrics_queue
        
        # Data buffers
        self.eeg_buffer_size = 1000
        self.metrics_buffer_size = 200
        
        self.time_buffer = deque(maxlen=self.eeg_buffer_size)
        self.t7_buffer = deque(maxlen=self.eeg_buffer_size)
        self.t8_buffer = deque(maxlen=self.eeg_buffer_size)
        
        self.metrics_time_buffer = deque(maxlen=self.metrics_buffer_size)
        self.attention_buffer = deque(maxlen=self.metrics_buffer_size)
        self.stress_buffer = deque(maxlen=self.metrics_buffer_size)
        
        self.plot_counter = 0
        
    def update_data(self):
        """Update data buffers"""
        # Process EEG data
        while not self.data_queue.empty():
            try:
                eeg_data = self.data_queue.get_nowait()
                current_time = time.time()
                
                self.time_buffer.append(current_time)
                self.t7_buffer.append(eeg_data[2])  # T7 electrode
                self.t8_buffer.append(eeg_data[3])  # T8 electrode
                
            except queue.Empty:
                break
        
        # Process metrics data
        while not self.metrics_queue.empty():
            try:
                metrics_data = self.metrics_queue.get_nowait()
                current_time = time.time()
                
                self.metrics_time_buffer.append(current_time)
                self.attention_buffer.append(metrics_data[1])  # Attention
                self.stress_buffer.append(metrics_data[3])     # Cognitive stress
                
            except queue.Empty:
                break
    
    def create_plot_snapshot(self):
        """Create and save plot snapshot"""
        if len(self.time_buffer) < 10:
            return
            
        self.plot_counter += 1
        
        # Create figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'EEG Monitoring System - Snapshot {self.plot_counter}', fontsize=16)
        
        # EEG waveforms
        if len(self.time_buffer) > 1:
            time_array = np.array(self.time_buffer)
            rel_time = time_array - time_array[0]
            
            ax1.plot(rel_time, list(self.t7_buffer), 'b-', label='T7', linewidth=1)
            ax1.set_title('T7 Electrode Waveform')
            ax1.set_ylabel('Voltage (μV)')
            ax1.set_xlabel('Time (s)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            ax2.plot(rel_time, list(self.t8_buffer), 'r-', label='T8', linewidth=1)
            ax2.set_title('T8 Electrode Waveform')
            ax2.set_ylabel('Voltage (μV)')
            ax2.set_xlabel('Time (s)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # Metrics
        if len(self.metrics_time_buffer) > 1:
            time_array = np.array(self.metrics_time_buffer)
            rel_time = (time_array - time_array[0]) / 60  # Convert to minutes
            
            ax3.plot(rel_time, list(self.attention_buffer), 'g-', linewidth=2, label='Attention')
            ax3.set_title('Attention Level Trend')
            ax3.set_ylabel('Attention Level')
            ax3.set_xlabel('Time (min)')
            ax3.set_ylim(0, 1)
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            ax4.plot(rel_time, list(self.stress_buffer), 'orange', linewidth=2, label='Cognitive Stress')
            ax4.set_title('Cognitive Stress Monitoring')
            ax4.set_ylabel('Stress Level')
            ax4.set_xlabel('Time (min)')
            ax4.set_ylim(0, 1)
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        filename = f'eeg_snapshot_{self.plot_counter:03d}.png'
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        plt.close()
        print(f"📊 Plot snapshot saved: {filename}")

class ConsoleStatusMonitor:
    """Console Status Monitor - displays real-time status in console"""
    
    def __init__(self):
        self.current_attention = 0
        self.current_stress = 0
        self.session_duration = 0
        self.data_count = 0
        self.last_update = time.time()
        self.eeg_count = 0
        self.metrics_count = 0
        
    def update_status(self, attention=None, stress=None, duration=None, eeg_count=None, metrics_count=None):
        """Update status display"""
        if attention is not None:
            self.current_attention = attention
            
        if stress is not None:
            self.current_stress = stress
            
        if duration is not None:
            self.session_duration = duration
            
        if eeg_count is not None:
            self.eeg_count = eeg_count
            
        if metrics_count is not None:
            self.metrics_count = metrics_count
        
        # Update display every 3 seconds
        current_time = time.time()
        if current_time - self.last_update > 3:
            self.print_status()
            self.last_update = current_time
        
    def print_status(self):
        """Print status to console"""
        # Clear screen effect
        print("\n" + "="*70)
        print("🧠 EEG Monitoring System - Real-time Status")
        print("="*70)
        
        # Session duration
        hours = int(self.session_duration // 3600)
        minutes = int((self.session_duration % 3600) // 60)
        seconds = int(self.session_duration % 60)
        print(f"⏱️  Session Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Data statistics
        print(f"📊 EEG Packets: {self.eeg_count}")
        print(f"📈 Metrics Packets: {self.metrics_count}")
        print(f"📦 Total Packets: {self.eeg_count + self.metrics_count}")
        
        # Attention level
        attention_percent = self.current_attention * 100
        attention_bar = "█" * int(attention_percent / 5) + "░" * (20 - int(attention_percent / 5))
        print(f"🎯 Attention Level: [{attention_bar}] {attention_percent:.1f}%")
        
        # Cognitive stress
        stress_percent = self.current_stress * 100
        stress_bar = "█" * int(stress_percent / 5) + "░" * (20 - int(stress_percent / 5))
        print(f"⚡ Cognitive Stress: [{stress_bar}] {stress_percent:.1f}%")
        
        # Focus status
        if self.current_attention > 0.7:
            status = "Highly Focused 🟢"
        elif self.current_attention > 0.4:
            status = "Moderately Focused 🟡"
        else:
            status = "Distracted 🔴"
        
        print(f"🎪 Current Status: {status}")
        
        # Data rate
        if self.session_duration > 0:
            eeg_rate = self.eeg_count / self.session_duration
            metrics_rate = self.metrics_count / self.session_duration
            print(f"📊 Data Rate: EEG {eeg_rate:.1f} Hz, Metrics {metrics_rate:.2f} Hz")
        
        print("="*70)

class CortexDataCollector:
    """Cortex Data Collector"""
    
    def __init__(self, url, client_id, client_secret):
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.ws = None
        self.token = None
        self.running = False
        
    def connect(self):
        """Establish WebSocket connection"""
        try:
            self.ws = websocket.create_connection(self.url, sslopt={"cert_reqs": ssl.CERT_NONE})
            print("✅ Connected to Cortex API")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def send_request(self, method, params={}):
        """Send request"""
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        self.ws.send(json.dumps(request))
        response = self.ws.recv()
        return json.loads(response)

    def setup_session(self):
        """Setup session (includes all initialization steps)"""
        # Get user login
        response = self.send_request("getUserLogin")
        if not ('result' in response):
            return False
        print("✅ User logged in")
        
        # Request access
        response = self.send_request("requestAccess", {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        })
        if not ('result' in response and response['result']['accessGranted']):
            return False
        print("✅ Access granted")
        
        # Authorize
        response = self.send_request("authorize", {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        })
        if not ('result' in response and 'cortexToken' in response['result']):
            return False
        self.token = response['result']['cortexToken']
        print("✅ Authorization successful")
        
        # Query headsets
        response = self.send_request("queryHeadsets")
        headset_id = None
        if 'result' in response and response['result']:
            for headset in response['result']:
                if headset['status'] == 'connected':
                    headset_id = headset['id']
                    break
        if not headset_id:
            return False
        print(f"✅ Device found: {headset_id}")
        
        # Create session
        response = self.send_request("createSession", {
            "cortexToken": self.token,
            "headset": headset_id,
            "status": "active"
        })
        if not ('result' in response):
            return False
        session_id = response['result']['id']
        print(f"✅ Session created: {session_id}")
        
        # Subscribe to data streams
        response = self.send_request("subscribe", {
            "cortexToken": self.token,
            "session": session_id,
            "streams": ["eeg", "met"]
        })
        if not ('result' in response):
            return False
        print("✅ Data stream subscription successful")
        
        return True
    
    def start_data_collection(self, data_queue, metrics_queue, data_manager, status_monitor, visualizer):
        """Start data collection"""
        self.running = True
        eeg_count = 0
        metrics_count = 0
        start_time = time.time()
        last_plot_time = time.time()
        
        print("🚀 Starting data collection...")
        print("📋 Press Ctrl+C to stop monitoring")
        
        while self.running:
            try:
                self.ws.settimeout(1.0)
                message = self.ws.recv()
                data = json.loads(message)
                
                current_time = time.time()
                duration = current_time - start_time
                
                if 'eeg' in data:
                    eeg_count += 1
                    data_queue.put(data['eeg'])
                    data_manager.save_eeg_data(data['eeg'])
                    
                elif 'met' in data:
                    metrics_count += 1
                    metrics_queue.put(data['met'])
                    data_manager.save_metrics_data(data['met'])
                    
                    # Update status monitor
                    if len(data['met']) >= 4:
                        status_monitor.update_status(
                            attention=data['met'][1],
                            stress=data['met'][3],
                            duration=duration,
                            eeg_count=eeg_count,
                            metrics_count=metrics_count
                        )
                
                # Update visualizer and create periodic snapshots
                visualizer.update_data()
                if current_time - last_plot_time > 30:  # Create snapshot every 30 seconds
                    visualizer.create_plot_snapshot()
                    last_plot_time = current_time
                
            except websocket.WebSocketTimeoutException:
                continue
            except websocket.WebSocketConnectionClosedException:
                print("❌ Connection closed")
                break
            except Exception as e:
                print(f"❌ Data processing error: {e}")
                continue
    
    def stop_collection(self):
        """Stop data collection"""
        self.running = False
        if self.ws:
            self.ws.close()

class EEGMonitorSystem:
    """Main system class - coordinates all components"""
    
    def __init__(self):
        # Initialize components
        self.data_queue = queue.Queue()
        self.metrics_queue = queue.Queue()
        self.data_manager = DataManager()
        self.collector = CortexDataCollector(cortex_url, client_id, client_secret)
        self.visualizer = OfflineVisualizer(self.data_queue, self.metrics_queue)
        self.status_monitor = ConsoleStatusMonitor()
        
        # Thread management
        self.threads = []
        self.running = False
        
    def start_system(self):
        """Start the entire system"""
        print("🚀 Starting EEG monitoring system...")
        
        # Connect and setup session
        if not self.collector.connect():
            print("❌ Unable to connect to Cortex API")
            return False
            
        if not self.collector.setup_session():
            print("❌ Session setup failed")
            return False
        
        print("✅ System initialization complete")
        
        self.running = True
        
        # Start data collection thread
        data_thread = threading.Thread(
            target=self.collector.start_data_collection,
            args=(self.data_queue, self.metrics_queue, self.data_manager, self.status_monitor, self.visualizer)
        )
        data_thread.daemon = True
        data_thread.start()
        self.threads.append(data_thread)
        
        print("🖥️ System running... (Plot snapshots will be saved periodically)")
        return True
    
    def run_forever(self):
        """Keep system running"""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 User interrupted")
            self.stop_system()
    
    def stop_system(self):
        """Stop system"""
        print("🛑 Stopping system...")
        self.running = False
        self.collector.stop_collection()
        
        # Create final plot
        self.visualizer.create_plot_snapshot()
        
        # Save session summary
        summary = {
            "session_id": self.data_manager.session_id,
            "start_time": self.data_manager.session_start_time,
            "end_time": datetime.now(),
            "duration_seconds": (datetime.now() - self.data_manager.session_start_time).total_seconds(),
            "files_created": {
                "eeg_data": self.data_manager.eeg_file,
                "metrics_data": self.data_manager.metrics_file,
                "summary": self.data_manager.summary_file
            }
        }
        self.data_manager.save_session_summary(summary)
        print("✅ Session data saved")

# --- Main program entry ---
if __name__ == "__main__":
    print("🧠 EEG Monitoring System Starting...")
    
    # Check dependencies
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        print("✅ Dependencies check passed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install matplotlib numpy pandas")
        exit(1)
    
    # Start system
    system = EEGMonitorSystem()
    
    try:
        if system.start_system():
            print("🎉 System running...")
            system.run_forever()
        else:
            print("❌ System startup failed")
    except KeyboardInterrupt:
        print("\n👋 User interrupted")
    finally:
        system.stop_system()
        print("✅ System stopped")