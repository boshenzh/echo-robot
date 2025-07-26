#ifndef __MQTT_MANAGER_H__
#define __MQTT_MANAGER_H__

#include "mqtt_client_interface.h"

// MQTT连接状态
typedef enum {
    MQTT_STATE_DISCONNECTED = 0,
    MQTT_STATE_CONNECTING,
    MQTT_STATE_CONNECTED
} mqtt_state_t;

// MQTT管理器接口
int mqtt_manager_init(void);
void mqtt_manager_deinit(void);
mqtt_state_t mqtt_manager_get_state(void);
int mqtt_manager_publish_start(bool start_value);

#endif // __MQTT_MANAGER_H__ 