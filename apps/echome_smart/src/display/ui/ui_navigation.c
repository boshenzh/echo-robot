#include "ui_navigation.h"
#include "ui_manager.h"
#include "ui_focus.h"
#include "font_awesome_symbols.h"
#include "tuya_log.h"
#include "tal_api.h"
#include <stdio.h>

// Navigation页面相关宏定义
#define NAV_START_BUTTON_SIZE 120
#define NAV_START_BUTTON_RADIUS 60
#define NAV_SLIDER_WIDTH 200
#define NAV_SLIDER_HEIGHT 30
#define NAV_TIME_MIN 0.0f
#define NAV_TIME_MAX 2.0f

// Navigation页面UI结构体
typedef struct {
    lv_obj_t *container;           // 页面容器
    lv_obj_t *background;          // 背景
    lv_obj_t *nav_start_button;    // 开始按钮
    lv_obj_t *nav_start_label;     // 开始按钮文字
    lv_obj_t *nav_time_slider;     // 时间slider
    lv_obj_t *nav_time_label;      // 时间显示标签
    lv_obj_t *nav_wifi_label;      // WiFi状态显示
    
    float selected_time;               // 选择的专注时间（小时）
} UI_NAVIGATION_T;

static UI_NAVIGATION_T sg_nav = {0};

// 前向声明
static void __ui_create_navigation_container(void);
static void __ui_create_navigation_background(void);
static void __ui_create_navigation_start_button(void);
static void __ui_create_navigation_time_slider(void);
static void __ui_create_navigation_wifi_status(void);
static void __start_button_event_cb(lv_event_t *e);
static void __time_slider_event_cb(lv_event_t *e);
static lv_color_t __get_slider_gradient_color(float value);

/**
 * @brief 初始化navigation页面
 */
int ui_navigation_init(UI_FONT_T *ui_font)
{
    (void)ui_font; // navigation页面不使用字体
    
    // 清空状态
    memset(&sg_nav, 0, sizeof(UI_NAVIGATION_T));
    sg_nav.selected_time = 1.0f;  // 默认1小时
    
    // 创建UI组件
    __ui_create_navigation_container();
    __ui_create_navigation_background();
    __ui_create_navigation_start_button();
    __ui_create_navigation_time_slider();
    __ui_create_navigation_wifi_status();
    

    
    // 初始隐藏
    lv_obj_add_flag(sg_nav.container, LV_OBJ_FLAG_HIDDEN);
    
    PR_INFO("Navigation page initialized");
    return 0;
}

/**
 * @brief 显示navigation页面
 */
void ui_navigation_show(void)
{
    lv_obj_clear_flag(sg_nav.container, LV_OBJ_FLAG_HIDDEN);
    PR_INFO("Navigation page shown");
}

/**
 * @brief 隐藏navigation页面
 */
void ui_navigation_hide(void)
{
    lv_obj_add_flag(sg_nav.container, LV_OBJ_FLAG_HIDDEN);
    PR_INFO("Navigation page hidden");
}

/**
 * @brief 获取选择的专注时间
 */
float ui_navigation_get_selected_time(void)
{
    return sg_nav.selected_time;
}

/**
 * @brief 设置专注时间
 */
void ui_navigation_set_selected_time(float time)
{
    sg_nav.selected_time = time;
    if (sg_nav.nav_time_slider) {
        int32_t slider_value = (int32_t)(time / NAV_TIME_MAX * 100);
        lv_slider_set_value(sg_nav.nav_time_slider, slider_value, LV_ANIM_OFF);
    }
}

/**
 * @brief 创建navigation页面容器
 */
static void __ui_create_navigation_container(void)
{
    sg_nav.container = lv_obj_create(lv_scr_act());
    lv_obj_set_size(sg_nav.container, LV_PCT(100), LV_PCT(100));
    lv_obj_set_pos(sg_nav.container, 0, 0);
    lv_obj_clear_flag(sg_nav.container, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(sg_nav.container, lv_color_black(), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_nav.container, LV_OPA_COVER, LV_PART_MAIN);
}

/**
 * @brief 创建navigation页面背景
 */
static void __ui_create_navigation_background(void)
{
    sg_nav.background = lv_obj_create(sg_nav.container);
    lv_obj_set_size(sg_nav.background, LV_PCT(100), LV_PCT(100));
    lv_obj_set_pos(sg_nav.background, 0, 0);
    lv_obj_clear_flag(sg_nav.background, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(sg_nav.background, lv_color_hex(0xD8E2EC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_nav.background, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_nav.background, 0, LV_PART_MAIN);
}

/**
 * @brief 创建开始按钮
 */
static void __ui_create_navigation_start_button(void)
{
    sg_nav.nav_start_button = lv_obj_create(sg_nav.container);
    lv_obj_set_size(sg_nav.nav_start_button, NAV_START_BUTTON_SIZE, NAV_START_BUTTON_SIZE);
    lv_obj_align(sg_nav.nav_start_button, LV_ALIGN_CENTER, 0, -30);  // button坐标
    lv_obj_clear_flag(sg_nav.nav_start_button, LV_OBJ_FLAG_SCROLLABLE);
    
    // 设置开始按钮样式
    lv_obj_set_style_bg_color(sg_nav.nav_start_button, lv_color_hex(0x529ACC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_nav.nav_start_button, LV_OPA_30, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_nav.nav_start_button, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_nav.nav_start_button, NAV_START_BUTTON_RADIUS, LV_PART_MAIN);
    
    // 创建开始按钮文字
    sg_nav.nav_start_label = lv_label_create(sg_nav.nav_start_button);
    lv_label_set_text(sg_nav.nav_start_label, "Start");
    lv_obj_set_style_text_color(sg_nav.nav_start_label, lv_color_hex(0x333333), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_nav.nav_start_label, &lv_font_montserrat_24, LV_PART_MAIN);
    lv_obj_center(sg_nav.nav_start_label);
    
    // 添加开始按钮点击事件
    lv_obj_add_event_cb(sg_nav.nav_start_button, __start_button_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(sg_nav.nav_start_button, __start_button_event_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(sg_nav.nav_start_button, __start_button_event_cb, LV_EVENT_PRESS_LOST, NULL);
}

/**
 * @brief 创建时间slider
 */
static void __ui_create_navigation_time_slider(void)
{
    sg_nav.nav_time_slider = lv_slider_create(sg_nav.container);
    lv_obj_set_size(sg_nav.nav_time_slider, NAV_SLIDER_WIDTH, NAV_SLIDER_HEIGHT);
    lv_obj_align(sg_nav.nav_time_slider, LV_ALIGN_BOTTOM_MID, 0, -40);
    lv_slider_set_range(sg_nav.nav_time_slider, 0, 100);
    lv_slider_set_value(sg_nav.nav_time_slider, 50, LV_ANIM_OFF);  // 默认1.0小时
    
    // 设置slider样式
    lv_obj_set_style_bg_color(sg_nav.nav_time_slider, lv_color_hex(0xE0E0E0), LV_PART_MAIN);
    lv_obj_set_style_bg_color(sg_nav.nav_time_slider, lv_color_hex(0xB0DAF0), LV_PART_INDICATOR);
    lv_obj_set_style_bg_color(sg_nav.nav_time_slider, lv_color_hex(0x529ACC), LV_PART_KNOB);
    
    // 添加slider事件
    lv_obj_add_event_cb(sg_nav.nav_time_slider, __time_slider_event_cb, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(sg_nav.nav_time_slider, __time_slider_event_cb, LV_EVENT_PRESSING, NULL);
    
    // 创建时间显示标签
    sg_nav.nav_time_label = lv_label_create(sg_nav.container);
    lv_obj_set_style_text_color(sg_nav.nav_time_label, lv_color_hex(0x333333), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_nav.nav_time_label, &lv_font_montserrat_14, LV_PART_MAIN);
    lv_obj_align(sg_nav.nav_time_label, LV_ALIGN_BOTTOM_MID, 0, -80);
    
    // 设置初始时间显示
    char time_str[16];
    int hours = (int)sg_nav.selected_time;
    int minutes = (int)((sg_nav.selected_time - hours) * 60);
    
    if (hours > 0) {
        if (minutes > 0) {
            sprintf(time_str, "%dh %dmin", hours, minutes);
        } else {
            sprintf(time_str, "%dh", hours);
        }
    } else {
        sprintf(time_str, "%dmin", minutes);
    }
    
    lv_label_set_text(sg_nav.nav_time_label, time_str);
}

/**
 * @brief 创建navigation页面wifi状态显示
 */
static void __ui_create_navigation_wifi_status(void)
{
    sg_nav.nav_wifi_label = lv_label_create(sg_nav.container);
    lv_label_set_text(sg_nav.nav_wifi_label, FONT_AWESOME_WIFI_OFF);
    lv_obj_set_style_text_color(sg_nav.nav_wifi_label, lv_color_hex(0x666666), LV_PART_MAIN);
    
    extern const lv_font_t font_awesome_16_4;
    lv_obj_set_style_text_font(sg_nav.nav_wifi_label, &font_awesome_16_4, LV_PART_MAIN);
    
    lv_obj_set_size(sg_nav.nav_wifi_label, 30, 30);  // 设置固定大小确保可见
    lv_obj_align(sg_nav.nav_wifi_label, LV_ALIGN_TOP_RIGHT, -15, 15);  // 与wait页面保持一致
}

// 动画相关函数已移除

/**
 * @brief start button事件回调
 */
static void __start_button_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    
    if (code == LV_EVENT_PRESSED) {
        PR_INFO("Start button pressed");
        
    } else if (code == LV_EVENT_RELEASED || code == LV_EVENT_PRESS_LOST) {
        PR_INFO("Start button released - jumping to focus page");
        
        int hours = (int)sg_nav.selected_time;
        int minutes = (int)((sg_nav.selected_time - hours) * 60);
        
        if (hours > 0) {
            if (minutes > 0) {
                PR_INFO("Jumping to focus page with %dh %dmin", hours, minutes);
            } else {
                PR_INFO("Jumping to focus page with %dh", hours);
            }
        } else {
            PR_INFO("Jumping to focus page with %dmin", minutes);
        }
        
        // 设置专注页面的时间
        ui_focus_set_time(sg_nav.selected_time);
        
        // 通过串口发送布尔值到电脑
        const char *serial_msg = "true\n";
        tal_uart_write(TUYA_UART_NUM_0, (const uint8_t *)serial_msg, strlen(serial_msg));
        PR_INFO("Serial message sent: %s", serial_msg);
        
        // 发送MQTT start消息 - 暂时注释掉用于调试
        // extern int mqtt_manager_publish_start(bool start_value);
        // int ret = mqtt_manager_publish_start(true);
        // if (ret == 0) {
        //     PR_INFO("MQTT start message sent successfully");
        // } else {
        //     PR_WARN("Failed to send MQTT start message: %d", ret);
        // }
        
        ui_manager_show_focus_page();
    }
}

/**
 * @brief 时间slider事件回调
 */
static void __time_slider_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    
    if (code == LV_EVENT_VALUE_CHANGED || code == LV_EVENT_PRESSING) {
        int32_t slider_value = lv_slider_get_value(sg_nav.nav_time_slider);
        sg_nav.selected_time = (float)slider_value / 100.0f * NAV_TIME_MAX;
        
        char time_str[16];
        int hours = (int)sg_nav.selected_time;
        int minutes = (int)((sg_nav.selected_time - hours) * 60);
        
        if (hours > 0) {
            if (minutes > 0) {
                sprintf(time_str, "%dh %dmin", hours, minutes);
            } else {
                sprintf(time_str, "%dh", hours);
            }
        } else {
            sprintf(time_str, "%dmin", minutes);
        }
        
        lv_label_set_text(sg_nav.nav_time_label, time_str);
        
        lv_color_t bg_color = __get_slider_gradient_color(sg_nav.selected_time);
        lv_obj_set_style_bg_color(sg_nav.background, bg_color, LV_PART_MAIN);
        
        PR_INFO("Time slider changed: %s", time_str);
    }
}

/**
 * @brief 获取slider渐变颜色
 */
static lv_color_t __get_slider_gradient_color(float value)
{
    float ratio = value / NAV_TIME_MAX;
    
    uint8_t r = 216 + (uint8_t)((252 - 216) * ratio);
    uint8_t g = 226 + (uint8_t)((224 - 226) * ratio);
    uint8_t b = 236 + (uint8_t)((231 - 236) * ratio);
    
    return lv_color_make(r, g, b);
}

/**
 * @brief 设置WiFi状态
 */
void ui_navigation_set_network(char *wifi_icon)
{
    if (wifi_icon == NULL) {
        return;
    }
    
    // 更新navigation页面的WiFi图标
    if (sg_nav.nav_wifi_label) {
        lv_label_set_text(sg_nav.nav_wifi_label, wifi_icon);
    }
    
    PR_INFO("Navigation WiFi status updated: %s", wifi_icon);
} 