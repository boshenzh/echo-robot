#!/usr/bin/env python3
"""
脑机接口与机械臂集成控制程序
用于脑机接口触发机械臂执行动作
"""

import logging
import time
import signal
import sys
import threading
import queue
from typing import Dict, Any, Optional, List, Callable

# --- 本地模块导入 ---
from robot_controller import RobotController, MoveResult

# --- 配置日志 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("brain_robot_integration.log")
    ]
)
logger = logging.getLogger(__name__)

class MQTTDisplayTest:
    """测试与显示屏的 MQTT 通信"""
    
    # MQTT 配置
    MQTT_BROKER = "localhost"  # MQTT服务器地址，本地测试使用localhost
    MQTT_PORT = 1883           # 标准MQTT端口
    MQTT_TOPIC = "echo_robot/display"  # 发布主题
    MQTT_CLIENT_ID = f"echo-robot-{random.randint(0, 1000)}"  # 随机客户端ID
    
    def __init__(self):
        """初始化 MQTT 测试"""
        self.running = True
        self.client = None
        self.connected = False
        
        logger.info("MQTT显示屏测试初始化")

    def setup(self):
        """设置 MQTT 客户端"""
        try:
            # 创建客户端实例
            self.client = mqtt.Client(client_id=self.MQTT_CLIENT_ID, 
                                      clean_session=True,
                                      protocol=mqtt.MQTTv311)
            
            # 设置回调函数
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            self.client.on_message = self._on_message
            
            # 连接到服务器
            logger.info(f"正在连接到MQTT服务器 {self.MQTT_BROKER}:{self.MQTT_PORT}...")
            self.client.connect(self.MQTT_BROKER, self.MQTT_PORT, 60)
            
            # 启动后台线程
            self.client.loop_start()
            
            # 等待连接建立
            timeout = 5  # 5秒超时
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if not self.connected:
                logger.error("连接MQTT服务器超时")
                return False
                
            # 订阅反馈主题
            self.client.subscribe(f"{self.MQTT_TOPIC}/feedback")
            logger.info(f"已订阅主题: {self.MQTT_TOPIC}/feedback")
            
            return True
            
        except Exception as e:
            logger.error(f"MQTT设置失败: {e}", exc_info=True)
            return False

    def run(self):
        """运行测试发送循环"""
        logger.info("开始MQTT测试发送...")
        
        try:
            message_count = 1
            
            while self.running:
                # 创建测试消息
                message = {
                    "id": message_count,
                    "timestamp": time.time(),
                    "type": "status_update",
                    "data": {
                        "robot_status": "测试中",
                        "position": {
                            "x": round(random.uniform(50, 150), 1),
                            "y": round(random.uniform(0, 100), 1),
                            "z": round(random.uniform(0, 50), 1)
                        },
                        "battery": random.randint(20, 100)
                    }
                }
                
                # 发布消息
                self._publish_message(message)
                message_count += 1
                
                # 每3秒发送一次
                time.sleep(3)
                
        except KeyboardInterrupt:
            logger.info("收到退出信号")
        except Exception as e:
            logger.error(f"运行时出错: {e}", exc_info=True)
        finally:
            self.shutdown()

    def shutdown(self):
        """安全关闭 MQTT 连接"""
        logger.info("正在关闭 MQTT 连接...")
        self.running = False
        
        if self.client:
            try:
                # 发送断开连接消息
                self._publish_message({
                    "type": "system",
                    "action": "disconnect",
                    "message": "MQTT测试客户端断开连接"
                })
                
                # 等待最后一条消息发送完成
                time.sleep(0.5)
                
                # 停止后台线程并断开连接
                self.client.loop_stop()
                self.client.disconnect()
                logger.info("MQTT客户端已断开连接")
                
            except Exception as e:
                logger.error(f"MQTT客户端断开连接出错: {e}")
        
        logger.info("MQTT测试已结束")

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.connected = True
            logger.info("已成功连接到MQTT服务器!")
        else:
            logger.error(f"连接失败，返回码: {rc}")
            # 返回码含义:
            # 0: 连接成功
            # 1: 协议版本不正确
            # 2: 无效的客户端标识
            # 3: 服务器不可用
            # 4: 用户名或密码错误
            # 5: 未授权

    def _on_disconnect(self, client, userdata, rc):
        """MQTT断开连接回调"""
        self.connected = False
        if rc != 0:
            logger.warning(f"意外断开连接，返回码: {rc}")
        else:
            logger.info("已断开与MQTT服务器的连接")

    def _on_publish(self, client, userdata, mid):
        """消息发布回调"""
        logger.debug(f"消息ID {mid} 已发布")

    def _on_message(self, client, userdata, msg):
        """接收消息回调"""
        try:
            payload = msg.payload.decode('utf-8')
            logger.info(f"收到主题 {msg.topic} 的消息: {payload}")
            
            # 尝试解析JSON
            try:
                data = json.loads(payload)
                logger.info(f"解析的JSON数据: {data}")
            except json.JSONDecodeError:
                logger.warning(f"收到的消息不是有效JSON: {payload}")
                
        except Exception as e:
            logger.error(f"处理接收消息时出错: {e}")

    def _publish_message(self, message: Dict[str, Any]):
        """发布消息到MQTT主题"""
        if not self.connected:
            logger.warning("MQTT未连接，无法发送消息")
            return False
            
        try:
            # 将消息转换为JSON
            payload = json.dumps(message)
            
            # 发布消息
            result = self.client.publish(self.MQTT_TOPIC, payload, qos=1)
            
            # 检查发布结果
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"消息已发送: {payload[:100]}...")
                return True
            else:
                logger.warning(f"消息发送失败，错误码: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"发布消息出错: {e}")
            return False


def signal_handler(sig, frame):
    """处理系统信号"""
    logger.info(f"收到系统信号 {sig}，准备安全退出")
    global mqtt_tester
    if mqtt_tester:
        mqtt_tester.shutdown()
    sys.exit(0)


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 创建并启动MQTT测试
    mqtt_tester = MQTTDisplayTest()
    
    try:
        if mqtt_tester.setup():
            mqtt_tester.run()
        else:
            logger.error("MQTT设置失败，无法启动测试")
    except Exception as e:
        logger.critical(f"主程序未处理异常: {e}", exc_info=True)
    finally:
        # 确保安全关闭
        if mqtt_tester:
            mqtt_tester.shutdown()
        
        logger.info("程序已退出")
