import websocket
import json
import ssl
import time
from datetime import datetime
from collections import defaultdict, deque
import threading

# Cortex API配置
cortex_url = "wss://localhost:6868"
client_id = "5PQNigMKSEFMObbxlKLIWZycuBE3VzWknPUzDaWt"
client_secret = "GOlCkjxftNGLbdkTDOeIEsSdC2niQl0MEjgJYIQRDQelI011EanfEfMsYJh9bu4NuYIrPa9ZV7gbeFEUCyahuSGJMT251ZD4PQ7gDS7uLzRQcCGOzBhifVWwA630sk2R"

class EMOTIVDataAnalyzer:
    """EMOTIV设备数据分析器 - 全面分析所有可用数据"""
    
    def __init__(self, url, client_id, client_secret):
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.ws = None
        self.token = None
        
        # 数据统计
        self.data_stats = defaultdict(int)
        self.data_samples = defaultdict(list)
        self.channel_info = {}
        self.metric_info = {}
        self.device_info = {}
        
        # 实时数据缓存
        self.eeg_channels = []
        self.motion_channels = []
        self.performance_metrics = []
        self.facial_expressions = []
        self.mental_commands = []
        
        # 分析结果
        self.analysis_results = {}
        
    def connect(self):
        """建立连接"""
        try:
            self.ws = websocket.create_connection(self.url, sslopt={"cert_reqs": ssl.CERT_NONE})
            print("✅ 连接到 Cortex API 成功")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def send_request(self, method, params={}):
        """发送请求"""
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        self.ws.send(json.dumps(request))
        response = self.ws.recv()
        return json.loads(response)
    
    def get_device_capabilities(self):
        """获取设备能力信息"""
        print("\n🔍 分析设备能力...")
        
        try:
            # 1. 获取Cortex信息
            cortex_info = self.send_request("getCortexInfo")
            if 'result' in cortex_info:
                print(f"📋 Cortex版本: {cortex_info['result']['version']}")
                self.device_info['cortex_version'] = cortex_info['result']['version']
        
            # 2. 查询许可信息
            license_info = self.send_request("getLicenseInfo", {
                "clientId": self.client_id
            })
            if 'result' in license_info:
                print(f"📜 许可信息: {license_info['result']}")
                self.device_info['license'] = license_info['result']
            
            # 3. 查询设备详细信息
            headsets = self.send_request("queryHeadsets")
            if 'result' in headsets and headsets['result']:
                for headset in headsets['result']:
                    if headset['status'] == 'connected':
                        print(f"🎧 设备详情:")
                        print(f"   ID: {headset['id']}")
                        print(f"   状态: {headset['status']}")
                        print(f"   连接类型: {headset.get('connectedBy', 'Unknown')}")
                        print(f"   固件版本: {headset.get('firmware', 'Unknown')}")
                        print(f"   设置: {headset.get('settings', {})}")
                        self.device_info['headset'] = headset
                        return headset['id']
            
            return None
            
        except Exception as e:
            print(f"❌ 获取设备信息失败: {e}")
            return None
    
    def analyze_available_streams(self):
        """分析可用的数据流"""
        print("\n📊 分析可用数据流...")
        
        # 所有可能的数据流类型
        possible_streams = [
            "eeg", "met", "mot", "dev", "pow", "fac", "com", "sys"
        ]
        
        available_streams = []
        
        for stream in possible_streams:
            try:
                # 尝试获取流信息
                if stream == "eeg":
                    # EEG通道信息
                    response = self.send_request("queryHeadsets")
                    if 'result' in response and response['result']:
                        headset = response['result'][0]
                        if 'channels' in headset:
                            self.eeg_channels = headset['channels']
                            available_streams.append(stream)
                            print(f"✅ EEG数据流可用 - 通道: {self.eeg_channels}")
                
                elif stream == "met":
                    # 性能指标信息
                    available_streams.append(stream)
                    print(f"✅ 性能指标数据流可用")
                
                elif stream == "mot":
                    # 运动数据
                    available_streams.append(stream)
                    print(f"✅ 运动数据流可用")
                
                elif stream == "pow":
                    # 频段功率
                    available_streams.append(stream)
                    print(f"✅ 频段功率数据流可用")
                
                elif stream == "fac":
                    # 面部表情
                    available_streams.append(stream)
                    print(f"✅ 面部表情数据流可用")
                
                elif stream == "com":
                    # 心理指令
                    available_streams.append(stream)
                    print(f"✅ 心理指令数据流可用")
                    
            except Exception as e:
                print(f"⚠️ {stream} 数据流不可用: {e}")
        
        return available_streams
    
    def get_detection_info(self):
        """获取检测能力信息"""
        print("\n🧠 分析检测能力...")
        
        detection_types = [
            "mentalCommand", "facialExpression", "performanceMetric"
        ]
        
        for detection in detection_types:
            try:
                response = self.send_request("getDetectionInfo", {
                    "detection": detection
                })
                
                if 'result' in response:
                    print(f"\n📈 {detection} 检测能力:")
                    result = response['result']
                    
                    if 'actions' in result:
                        print(f"   可用动作: {result['actions']}")
                        if detection == "mentalCommand":
                            self.mental_commands = result['actions']
                        elif detection == "facialExpression":
                            self.facial_expressions = result['actions']
                    
                    if 'controls' in result:
                        print(f"   控制选项: {result['controls']}")
                    
                    if 'events' in result:
                        print(f"   事件类型: {result['events']}")
                    
                    self.analysis_results[detection] = result
                
            except Exception as e:
                print(f"⚠️ 无法获取 {detection} 信息: {e}")
    
    def setup_comprehensive_session(self, headset_id):
        """建立全面的数据收集会话"""
        print("\n🚀 建立全面数据收集会话...")
        
        try:
            # 用户登录检查
            user_login = self.send_request("getUserLogin")
            if 'result' not in user_login:
                print("❌ 用户未登录")
                return None
            print("✅ 用户已登录")
            
            # 请求访问权限
            access_response = self.send_request("requestAccess", {
                "clientId": self.client_id,
                "clientSecret": self.client_secret
            })
            if not ('result' in access_response and access_response['result']['accessGranted']):
                print("❌ 访问权限被拒绝")
                return None
            print("✅ 访问权限获得")
            
            # 授权
            auth_response = self.send_request("authorize", {
                "clientId": self.client_id,
                "clientSecret": self.client_secret
            })
            if not ('result' in auth_response and 'cortexToken' in auth_response['result']):
                print("❌ 授权失败")
                return None
            
            self.token = auth_response['result']['cortexToken']
            print("✅ 授权成功")
            
            # 创建会话
            session_response = self.send_request("createSession", {
                "cortexToken": self.token,
                "headset": headset_id,
                "status": "active"
            })
            
            if 'result' not in session_response:
                print("❌ 会话创建失败")
                return None
            
            session_id = session_response['result']['id']
            print(f"✅ 会话创建成功: {session_id}")
            
            return session_id
            
        except Exception as e:
            print(f"❌ 会话建立失败: {e}")
            return None
    
    def subscribe_all_streams(self, session_id):
        """订阅所有可用的数据流"""
        print("\n📡 订阅所有可用数据流...")
        
        # 尝试订阅所有可能的数据流
        all_streams = ["eeg", "met", "mot", "pow", "fac", "com", "dev", "sys"]
        successful_streams = []
        
        for stream in all_streams:
            try:
                response = self.send_request("subscribe", {
                    "cortexToken": self.token,
                    "session": session_id,
                    "streams": [stream]
                })
                
                if 'result' in response:
                    successful_streams.append(stream)
                    print(f"✅ {stream} 数据流订阅成功")
                    
                    # 记录订阅详情
                    if 'cols' in response['result']:
                        if stream == "eeg":
                            self.eeg_channels = response['result']['cols']
                        elif stream == "met":
                            self.performance_metrics = response['result']['cols']
                        print(f"   数据列: {response['result']['cols']}")
                else:
                    print(f"⚠️ {stream} 数据流订阅失败")
                    
            except Exception as e:
                print(f"⚠️ {stream} 数据流订阅出错: {e}")
        
        return successful_streams
    
    def comprehensive_data_analysis(self, duration=60):
        """全面数据分析"""
        print(f"\n🔬 开始全面数据分析 (持续 {duration} 秒)")
        print("="*80)
        
        start_time = time.time()
        analysis_data = {
            'eeg': {'count': 0, 'samples': deque(maxlen=100), 'channels': {}},
            'met': {'count': 0, 'samples': deque(maxlen=50), 'metrics': {}},
            'mot': {'count': 0, 'samples': deque(maxlen=50)},
            'pow': {'count': 0, 'samples': deque(maxlen=50)},
            'fac': {'count': 0, 'samples': deque(maxlen=50)},
            'com': {'count': 0, 'samples': deque(maxlen=50)},
            'dev': {'count': 0, 'samples': deque(maxlen=50)},
            'sys': {'count': 0, 'samples': deque(maxlen=20)},
            'other': {'count': 0, 'samples': deque(maxlen=20)}
        }
        
        last_report_time = start_time
        
        try:
            while time.time() - start_time < duration:
                try:
                    self.ws.settimeout(2.0)
                    message = self.ws.recv()
                    data = json.loads(message)
                    
                    # 分析不同类型的数据
                    data_type = None
                    
                    if 'eeg' in data:
                        data_type = 'eeg'
                        eeg_data = data['eeg']
                        analysis_data['eeg']['count'] += 1
                        analysis_data['eeg']['samples'].append(eeg_data)
                        
                        # 分析EEG通道数据
                        for i, channel in enumerate(self.eeg_channels):
                            if i < len(eeg_data):
                                if channel not in analysis_data['eeg']['channels']:
                                    analysis_data['eeg']['channels'][channel] = {
                                        'values': deque(maxlen=100),
                                        'min': float('inf'),
                                        'max': float('-inf'),
                                        'avg': 0
                                    }
                                
                                value = eeg_data[i]
                                channel_data = analysis_data['eeg']['channels'][channel]
                                channel_data['values'].append(value)
                                channel_data['min'] = min(channel_data['min'], value)
                                channel_data['max'] = max(channel_data['max'], value)
                                channel_data['avg'] = sum(channel_data['values']) / len(channel_data['values'])
                    
                    elif 'met' in data:
                        data_type = 'met'
                        met_data = data['met']
                        analysis_data['met']['count'] += 1
                        analysis_data['met']['samples'].append(met_data)
                        
                        # 分析性能指标
                        for i, metric in enumerate(self.performance_metrics):
                            if i < len(met_data):
                                if metric not in analysis_data['met']['metrics']:
                                    analysis_data['met']['metrics'][metric] = {
                                        'values': deque(maxlen=50),
                                        'active_count': 0,
                                        'avg_value': 0
                                    }
                                
                                value = met_data[i]
                                metric_data = analysis_data['met']['metrics'][metric]
                                metric_data['values'].append(value)
                                
                                if '.isActive' in metric:
                                    if value:
                                        metric_data['active_count'] += 1
                                else:
                                    if len(metric_data['values']) > 0:
                                        metric_data['avg_value'] = sum(metric_data['values']) / len(metric_data['values'])
                    
                    elif 'mot' in data:
                        data_type = 'mot'
                        analysis_data['mot']['count'] += 1
                        analysis_data['mot']['samples'].append(data['mot'])
                    
                    elif 'pow' in data:
                        data_type = 'pow'
                        analysis_data['pow']['count'] += 1
                        analysis_data['pow']['samples'].append(data['pow'])
                    
                    elif 'fac' in data:
                        data_type = 'fac'
                        analysis_data['fac']['count'] += 1
                        analysis_data['fac']['samples'].append(data['fac'])
                    
                    elif 'com' in data:
                        data_type = 'com'
                        analysis_data['com']['count'] += 1
                        analysis_data['com']['samples'].append(data['com'])
                    
                    elif 'dev' in data:
                        data_type = 'dev'
                        analysis_data['dev']['count'] += 1
                        analysis_data['dev']['samples'].append(data['dev'])
                    
                    elif 'sys' in data:
                        data_type = 'sys'
                        analysis_data['sys']['count'] += 1
                        analysis_data['sys']['samples'].append(data['sys'])
                    
                    else:
                        data_type = 'other'
                        analysis_data['other']['count'] += 1
                        analysis_data['other']['samples'].append(data)
                    
                    # 每10秒输出一次进度报告
                    current_time = time.time()
                    if current_time - last_report_time >= 10:
                        self.print_progress_report(analysis_data, current_time - start_time)
                        last_report_time = current_time
                
                except websocket.WebSocketTimeoutException:
                    print(".", end="", flush=True)
                    continue
                except websocket.WebSocketConnectionClosedException:
                    print("\n❌ 连接已关闭")
                    break
                except KeyboardInterrupt:
                    print("\n👋 用户中断分析")
                    break
                except Exception as e:
                    print(f"\n⚠️ 数据处理错误: {e}")
                    continue
        
        finally:
            # 输出最终分析结果
            self.print_final_analysis(analysis_data, time.time() - start_time)
    
    def print_progress_report(self, data, elapsed_time):
        """打印进度报告"""
        print(f"\n⏱️ 进度报告 ({elapsed_time:.1f}s):")
        for data_type, info in data.items():
            if info['count'] > 0:
                rate = info['count'] / elapsed_time
                print(f"   {data_type.upper()}: {info['count']} 包 ({rate:.1f} Hz)")
    
    def print_final_analysis(self, data, total_time):
        """打印最终分析结果"""
        print("\n" + "="*80)
        print("🎯 EMOTIV设备数据分析完整报告")
        print("="*80)
        
        print(f"📊 分析时长: {total_time:.1f} 秒")
        print(f"🎧 设备型号: {self.device_info.get('headset', {}).get('id', 'Unknown')}")
        print(f"📋 Cortex版本: {self.device_info.get('cortex_version', 'Unknown')}")
        
        print("\n📈 数据流统计:")
        total_packets = 0
        for data_type, info in data.items():
            if info['count'] > 0:
                rate = info['count'] / total_time
                total_packets += info['count']
                print(f"   {data_type.upper():8}: {info['count']:6} 包 ({rate:6.1f} Hz)")
        
        print(f"   {'TOTAL':8}: {total_packets:6} 包")
        
        # EEG通道分析
        if data['eeg']['count'] > 0:
            print(f"\n🧠 EEG通道分析 ({len(self.eeg_channels)} 通道):")
            for channel, channel_data in data['eeg']['channels'].items():
                if len(channel_data['values']) > 0:
                    print(f"   {channel:12}: 范围 [{channel_data['min']:8.2f}, {channel_data['max']:8.2f}], "
                          f"平均 {channel_data['avg']:8.2f}")
        
        # 性能指标分析
        if data['met']['count'] > 0:
            print(f"\n🎯 性能指标分析 ({len(self.performance_metrics)} 指标):")
            for metric, metric_data in data['met']['metrics'].items():
                if '.isActive' in metric:
                    activation_rate = (metric_data['active_count'] / data['met']['count']) * 100
                    print(f"   {metric:20}: 激活率 {activation_rate:5.1f}%")
                else:
                    if len(metric_data['values']) > 0:
                        print(f"   {metric:20}: 平均值 {metric_data['avg_value']:6.3f}")
        
        # 其他数据流样本
        for data_type in ['mot', 'pow', 'fac', 'com', 'dev']:
            if data[data_type]['count'] > 0:
                print(f"\n📊 {data_type.upper()} 数据样本:")
                samples = list(data[data_type]['samples'])[:3]  # 显示前3个样本
                for i, sample in enumerate(samples):
                    print(f"   样本 {i+1}: {sample}")
        
        # 建议和总结
        print(f"\n💡 分析建议:")
        if data['eeg']['count'] > 100:
            print("   ✅ EEG数据收集良好，适合进行脑电分析")
        else:
            print("   ⚠️ EEG数据量较少，建议延长采集时间")
        
        if data['met']['count'] > 10:
            print("   ✅ 性能指标数据充足，可进行认知状态分析")
        else:
            print("   ⚠️ 性能指标数据不足")
        
        available_streams = [k for k, v in data.items() if v['count'] > 0]
        print(f"   📡 可用数据流: {', '.join(available_streams)}")
        
        print("\n🎉 分析完成！")
    
    def save_analysis_report(self):
        """保存分析报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"emotiv_analysis_report_{timestamp}.json"
        
        report = {
            "timestamp": timestamp,
            "device_info": self.device_info,
            "eeg_channels": self.eeg_channels,
            "performance_metrics": self.performance_metrics,
            "mental_commands": self.mental_commands,
            "facial_expressions": self.facial_expressions,
            "analysis_results": self.analysis_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 分析报告已保存: {filename}")
    
    def close(self):
        """关闭连接"""
        if self.ws:
            self.ws.close()
            print("🔌 连接已关闭")

# --- 主程序 ---
if __name__ == "__main__":
    print("🚀 EMOTIV Cortex API 全面数据分析器")
    print("📋 目标: 全面分析设备支持的所有数据和功能")
    print("="*80)
    
    analyzer = EMOTIVDataAnalyzer(cortex_url, client_id, client_secret)
    
    try:
        # 1. 建立连接
        if analyzer.connect():
            
            # 2. 获取设备能力信息
            headset_id = analyzer.get_device_capabilities()
            
            if headset_id:
                # 3. 分析可用数据流
                available_streams = analyzer.analyze_available_streams()
                
                # 4. 获取检测能力信息
                analyzer.get_detection_info()
                
                # 5. 建立会话
                session_id = analyzer.setup_comprehensive_session(headset_id)
                
                if session_id:
                    # 6. 订阅所有数据流
                    successful_streams = analyzer.subscribe_all_streams(session_id)
                    
                    if successful_streams:
                        print(f"\n✅ 成功订阅 {len(successful_streams)} 个数据流")
                        
                        # 7. 进行全面数据分析
                        print("\n🎯 开始数据收集和分析...")
                        print("📋 按 Ctrl+C 提前结束分析")
                        
                        analyzer.comprehensive_data_analysis(120)  # 分析2分钟
                        
                        # 8. 保存分析报告
                        analyzer.save_analysis_report()
                    else:
                        print("❌ 没有成功订阅任何数据流")
                else:
                    print("❌ 会话建立失败")
            else:
                print("❌ 没有找到连接的设备")
        else:
            print("❌ 连接失败")
    
    except KeyboardInterrupt:
        print("\n👋 分析被用户中断")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
    finally:
        analyzer.close()
        print("✅ 程序执行完毕")