import websocket
import json
import ssl
import time
import numpy as np
from collections import deque

# Cortex API 的 WebSocket URL
cortex_url = "wss://localhost:6868"

# 替换为您自己的客户端 ID 和客户端密钥
client_id = "5PQNigMKSEFMObbxlKLIWZycuBE3VzWknPUzDaWt"
client_secret = "GOlCkjxftNGLbdkTDOeIEsSdC2niQl0MEjgJYIQRDQelI011EanfEfMsYJh9bu4NuYIrPa9ZV7gbeFEUCyahuSGJMT251ZD4PQ7gDS7uLzRQcCGOzBhifVWwA630sk2R"

class FocusAnalyzer:
    def __init__(self):
        self.eeg_buffer = deque(maxlen=256)  # 保存最近的EEG数据
        self.focus_scores = deque(maxlen=10)  # 保存最近的专注度分数
        
    def analyze_focus(self, eeg_data):
        """分析EEG数据并计算专注度"""
        if len(eeg_data) < 14:  # 确保有足够的通道数据
            return 0
            
        # 简化的专注度计算（基于Beta波段功率）
        # 实际应用中需要更复杂的信号处理
        try:
            # 选择前额叶区域的电极（AF3, AF4, F3, F4）
            frontal_channels = [eeg_data[2], eeg_data[3], eeg_data[4], eeg_data[5]]
            
            # 计算信号强度
            signal_power = sum([abs(x) for x in frontal_channels if x != 0])
            
            # 归一化到0-1范围
            focus_score = min(signal_power / 1000.0, 1.0)
            
            self.focus_scores.append(focus_score)
            
            # 返回平均专注度
            return sum(self.focus_scores) / len(self.focus_scores)
            
        except Exception as e:
            print(f"专注度分析错误: {e}")
            return 0
    
    def get_focus_status(self, focus_score):
        """根据专注度分数返回状态"""
        if focus_score > 0.7:
            return "高度专注", "🟢"
        elif focus_score > 0.4:
            return "中等专注", "🟡"
        else:
            return "注意力分散", "🔴"

class SimpleCortexAPI:
    def __init__(self, url, client_id, client_secret):
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.ws = None
        self.token = None
        self.analyzer = FocusAnalyzer()

    def connect(self):
        """建立WebSocket连接"""
        try:
            self.ws = websocket.create_connection(self.url, sslopt={"cert_reqs": ssl.CERT_NONE})
            print("✅ 已连接到 Cortex API")
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

    def get_user_login(self):
        """获取已登录用户信息（无需会话）"""
        try:
            response = self.send_request("getUserLogin")
            if 'result' in response:
                print(f"✅ 用户已登录: {response['result']}")
                return True
            return False
        except:
            return False

    def query_headsets(self):
        """查询可用设备"""
        try:
            response = self.send_request("queryHeadsets")
            if 'result' in response and response['result']:
                headsets = response['result']
                for headset in headsets:
                    if headset['status'] == 'connected':
                        print(f"🎧 找到连接的设备: {headset['id']}")
                        return headset['id']
            print("⚠️ 没有找到连接的设备")
            return None
        except Exception as e:
            print(f"❌ 查询设备失败: {e}")
            return None

    def request_access(self):
        """请求访问权限"""
        try:
            response = self.send_request("requestAccess", {
                "clientId": self.client_id,
                "clientSecret": self.client_secret
            })
            if 'result' in response and response['result']['accessGranted']:
                print("✅ 访问权限已获得")
                return True
            print("❌ 访问权限被拒绝")
            return False
        except Exception as e:
            print(f"❌ 请求访问失败: {e}")
            return False

    def authorize(self, debit=None):
        """获取授权token"""
        try:
            params = {
                "clientId": self.client_id,
                "clientSecret": self.client_secret
            }
            
            # 如果提供了debit参数，添加到请求中
            if debit is not None:
                params["debit"] = debit
                print(f"🪙 使用 {debit} 个 debit 进行授权...")
            
            response = self.send_request("authorize", params)
            if 'result' in response and 'cortexToken' in response['result']:
                self.token = response['result']['cortexToken']
                print("✅ 授权成功")
                return True
            print("❌ 授权失败")
            return False
        except Exception as e:
            print(f"❌ 授权过程出错: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.ws:
            self.ws.close()
            print("🔌 连接已关闭")

    def create_session(self, headset_id):
        """创建会话"""
        try:
            response = self.send_request("createSession", {
                "cortexToken": self.token,
                "headset": headset_id,
                "status": "active"
            })
            if 'result' in response:
                session_id = response['result']['id']
                print(f"✅ 会话创建成功: {session_id}")
                return session_id
            else:
                print(f"❌ 创建会话失败: {response}")
                return None
        except Exception as e:
            print(f"❌ 创建会话出错: {e}")
            return None

    def subscribe_data(self, session_id, streams=["eeg", "met"]):
        """订阅数据流"""
        try:
            response = self.send_request("subscribe", {
                "cortexToken": self.token,
                "session": session_id,
                "streams": streams
            })
            if 'result' in response:
                print(f"✅ 订阅成功: {response['result']}")
                return True
            else:
                print(f"❌ 订阅失败: {response}")
                return False
        except Exception as e:
            print(f"❌ 订阅出错: {e}")
            return False

    def monitor_realtime_data(self):
        """监控实时数据流"""
        print("🧠 开始监控脑电数据...")
        print("📊 专注度分析:")
        print("-" * 50)
        
        session_id = None
        
        # 尝试获取访问权限和授权
        if self.request_access():
            print("🔄 尝试免费授权...")
            if self.authorize():
                headset_id = self.query_headsets()
                if headset_id:
                    print("🔄 创建会话...")
                    session_id = self.create_session(headset_id)
                    if session_id:
                        print("🔄 订阅数据流...")
                        if self.subscribe_data(session_id):
                            print("✅ 开始接收数据流...")
                        else:
                            print("⚠️ 订阅失败，但继续尝试监听...")
                    else:
                        print("⚠️ 免费会话创建失败，尝试付费授权...")
                        # 尝试使用debit进行付费授权
                        if self.authorize(debit=1):
                            print("🔄 使用付费授权创建会话...")
                            session_id = self.create_session(headset_id)
                            if session_id:
                                print("🔄 订阅数据流...")
                                if self.subscribe_data(session_id):
                                    print("✅ 开始接收数据流...")
                                else:
                                    print("⚠️ 订阅失败，但继续尝试监听...")
                            else:
                                print("❌ 付费会话也创建失败")
        
        data_count = 0
        no_data_count = 0
        timeout_count = 0
        
        while True:
            try:
                # 设置接收超时
                self.ws.settimeout(5.0)
                message = self.ws.recv()
                data = json.loads(message)
                
                # 重置超时计数
                timeout_count = 0
                
                # 调试: 打印接收到的数据类型
                if no_data_count % 50 == 0:
                    print(f"🔍 接收到数据类型: {list(data.keys())}")
                
                # 检查是否是EEG数据
                if 'eeg' in data:
                    eeg_values = data['eeg']
                    if len(eeg_values) > 1:
                        focus_score = self.analyzer.analyze_focus(eeg_values[1:])
                        status, emoji = self.analyzer.get_focus_status(focus_score)
                        
                        data_count += 1
                        print(f"{emoji} 专注度: {focus_score:.2f} | 状态: {status} | 数据#{data_count}")
                
                # 检查性能指标数据
                elif 'met' in data:
                    met_values = data['met']
                    if len(met_values) > 1:
                        print(f"📈 性能指标: {met_values[1:]}")
                
                # 检查其他类型的数据
                elif 'sys' in data:
                    print(f"🔧 系统消息: {data['sys']}")
                
                # 检查错误消息
                elif 'error' in data:
                    print(f"❌ 接收到错误: {data['error']}")
                
                else:
                    no_data_count += 1
                    if no_data_count % 50 == 0:
                        print(f"⏳ 等待EEG数据... (已接收 {no_data_count} 个其他数据包)")
                        print(f"📋 数据内容: {data}")
                
            except websocket.WebSocketTimeoutException:
                timeout_count += 1
                if timeout_count <= 3:
                    print(f"⏰ 等待数据超时 ({timeout_count}/3)，继续监听...")
                elif timeout_count == 4:
                    print("⚠️ 多次超时，可能的原因:")
                    print("   1. 没有创建成功的会话来获取EEG数据")
                    print("   2. 设备需要重新连接")
                    print("   3. 可能需要在 EMOTIV Launcher 中手动启动数据流")
                    if session_id:
                        print(f"   当前会话ID: {session_id}")
                    else:
                        print("   当前没有活跃会话")
                    print("\n💡 建议:")
                    print("   1. 确保您的账户有足够的 debit 余额")
                    print("   2. 在 EMOTIV Launcher 中检查设备状态")
                    print("   3. 尝试重新启动 EMOTIV Launcher")
                continue
            except websocket.WebSocketConnectionClosedException:
                print("❌ 连接已关闭")
                break
            except KeyboardInterrupt:
                print("\n⏹️ 用户中断监控")
                break
            except Exception as e:
                print(f"❌ 数据处理错误: {e}")
                time.sleep(1)
                continue


# --- 主程序 ---
if __name__ == "__main__":
    print("🚀 启动脑电专注度监控系统")
    print("📝 注意: 此版本尝试监控可用数据")
    
    api = SimpleCortexAPI(cortex_url, client_id, client_secret)
    
    try:
        if api.connect():
            if api.get_user_login():
                print("✨ 开始实时监控...")
                api.monitor_realtime_data()
            else:
                print("⚠️ 请确保在 EMOTIV Launcher 中已登录")
    except KeyboardInterrupt:
        print("\n👋 程序已停止")
    finally:
        api.close()