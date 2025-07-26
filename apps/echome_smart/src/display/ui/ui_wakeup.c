/**
 * @file ui_wakeup.c
 * @version 0.1
 * @date 2025-06-13
 */

#include "tuya_cloud_types.h"
#include "tal_api.h"

#if defined(ENABLE_GUI_WAKEUP) && (ENABLE_GUI_WAKEUP == 1)
#include "ui_display.h"
#include "ui_wakeup.h"
#include "ui_manager.h"
#include "app_display.h"

#include "lvgl.h"
#include <stdio.h>  
#include "font_awesome_symbols.h"

/***********************************************************
************************macro define************************
***********************************************************/
#define CIRCLE_BUTTON_SIZE      160
#define CIRCLE_BUTTON_RADIUS    80
#define CIRCLE_BUTTON_SIZE_PRESSED  180    // 点击时放大的尺寸
#define CIRCLE_BUTTON_RADIUS_PRESSED 90
#define CIRCLE_SHADOW_SIZE      180    // 阴影比按钮大20px
#define CIRCLE_SHADOW_RADIUS    90
#define BOOT_FADE_DURATION      1500  // 1.5秒从黑到亮的渐变时间
#define BUTTON_SCALE_DURATION   150   // 按钮缩放动画时长

/***********************************************************
***********************typedef define***********************
***********************************************************/
typedef struct {
    lv_obj_t *container;
    lv_obj_t *background;
    lv_obj_t *circle_shadow;      
    lv_obj_t *circle_button;
    lv_obj_t *button_label;
    lv_obj_t *wifi_label;
    
    lv_anim_t boot_fade_anim;
    lv_anim_t button_scale_anim;
    WAKEUP_STATE_E current_state;
    bool boot_fade_completed;
    bool is_button_pressed;
} UI_WAKEUP_T;

/***********************************************************
***********************variable define**********************
***********************************************************/
static UI_WAKEUP_T sg_ui;

/***********************************************************
***********************function define**********************
***********************************************************/

/**
 * @brief 启动渐变动画执行回调 - 实现从黑到亮的效果
 */
static void __boot_fade_exec_cb(void *var, int32_t value)
{
    // value: 0-255，从透明(0)到不透明(255)
    lv_obj_set_style_bg_opa(sg_ui.background, value, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_ui.circle_shadow, value * 0.6, LV_PART_MAIN);  // 阴影透明度更低
    lv_obj_set_style_bg_opa(sg_ui.circle_button, value, LV_PART_MAIN);
    lv_obj_set_style_text_opa(sg_ui.wifi_label, value, LV_PART_MAIN);  // wifi状态显示渐现
}

/**
 * @brief 启动渐变动画完成回调
 */
static void __boot_fade_ready_cb(lv_anim_t *anim)
{
    sg_ui.boot_fade_completed = true;
    PR_INFO("Boot fade animation completed - wait page fully visible");
}

/**
 * @brief 按钮缩放动画执行回调
 */
static void __button_scale_exec_cb(void *var, int32_t value)
{
    // value: 100-120，按钮缩放百分比
    int32_t button_size = (CIRCLE_BUTTON_SIZE * value) / 100;
    int32_t button_radius = button_size / 2;
    
    // 只更新按钮的大小，阴影保持固定
    lv_obj_set_size(sg_ui.circle_button, button_size, button_size);
    lv_obj_set_style_radius(sg_ui.circle_button, button_radius, LV_PART_MAIN);
    
    // 重新居中对齐按钮
    lv_obj_center(sg_ui.circle_button);
}

/**
 * @brief 按钮缩放动画完成回调
 */
static void __button_scale_ready_cb(lv_anim_t *anim)
{
    if (sg_ui.is_button_pressed) {
        // 如果是按下状态，开始放大
        lv_anim_set_values(&sg_ui.button_scale_anim, 100, 120);
        lv_anim_set_repeat_count(&sg_ui.button_scale_anim, 1);
        lv_anim_start(&sg_ui.button_scale_anim);
        sg_ui.is_button_pressed = false; // 重置状态，下次动画将是缩回
    }
}

/**
 * @brief 触摸事件回调
 */
static void __touch_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    
    // 在开机动画完成前忽略触摸事件
    if (!sg_ui.boot_fade_completed) {
        return;
    }
    
    if (code == LV_EVENT_PRESSED) {
        PR_INFO("Button pressed - starting scale animation");
        
        // 停止当前动画
        lv_anim_del(&sg_ui.circle_button, NULL);
        
        // 初始化动画
        lv_anim_init(&sg_ui.button_scale_anim);
        lv_anim_set_var(&sg_ui.button_scale_anim, &sg_ui.circle_button);
        lv_anim_set_exec_cb(&sg_ui.button_scale_anim, __button_scale_exec_cb);
        lv_anim_set_time(&sg_ui.button_scale_anim, BUTTON_SCALE_DURATION);
        lv_anim_set_ready_cb(&sg_ui.button_scale_anim, __button_scale_ready_cb);
        lv_anim_set_path_cb(&sg_ui.button_scale_anim, lv_anim_path_ease_out);
        
        // 开始放大动画
        sg_ui.is_button_pressed = true;
        lv_anim_set_values(&sg_ui.button_scale_anim, 100, 120);
        lv_anim_set_repeat_count(&sg_ui.button_scale_anim, 1);
        lv_anim_start(&sg_ui.button_scale_anim);
        
    } else if (code == LV_EVENT_RELEASED || code == LV_EVENT_PRESS_LOST) {
        PR_INFO("Button released - starting scale back and jumping to nav");
        
        // 停止当前动画
        lv_anim_del(&sg_ui.circle_button, NULL);
        
        // 开始缩回动画
        sg_ui.is_button_pressed = false;
        lv_anim_set_values(&sg_ui.button_scale_anim, 120, 100);
        lv_anim_set_repeat_count(&sg_ui.button_scale_anim, 1);
        lv_anim_start(&sg_ui.button_scale_anim);
        
        // 手指松开立即跳转到navigation页面
        ui_manager_show_navigation_page();
    }
}

/**
 * @brief 创建容器
 */
static void __ui_create_container(void)
{
    sg_ui.container = lv_obj_create(lv_scr_act());
    lv_obj_set_size(sg_ui.container, LV_PCT(100), LV_PCT(100));
    lv_obj_set_pos(sg_ui.container, 0, 0);
    lv_obj_clear_flag(sg_ui.container, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(sg_ui.container, lv_color_black(), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_ui.container, LV_OPA_COVER, LV_PART_MAIN);
}

/**
 * @brief 创建背景
 */
static void __ui_create_background(void)
{
    sg_ui.background = lv_obj_create(sg_ui.container);
    lv_obj_set_size(sg_ui.background, LV_PCT(100), LV_PCT(100));
    lv_obj_set_pos(sg_ui.background, 0, 0);
    lv_obj_clear_flag(sg_ui.background, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(sg_ui.background, lv_color_hex(0xD4F0F7), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_ui.background, LV_OPA_TRANSP, LV_PART_MAIN);  // 初始透明
    lv_obj_set_style_border_width(sg_ui.background, 0, LV_PART_MAIN);
}

/**
 * @brief 创建圆形阴影
 */
static void __ui_create_circle_shadow(void)
{
    sg_ui.circle_shadow = lv_obj_create(sg_ui.container);
    lv_obj_set_size(sg_ui.circle_shadow, CIRCLE_SHADOW_SIZE, CIRCLE_SHADOW_SIZE);
    lv_obj_center(sg_ui.circle_shadow);
    lv_obj_clear_flag(sg_ui.circle_shadow, LV_OBJ_FLAG_SCROLLABLE);
    
    // 设置阴影样式
    lv_obj_set_style_bg_color(sg_ui.circle_shadow, lv_color_hex(0xE8F4FD), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_ui.circle_shadow, LV_OPA_TRANSP, LV_PART_MAIN);  // 初始透明
    lv_obj_set_style_border_width(sg_ui.circle_shadow, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_ui.circle_shadow, CIRCLE_SHADOW_RADIUS, LV_PART_MAIN);
    
    // 添加阴影效果
    lv_obj_set_style_shadow_width(sg_ui.circle_shadow, 20, LV_PART_MAIN);
    lv_obj_set_style_shadow_color(sg_ui.circle_shadow, lv_color_hex(0xA8D8EA), LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(sg_ui.circle_shadow, LV_OPA_30, LV_PART_MAIN);
    lv_obj_set_style_shadow_spread(sg_ui.circle_shadow, 5, LV_PART_MAIN);
    lv_obj_set_style_shadow_ofs_x(sg_ui.circle_shadow, 2, LV_PART_MAIN);
    lv_obj_set_style_shadow_ofs_y(sg_ui.circle_shadow, 3, LV_PART_MAIN);
}

/**
 * @brief 创建圆形按钮
 */
static void __ui_create_circle_button(void)
{
    sg_ui.circle_button = lv_obj_create(sg_ui.container);
    lv_obj_set_size(sg_ui.circle_button, CIRCLE_BUTTON_SIZE, CIRCLE_BUTTON_SIZE);
    lv_obj_center(sg_ui.circle_button);
    lv_obj_clear_flag(sg_ui.circle_button, LV_OBJ_FLAG_SCROLLABLE);
    
    // 设置按钮样式
    lv_obj_set_style_bg_color(sg_ui.circle_button, lv_color_hex(0xA8D8EA), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_ui.circle_button, LV_OPA_TRANSP, LV_PART_MAIN);  // 初始透明
    lv_obj_set_style_border_width(sg_ui.circle_button, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_ui.circle_button, CIRCLE_BUTTON_RADIUS, LV_PART_MAIN);
    
    // 创建按钮文字
    sg_ui.button_label = lv_label_create(sg_ui.circle_button);
    lv_label_set_text(sg_ui.button_label, "Believe");
    lv_obj_set_style_text_color(sg_ui.button_label, lv_color_hex(0x333333), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_ui.button_label, &lv_font_montserrat_24, LV_PART_MAIN);
    lv_obj_center(sg_ui.button_label);
    
    // 添加触摸事件（只对按钮有效）
    lv_obj_add_event_cb(sg_ui.circle_button, __touch_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(sg_ui.circle_button, __touch_event_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(sg_ui.circle_button, __touch_event_cb, LV_EVENT_PRESS_LOST, NULL);
}

/**
 * @brief 创建wifi状态显示
 */
static void __ui_create_wifi_status(void)
{
    sg_ui.wifi_label = lv_label_create(sg_ui.container);
    lv_label_set_text(sg_ui.wifi_label, FONT_AWESOME_WIFI_OFF);
    lv_obj_set_style_text_color(sg_ui.wifi_label, lv_color_hex(0x666666), LV_PART_MAIN);
    
    extern const lv_font_t font_awesome_16_4;
    lv_obj_set_style_text_font(sg_ui.wifi_label, &font_awesome_16_4, LV_PART_MAIN);
    
    lv_obj_set_style_text_opa(sg_ui.wifi_label, LV_OPA_TRANSP, LV_PART_MAIN);  // 初始透明
    lv_obj_set_size(sg_ui.wifi_label, 30, 30);  // 设置固定大小确保可见
    lv_obj_align(sg_ui.wifi_label, LV_ALIGN_TOP_RIGHT, -15, 15);  // 右上角，增大边距
    
    PR_INFO("WiFi label created on wait page");
}



/**
 * @brief 启动从黑到亮的渐变动画
 */
static void __start_boot_fade_animation(void)
{
    lv_anim_init(&sg_ui.boot_fade_anim);
    lv_anim_set_var(&sg_ui.boot_fade_anim, &sg_ui.background);
    lv_anim_set_exec_cb(&sg_ui.boot_fade_anim, __boot_fade_exec_cb);
    lv_anim_set_time(&sg_ui.boot_fade_anim, BOOT_FADE_DURATION);
    lv_anim_set_ready_cb(&sg_ui.boot_fade_anim, __boot_fade_ready_cb);
    lv_anim_set_path_cb(&sg_ui.boot_fade_anim, lv_anim_path_ease_out);
    
    // 从透明(0)到不透明(255)
    lv_anim_set_values(&sg_ui.boot_fade_anim, 0, 255);
    lv_anim_set_repeat_count(&sg_ui.boot_fade_anim, 1);
    lv_anim_start(&sg_ui.boot_fade_anim);
    
    PR_INFO("Boot fade animation started");
}

/**
 * @brief Initialize wakeup UI
 */
int ui_wakeup_init(UI_FONT_T *ui_font)
{
    (void)ui_font; // wakeup页面不使用字体
    
    // 清空状态
    memset(&sg_ui, 0, sizeof(UI_WAKEUP_T));
    sg_ui.current_state = WAKEUP_STATE_HIDDEN;
    sg_ui.boot_fade_completed = false;
    sg_ui.is_button_pressed = false;
    
    // 创建UI组件（顺序很重要：背景 -> 阴影 -> 按钮 -> wifi）
    __ui_create_container();
    __ui_create_background();
    __ui_create_circle_shadow();
    __ui_create_circle_button();
    __ui_create_wifi_status();
    
    // 启动从黑到亮的渐变动画，然后显示wait状态
    __start_boot_fade_animation();
    sg_ui.current_state = WAKEUP_STATE_WAIT;
    
    PR_INFO("Wakeup UI initialized");
    return 0;
}

/**
 * @brief Initialize UI
 */
int ui_init(UI_FONT_T *ui_font)
{
    return ui_wakeup_init(ui_font);
}

/**
 * @brief Show wait page
 */
int ui_wakeup_show_wait(void)
{
    if (sg_ui.current_state == WAKEUP_STATE_HIDDEN) {
        lv_obj_clear_flag(sg_ui.container, LV_OBJ_FLAG_HIDDEN);
        sg_ui.current_state = WAKEUP_STATE_WAIT;
        PR_INFO("Wait page shown");
    }
    
    // 确保按钮和阴影回到原始大小和位置
    lv_obj_set_size(sg_ui.circle_button, CIRCLE_BUTTON_SIZE, CIRCLE_BUTTON_SIZE);
    lv_obj_set_style_radius(sg_ui.circle_button, CIRCLE_BUTTON_RADIUS, LV_PART_MAIN);
    lv_obj_center(sg_ui.circle_button);
    
    lv_obj_set_size(sg_ui.circle_shadow, CIRCLE_SHADOW_SIZE, CIRCLE_SHADOW_SIZE);
    lv_obj_set_style_radius(sg_ui.circle_shadow, CIRCLE_SHADOW_RADIUS, LV_PART_MAIN);
    lv_obj_center(sg_ui.circle_shadow);
    
    return 0;
}

/**
 * @brief Hide wakeup UI
 */
int ui_wakeup_hide(void)
{
    // 停止所有动画
    lv_anim_del(&sg_ui.circle_button, NULL);
    lv_anim_del(&sg_ui, NULL);
    
    // 隐藏整个容器
    lv_obj_add_flag(sg_ui.container, LV_OBJ_FLAG_HIDDEN);
    
    sg_ui.current_state = WAKEUP_STATE_HIDDEN;
    return 0;
}

/**
 * @brief 获取当前状态
 */
int ui_wakeup_get_state(void)
{
    return sg_ui.current_state;
}

// UI interface functions (required by ui_display.h)
void ui_set_user_msg(const char *text)
{
    // wakeup页面不显示用户消息
}

void ui_set_assistant_msg(const char *text)
{
    // wakeup页面不显示助手消息
}

void ui_set_system_msg(const char *text)
{
    // wakeup页面不显示系统消息
}

void ui_set_emotion(const char *emotion)
{
    // Eyes功能已删除
}

void ui_set_status(const char *status)
{
    // Wakeup页面不需要状态显示
}

void ui_set_notification(const char *notification)
{
    // Wakeup页面不需要通知显示
}

void ui_set_network(char *wifi_icon)
{
    if (wifi_icon == NULL) {
        return;
    }
    
    // 更新wait页面的WiFi图标
    if (sg_ui.wifi_label) {
        lv_label_set_text(sg_ui.wifi_label, wifi_icon);
    }
    
    PR_INFO("WiFi status updated: %s", wifi_icon);
}
    
void ui_set_chat_mode(const char *chat_mode)
{
    // Wakeup页面不需要聊天模式显示
}



#endif 