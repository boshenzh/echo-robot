English | [简体中文](./RAEDME_zh.md)

# echome_smart
echome_smart is an intelligent home control system based on TuyaOpen framework. It combines AI voice chat capabilities with smart home control features, providing MQTT communication, device management, and interactive voice assistance.

**Note: This project is based on your_chat_bot and includes enhanced smart home features.**

## Supported Features

1. AI intelligent conversation (inherited from your_chat_bot)
2. Button wake-up/Voice wake-up, turn-ended dialogue, supports voice interruption
3. Expression display and real-time chat content on LCD
4. MQTT communication for IoT device control
5. Smart home device management interface
6. Multi-page navigation system
7. Wi-Fi and cloud connectivity status monitoring
8. Quick Bluetooth network connection to router
9. Real-time switching of AI entity roles on the APP side

![](../../../docs/images/apps/your_chat_bot.png)

## Hardware Dependencies
1. Audio capture
2. Audio playback
3. LCD display with touch support
4. Wi-Fi connectivity

## Supported Hardware
| Model | Description | Reset Method |
| --- | --- | --- |
| TUYA T5AI_Board Development Board | [https://developer.tuya.com/en/docs/iot-device-dev/T5-E1-IPEX-development-board?id=Ke9xehig1cabj](https://developer.tuya.com/en/docs/iot-device-dev/T5-E1-IPEX-development-board?id=Ke9xehig1cabj) | Reset by restarting 3 times |
| TUYA T5AI_EVB Board | [https://oshwhub.com/flyingcys/t5ai_evb](https://oshwhub.com/flyingcys/t5ai_evb) | Reset by restarting 3 times |

## Compilation
1. Run the `tos config_choice` command to select the current development board in use.
2. If you need to modify the configuration, run the `tos menuconfig` command to make changes.
3. Run the `tos build` command to compile the project.
