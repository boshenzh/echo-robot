import websocket
import json
import ssl
import time

# Cortex API 的 WebSocket URL
cortex_url = "wss://localhost:6868"

# 替换为您自己的客户端 ID 和客户端密钥
client_id = "5PQNigMKSEFMObbxlKLIWZycuBE3VzWknPUzDaWt"
client_secret = "GOlCkjxftNGLbdkTDOeIEsSdC2niQl0MEjgJYIQRDQelI011EanfEfMsYJh9bu4NuYIrPa9ZV7gbeFEUCyahuSGJMT251ZD4PQ7gDS7uLzRQcCGOzBhifVWwA630sk2R"

class SimpleCortexAPI:
    def __init__(self, url, client_id, client_secret):
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.ws = None
        self.token = None

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
        """获取已登录用户信息"""
        try:
            response = self.send_request("getUserLogin")
            if 'result' in response:
                print(f"✅ 用户已登录: {response['result'][0]['username']}")
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

    def test_data_stream(self, duration=30):
        """测试数据流接收"""
        print(f" 开始测试数据流接收 (持续 {duration} 秒)...")
        print("-" * 50)
        
        eeg_count = 0
        met_count = 0
        other_count = 0
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                self.ws.settimeout(5.0)
                message = self.ws.recv()
                data = json.loads(message)
                
                # 统计不同类型的数据
                if 'eeg' in data:
                    eeg_count += 1
                    if eeg_count <= 3:  # 只显示前3次EEG数据作为示例
                        print(f" EEG数据 #{eeg_count}: 接收到 {len(data['eeg'])} 个值")
                        print(f"    前5个值: {data['eeg'][:5]}")
                
                elif 'met' in data:
                    met_count += 1
                    if met_count <= 3:  # 只显示前3次性能指标数据
                        print(f" 性能指标 #{met_count}: {data['met']}")
                
                elif 'sys' in data:
                    print(f" 系统消息: {data['sys']}")
                
                elif 'error' in data:
                    print(f"❌ 错误消息: {data['error']}")
                
                else:
                    other_count += 1
                    if other_count % 10 == 1:  # 每10个其他数据包显示一次
                        print(f"📋 其他数据: {list(data.keys())}")
                
            except websocket.WebSocketTimeoutException:
                print(" 等待数据超时...")
                continue
            except websocket.WebSocketConnectionClosedException:
                print("❌ 连接已关闭")
                break
            except KeyboardInterrupt:
                print("\n 用户中断测试")
                break
            except Exception as e:
                print(f"❌ 数据处理错误: {e}")
                continue
        
        # 显示统计结果
        print("\n" + "="*50)
        print(" 数据接收统计:")
        print(f"   EEG数据包: {eeg_count}")
        print(f"   性能指标数据包: {met_count}")
        print(f"   其他数据包: {other_count}")
        print(f"   总计: {eeg_count + met_count + other_count}")
        
        if eeg_count > 0:
            print("✅ EEG数据接收成功!")
        else:
            print("⚠️ 未接收到EEG数据")
            
        if met_count > 0:
            print("✅ 性能指标数据接收成功!")
        else:
            print("⚠️ 未接收到性能指标数据")

    def close(self):
        """关闭连接"""
        if self.ws:
            self.ws.close()
            print("🔌 连接已关闭")

# --- 主程序 ---
if __name__ == "__main__":
    print("🚀 启动 Cortex API 连接测试")
    print("📝 目标: 测试连接和数据接收功能")
    
    api = SimpleCortexAPI(cortex_url, client_id, client_secret)
    
    try:
        # 步骤1: 建立连接
        if api.connect():
            # 步骤2: 检查用户登录
            if api.get_user_login():
                # 步骤3: 请求访问权限
                if api.request_access():
                    # 步骤4: 获取授权
                    if api.authorize():
                        # 步骤5: 查询设备
                        headset_id = api.query_headsets()
                        if headset_id:
                            # 步骤6: 创建会话
                            session_id = api.create_session(headset_id)
                            if session_id:
                                # 步骤7: 订阅数据流
                                if api.subscribe_data(session_id):
                                    # 步骤8: 测试数据接收
                                    api.test_data_stream(30)  # 测试30秒
                                else:
                                    print("❌ 订阅失败")
                            else:
                                print("❌ 会话创建失败，尝试付费授权...")
                                # 尝试付费授权
                                if api.authorize(debit=1):
                                    session_id = api.create_session(headset_id)
                                    if session_id:
                                        if api.subscribe_data(session_id):
                                            api.test_data_stream(30)
                        else:
                            print("❌ 没有找到设备")
                    else:
                        print("❌ 授权失败")
                else:
                    print("❌ 访问权限获取失败")
            else:
                print("❌ 用户未登录")
        else:
            print("❌ 连接失败")
    
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    finally:
        api.close()
        print("✅ 测试完成")