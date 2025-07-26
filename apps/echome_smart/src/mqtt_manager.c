#include "mqtt_manager.h"
#include "tuya_log.h"
#include "tal_api.h"
#include <string.h>
#include <stdio.h>

/***********************************************************
************************ 宏定义 ****************************
***********************************************************/
#define MQTT_BROKER_HOST        "172.20.10.3"
#define MQTT_BROKER_PORT        1883
#define MQTT_CLIENT_ID          "echome_smart_device_001"
#define MQTT_TOPIC_START        "topic/start"
#define MQTT_KEEPALIVE_INTERVAL 60
#define MQTT_TIMEOUT_MS         5000

/***********************************************************
************************ 类型定义 **************************
***********************************************************/
typedef struct {
    void *mqtt_client;
    mqtt_state_t state;
    bool initialized;
} mqtt_manager_t;

/***********************************************************
************************ 静态变量 **************************
***********************************************************/
static mqtt_manager_t sg_mqtt = {0};

/***********************************************************
************************ 回调函数 **************************
***********************************************************/

/**
 * @brief MQTT连接成功回调
 */
static void mqtt_connected_cb(void *client, void *userdata)
{
    PR_INFO("MQTT connected to %s:%d", MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    sg_mqtt.state = MQTT_STATE_CONNECTED;
}

/**
 * @brief MQTT断开连接回调
 */
static void mqtt_disconnected_cb(void *client, void *userdata)
{
    PR_INFO("MQTT disconnected from %s:%d", MQTT_BROKER_HOST, MQTT_BROKER_PORT);
    sg_mqtt.state = MQTT_STATE_DISCONNECTED;
}

/**
 * @brief MQTT消息接收回调
 */
static void mqtt_message_cb(void *client, uint16_t msgid, const mqtt_client_message_t *msg, void *userdata)
{
    PR_DEBUG("MQTT received message on topic: %s, length: %d", msg->topic, msg->length);
}

/**
 * @brief MQTT发布成功回调
 */
static void mqtt_published_cb(void *client, uint16_t msgid, void *userdata)
{
    PR_DEBUG("MQTT message published successfully, msgid: %d", msgid);
}

/**
 * @brief MQTT订阅成功回调
 */
static void mqtt_subscribed_cb(void *client, uint16_t msgid, void *userdata)
{
    PR_DEBUG("MQTT subscribed successfully, msgid: %d", msgid);
}

/**
 * @brief MQTT取消订阅回调
 */
static void mqtt_unsubscribed_cb(void *client, uint16_t msgid, void *userdata)
{
    PR_DEBUG("MQTT unsubscribed successfully, msgid: %d", msgid);
}

/***********************************************************
************************ 公共函数 **************************
***********************************************************/

/**
 * @brief 初始化MQTT管理器
 */
int mqtt_manager_init(void)
{
    if (sg_mqtt.initialized) {
        PR_WARN("MQTT manager already initialized");
        return 0;
    }

    // 创建MQTT客户端
    sg_mqtt.mqtt_client = mqtt_client_new();
    if (!sg_mqtt.mqtt_client) {
        PR_ERR("Failed to create MQTT client");
        return -1;
    }

    // 配置MQTT客户端
    mqtt_client_config_t config = {
        .cacert = NULL,
        .cacert_len = 0,
        .host = MQTT_BROKER_HOST,
        .port = MQTT_BROKER_PORT,
        .keepalive = MQTT_KEEPALIVE_INTERVAL,
        .timeout_ms = MQTT_TIMEOUT_MS,
        .clientid = MQTT_CLIENT_ID,
        .username = NULL,  // 无用户名
        .password = NULL,  // 无密码
        .userdata = NULL,
        .on_connected = mqtt_connected_cb,
        .on_disconnected = mqtt_disconnected_cb,
        .on_message = mqtt_message_cb,
        .on_published = mqtt_published_cb,
        .on_subscribed = mqtt_subscribed_cb,
        .on_unsubscribed = mqtt_unsubscribed_cb
    };

    // 初始化MQTT客户端
    mqtt_client_status_t status = mqtt_client_init(sg_mqtt.mqtt_client, &config);
    if (status != MQTT_STATUS_SUCCESS) {
        PR_ERR("Failed to initialize MQTT client, status: %d", status);
        mqtt_client_free(sg_mqtt.mqtt_client);
        sg_mqtt.mqtt_client = NULL;
        return -1;
    }

    sg_mqtt.state = MQTT_STATE_DISCONNECTED;
    sg_mqtt.initialized = true;

    PR_INFO("MQTT manager initialized successfully");
    return 0;
}

/**
 * @brief 反初始化MQTT管理器
 */
void mqtt_manager_deinit(void)
{
    if (!sg_mqtt.initialized) {
        return;
    }

    if (sg_mqtt.mqtt_client) {
        if (sg_mqtt.state == MQTT_STATE_CONNECTED) {
            mqtt_client_disconnect(sg_mqtt.mqtt_client);
        }
        mqtt_client_deinit(sg_mqtt.mqtt_client);
        mqtt_client_free(sg_mqtt.mqtt_client);
        sg_mqtt.mqtt_client = NULL;
    }

    sg_mqtt.state = MQTT_STATE_DISCONNECTED;
    sg_mqtt.initialized = false;

    PR_INFO("MQTT manager deinitialized");
}

/**
 * @brief 获取MQTT连接状态
 */
mqtt_state_t mqtt_manager_get_state(void)
{
    return sg_mqtt.state;
}

/**
 * @brief 发布start消息
 */
int mqtt_manager_publish_start(bool start_value)
{
    if (!sg_mqtt.initialized || !sg_mqtt.mqtt_client) {
        PR_ERR("MQTT manager not initialized");
        return -1;
    }

    // 如果未连接，先尝试连接
    if (sg_mqtt.state == MQTT_STATE_DISCONNECTED) {
        PR_INFO("MQTT connecting to %s:%d", MQTT_BROKER_HOST, MQTT_BROKER_PORT);
        sg_mqtt.state = MQTT_STATE_CONNECTING;
        
        mqtt_client_status_t status = mqtt_client_connect(sg_mqtt.mqtt_client);
        if (status != MQTT_STATUS_SUCCESS) {
            PR_ERR("Failed to connect MQTT broker, status: %d", status);
            sg_mqtt.state = MQTT_STATE_DISCONNECTED;
            return -1;
        }
        
        // 等待连接完成
        for (int i = 0; i < 50 && sg_mqtt.state != MQTT_STATE_CONNECTED; i++) {
            mqtt_client_yield(sg_mqtt.mqtt_client);
            tal_system_sleep(100);
        }
        
        if (sg_mqtt.state != MQTT_STATE_CONNECTED) {
            PR_ERR("MQTT connection timeout");
            sg_mqtt.state = MQTT_STATE_DISCONNECTED;
            return -1;
        }
    }

    // 发布消息
    const char *payload = start_value ? "true" : "false";
    uint16_t msgid = mqtt_client_publish(sg_mqtt.mqtt_client, MQTT_TOPIC_START, 
                                       (const uint8_t *)payload, strlen(payload), MQTT_QOS_0);
    
    if (msgid <= 0) {
        PR_ERR("Failed to publish start message");
        return -1;
    }

    PR_INFO("Published to %s: %s (msgid: %d)", MQTT_TOPIC_START, payload, msgid);
    
    // 处理发布结果
    mqtt_client_yield(sg_mqtt.mqtt_client);
    
    return 0;
} 