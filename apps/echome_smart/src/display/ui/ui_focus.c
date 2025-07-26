#include "ui_focus.h"
#include "ui_manager.h"
#include "../font/font_awesome_symbols.h"
#include "tuya_log.h"
#include <stdio.h>
#include <math.h>

// Focus页面UI结构体
typedef struct {
    lv_obj_t *container;           // 页面容器
    lv_obj_t *background;          // 背景
    lv_obj_t *progress_ring;       // 圆环进度条
    lv_obj_t *time_label;          // 倒计时显示标签
    lv_obj_t *status_label;        // 状态显示标签
    lv_obj_t *stop_button;         // 停止/继续按钮
    lv_obj_t *stop_label;          // 停止/继续按钮文字
    lv_obj_t *finish_button;       // 完成按钮
    lv_obj_t *finish_label;        // 完成按钮文字
    lv_obj_t *wifi_label;          // WiFi状态显示
    lv_timer_t *timer;             // 倒计时定时器
    
    float total_time;              // 总专注时间（小时）
    float remaining_time;          // 剩余时间（小时）
    bool is_running;               // 是否正在倒计时
    bool is_paused;                // 是否暂停
} UI_FOCUS_T;

static UI_FOCUS_T sg_focus = {0};

// 前向声明
static void __ui_create_focus_container(void);
static void __ui_create_focus_background(void);
static void __ui_create_focus_progress_ring(void);
static void __ui_create_focus_time_label(void);
static void __ui_create_focus_status_label(void);
static void __ui_create_focus_stop_button(void);
static void __ui_create_focus_finish_button(void);
static void __ui_create_focus_wifi_status(void);
static void __focus_timer_cb(lv_timer_t *timer);
static void __stop_button_event_cb(lv_event_t *e);
static void __finish_button_event_cb(lv_event_t *e);
static void __update_time_display(void);
static void __update_progress_ring(void);

/**
 * @brief 初始化focus页面
 */
int ui_focus_init(UI_FONT_T *ui_font)
{
    (void)ui_font; // focus页面不使用字体
    
    // 清空状态
    memset(&sg_focus, 0, sizeof(UI_FOCUS_T));
    sg_focus.total_time = 1.0f;      // 默认1小时
    sg_focus.remaining_time = 1.0f;  // 默认1小时
    sg_focus.is_running = false;
    sg_focus.is_paused = false;
    
    // 创建UI组件
    __ui_create_focus_container();
    __ui_create_focus_background();
    __ui_create_focus_progress_ring();
    __ui_create_focus_time_label();
    __ui_create_focus_status_label();
    __ui_create_focus_stop_button();
    __ui_create_focus_finish_button();
    __ui_create_focus_wifi_status();
    
    // 初始隐藏
    lv_obj_add_flag(sg_focus.container, LV_OBJ_FLAG_HIDDEN);
    
    PR_INFO("Focus page initialized");
    return 0;
}

/**
 * @brief 显示focus页面
 */
void ui_focus_show(void)
{
    lv_obj_clear_flag(sg_focus.container, LV_OBJ_FLAG_HIDDEN);
    
    // 重置状态
    sg_focus.is_running = true;
    sg_focus.is_paused = false;
    sg_focus.remaining_time = sg_focus.total_time;
    
    // 重置UI显示
    lv_label_set_text(sg_focus.status_label, "");
    lv_label_set_text(sg_focus.stop_label, "Stop");
    
    // 创建定时器，每秒更新一次
    sg_focus.timer = lv_timer_create(__focus_timer_cb, 1000, NULL);
    
    // 更新显示
    __update_time_display();
    __update_progress_ring();
    
    PR_INFO("Focus page shown with %.1f hours", sg_focus.total_time);
}

/**
 * @brief 隐藏focus页面
 */
void ui_focus_hide(void)
{
    lv_obj_add_flag(sg_focus.container, LV_OBJ_FLAG_HIDDEN);
    
    // 停止定时器
    if (sg_focus.timer) {
        lv_timer_del(sg_focus.timer);
        sg_focus.timer = NULL;
    }
    
    sg_focus.is_running = false;
    sg_focus.is_paused = false;
    PR_INFO("Focus page hidden");
}

/**
 * @brief 设置专注时间
 */
void ui_focus_set_time(float time)
{
    sg_focus.total_time = time;
    sg_focus.remaining_time = time;
    
    if (sg_focus.is_running) {
        __update_time_display();
        __update_progress_ring();
    }
    
    PR_INFO("Focus time set to %.1f hours", time);
}

/**
 * @brief 创建focus页面容器
 */
static void __ui_create_focus_container(void)
{
    sg_focus.container = lv_obj_create(lv_scr_act());
    lv_obj_set_size(sg_focus.container, LV_PCT(100), LV_PCT(100));
    lv_obj_set_pos(sg_focus.container, 0, 0);
    lv_obj_clear_flag(sg_focus.container, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(sg_focus.container, lv_color_black(), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_focus.container, LV_OPA_COVER, LV_PART_MAIN);
}

/**
 * @brief 创建focus页面背景
 */
static void __ui_create_focus_background(void)
{
    sg_focus.background = lv_obj_create(sg_focus.container);
    lv_obj_set_size(sg_focus.background, LV_PCT(100), LV_PCT(100));
    lv_obj_set_pos(sg_focus.background, 0, 0);
    lv_obj_clear_flag(sg_focus.background, LV_OBJ_FLAG_SCROLLABLE);
    // 使用nav页面的背景色
    lv_obj_set_style_bg_color(sg_focus.background, lv_color_hex(0xD8E2EC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_focus.background, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_focus.background, 0, LV_PART_MAIN);
}

/**
 * @brief 创建focus页面圆环进度条
 */
static void __ui_create_focus_progress_ring(void)
{
    sg_focus.progress_ring = lv_arc_create(sg_focus.container);
    lv_obj_set_size(sg_focus.progress_ring, 200, 200);
    lv_obj_align(sg_focus.progress_ring, LV_ALIGN_CENTER, 0, -20);
    
    // 设置圆环样式
    lv_arc_set_range(sg_focus.progress_ring, 0, 100);
    lv_arc_set_value(sg_focus.progress_ring, 100);
    lv_arc_set_bg_angles(sg_focus.progress_ring, 0, 360);
    
    // 设置圆环颜色 - 使用统一颜色
    lv_obj_set_style_arc_color(sg_focus.progress_ring, lv_color_hex(0xE0E0E0), LV_PART_MAIN);  // 背景圆环
    lv_obj_set_style_arc_color(sg_focus.progress_ring, lv_color_hex(0x529ACC), LV_PART_INDICATOR);  // 进度圆环
    lv_obj_set_style_arc_width(sg_focus.progress_ring, 8, LV_PART_MAIN);
    lv_obj_set_style_arc_width(sg_focus.progress_ring, 8, LV_PART_INDICATOR);
    
    // 隐藏圆环的旋钮
    lv_obj_set_style_arc_width(sg_focus.progress_ring, 0, LV_PART_KNOB);
}

/**
 * @brief 创建focus页面时间显示标签
 */
static void __ui_create_focus_time_label(void)
{
    sg_focus.time_label = lv_label_create(sg_focus.container);
    lv_obj_set_style_text_color(sg_focus.time_label, lv_color_hex(0x333333), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_focus.time_label, &lv_font_montserrat_24, LV_PART_MAIN);
    lv_obj_align(sg_focus.time_label, LV_ALIGN_CENTER, 0, -20);
    
    // 设置初始文本
    lv_label_set_text(sg_focus.time_label, "01:00:00");
}

/**
 * @brief 创建focus页面状态显示标签
 */
static void __ui_create_focus_status_label(void)
{
    sg_focus.status_label = lv_label_create(sg_focus.container);
    lv_obj_set_style_text_color(sg_focus.status_label, lv_color_hex(0x666666), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_focus.status_label, &lv_font_montserrat_14, LV_PART_MAIN);
    lv_obj_align(sg_focus.status_label, LV_ALIGN_CENTER, 0, 80);
    
    // 不显示状态文本
    lv_label_set_text(sg_focus.status_label, "");
}

/**
 * @brief focus页面停止/继续按钮
 */
static void __ui_create_focus_stop_button(void)
{
    sg_focus.stop_button = lv_obj_create(sg_focus.container);
    lv_obj_set_size(sg_focus.stop_button, 80, 40);
    lv_obj_align(sg_focus.stop_button, LV_ALIGN_CENTER, -60, 120);  
    lv_obj_clear_flag(sg_focus.stop_button, LV_OBJ_FLAG_SCROLLABLE);
    

    lv_obj_set_style_bg_color(sg_focus.stop_button, lv_color_hex(0x529ACC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_focus.stop_button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_focus.stop_button, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_focus.stop_button, 20, LV_PART_MAIN);
    
    // 停止按钮文字
    sg_focus.stop_label = lv_label_create(sg_focus.stop_button);
    lv_label_set_text(sg_focus.stop_label, "Stop");
    lv_obj_set_style_text_color(sg_focus.stop_label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_focus.stop_label, &lv_font_montserrat_14, LV_PART_MAIN);
    lv_obj_center(sg_focus.stop_label);
    
    // 停止按钮点击事件
    lv_obj_add_event_cb(sg_focus.stop_button, __stop_button_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(sg_focus.stop_button, __stop_button_event_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(sg_focus.stop_button, __stop_button_event_cb, LV_EVENT_PRESS_LOST, NULL);
}

/**
 * @brief focus页面完成按钮
 */
static void __ui_create_focus_finish_button(void)
{
    sg_focus.finish_button = lv_obj_create(sg_focus.container);
    lv_obj_set_size(sg_focus.finish_button, 80, 40);
    lv_obj_align(sg_focus.finish_button, LV_ALIGN_CENTER, 60, 120);  // 向右放置
    lv_obj_clear_flag(sg_focus.finish_button, LV_OBJ_FLAG_SCROLLABLE);
    
    // 完成按钮样式 
    lv_obj_set_style_bg_color(sg_focus.finish_button, lv_color_hex(0x529ACC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_focus.finish_button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_focus.finish_button, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_focus.finish_button, 20, LV_PART_MAIN);
    
    // 完成按钮文字
    sg_focus.finish_label = lv_label_create(sg_focus.finish_button);
    lv_label_set_text(sg_focus.finish_label, "Finish");
    lv_obj_set_style_text_color(sg_focus.finish_label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_focus.finish_label, &lv_font_montserrat_14, LV_PART_MAIN);
    lv_obj_center(sg_focus.finish_label);
    
    // 完成按钮点击事件
    lv_obj_add_event_cb(sg_focus.finish_button, __finish_button_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(sg_focus.finish_button, __finish_button_event_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(sg_focus.finish_button, __finish_button_event_cb, LV_EVENT_PRESS_LOST, NULL);
}

/**
 * @brief focus页面WiFi状态显示
 */
static void __ui_create_focus_wifi_status(void)
{
    sg_focus.wifi_label = lv_label_create(sg_focus.container);
    lv_label_set_text(sg_focus.wifi_label, FONT_AWESOME_WIFI_OFF);
    lv_obj_set_style_text_color(sg_focus.wifi_label, lv_color_hex(0x666666), LV_PART_MAIN);
    
    extern const lv_font_t font_awesome_16_4;
    lv_obj_set_style_text_font(sg_focus.wifi_label, &font_awesome_16_4, LV_PART_MAIN);
    
    lv_obj_set_size(sg_focus.wifi_label, 30, 30);  // 设置固定大小确保可见
    lv_obj_align(sg_focus.wifi_label, LV_ALIGN_TOP_RIGHT, -15, 15);  // 与其他页面保持一致
}

/**
 * @brief 倒计时定时器回调
 */
static void __focus_timer_cb(lv_timer_t *timer)
{
    (void)timer;
    
    if (!sg_focus.is_running || sg_focus.is_paused) {
        return;
    }
    
    // 减少剩余时间（每秒减少1/3600小时）
    sg_focus.remaining_time -= 1.0f / 3600.0f;
    
    if (sg_focus.remaining_time <= 0) {
        // 倒计时结束
        sg_focus.remaining_time = 0;
        sg_focus.is_running = false;
        
        // 停止定时器
        if (sg_focus.timer) {
            lv_timer_del(sg_focus.timer);
            sg_focus.timer = NULL;
        }
        
        // 更新状态显示
        lv_label_set_text(sg_focus.status_label, "Time's Up!");
        lv_label_set_text(sg_focus.stop_label, "Done");
        lv_label_set_text(sg_focus.finish_label, "Done");
        
        PR_INFO("Focus session completed");
    }
    
    // 更新显示
    __update_time_display();
    __update_progress_ring();
}

/**
 * @brief 停止/继续按钮事件回调
 */
static void __stop_button_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    
    if (code == LV_EVENT_PRESSED) {
        PR_INFO("Stop/Continue button pressed");
        
    } else if (code == LV_EVENT_RELEASED || code == LV_EVENT_PRESS_LOST) {
        PR_INFO("Stop/Continue button released");
        
        if (sg_focus.is_paused) {
            // 如果已暂停，继续倒计时
            PR_INFO("Continuing focus session");
            sg_focus.is_paused = false;
            sg_focus.is_running = true;
            
            // 重新创建定时器
            sg_focus.timer = lv_timer_create(__focus_timer_cb, 1000, NULL);
            
            // 更新按钮文字和状态
            lv_label_set_text(sg_focus.stop_label, "Stop");
            lv_label_set_text(sg_focus.status_label, "");
            
        } else if (sg_focus.is_running) {
            // 如果正在倒计时，暂停
            PR_INFO("Pausing focus session");
            sg_focus.is_paused = true;
            sg_focus.is_running = false;
            
            // 停止定时器
            if (sg_focus.timer) {
                lv_timer_del(sg_focus.timer);
                sg_focus.timer = NULL;
            }
            
            // 更新按钮文字和状态
            lv_label_set_text(sg_focus.stop_label, "Continue");
            lv_label_set_text(sg_focus.status_label, "");
            
        } else {
            // 如果倒计时已结束，返回导航页面
            PR_INFO("Focus session completed, returning to navigation");
            ui_manager_show_navigation_page();
        }
    }
}

/**
 * @brief 完成按钮事件回调
 */
static void __finish_button_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    
    if (code == LV_EVENT_PRESSED) {
        PR_INFO("Finish button pressed");
        
    } else if (code == LV_EVENT_RELEASED || code == LV_EVENT_PRESS_LOST) {
        PR_INFO("Finish button released");
        
        // 停止定时器
        if (sg_focus.timer) {
            lv_timer_del(sg_focus.timer);
            sg_focus.timer = NULL;
        }
        
        // 重置状态
        sg_focus.is_running = false;
        sg_focus.is_paused = false;
        
        // 更新状态显示
        lv_label_set_text(sg_focus.status_label, "Finished");
        lv_label_set_text(sg_focus.stop_label, "Done");
        
        PR_INFO("Focus session finished by user");
        
        // 返回导航页面
        ui_manager_show_navigation_page();
    }
}

/**
 * @brief 更新时间显示
 */
static void __update_time_display(void)
{
    if (!sg_focus.time_label) {
        return;
    }
    

    int total_seconds = (int)(sg_focus.remaining_time * 3600);
    int hours = total_seconds / 3600;
    int minutes = (total_seconds % 3600) / 60;
    int seconds = total_seconds % 60;
    
    char time_str[16];
    sprintf(time_str, "%02d:%02d:%02d", hours, minutes, seconds);
    lv_label_set_text(sg_focus.time_label, time_str);
}

/**
 * @brief 更新圆环进度条
 */
static void __update_progress_ring(void)
{
    if (!sg_focus.progress_ring) {
        return;
    }
    
    // 计算进度百分比
    float progress = 0.0f;
    if (sg_focus.total_time > 0) {
        progress = (sg_focus.remaining_time / sg_focus.total_time) * 100.0f;
    }
    
    // 设置圆环进度
    lv_arc_set_value(sg_focus.progress_ring, (int16_t)progress);
}

/**
 * @brief 设置WiFi状态
 */
void ui_focus_set_network(char *wifi_icon)
{
    if (wifi_icon == NULL) {
        return;
    }
    
    // focus页面的WiFi图标
    if (sg_focus.wifi_label) {
        lv_label_set_text(sg_focus.wifi_label, wifi_icon);
    }
    
    PR_INFO("Focus WiFi status updated: %s", wifi_icon);
} 