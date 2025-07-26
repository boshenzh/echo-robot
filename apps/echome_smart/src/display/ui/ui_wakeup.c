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
#define CIRCLE_BUTTON_SIZE_PRESSED  180    // Size when pressed
#define CIRCLE_BUTTON_RADIUS_PRESSED 90
#define CIRCLE_SHADOW_SIZE      180    // Shadow 20px larger than button
#define CIRCLE_SHADOW_RADIUS    90
#define BOOT_FADE_DURATION      1500  // 1.5 second fade from black to bright
#define BUTTON_SCALE_DURATION   150   // Button scale animation duration

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
 * @brief Boot fade animation execution callback - implements fade from black to bright
 */
static void __boot_fade_exec_cb(void *var, int32_t value)
{
    // value: 0-255, from transparent(0) to opaque(255)
    lv_obj_set_style_bg_opa(sg_ui.background, value, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_ui.circle_shadow, value * 0.6, LV_PART_MAIN);  // Shadow has lower opacity
    lv_obj_set_style_bg_opa(sg_ui.circle_button, value, LV_PART_MAIN);
    lv_obj_set_style_text_opa(sg_ui.wifi_label, value, LV_PART_MAIN);  // WiFi status display fades in
}

/**
 * @brief Boot fade animation completion callback
 */
static void __boot_fade_ready_cb(lv_anim_t *anim)
{
    sg_ui.boot_fade_completed = true;
    PR_INFO("Boot fade animation completed - wait page fully visible");
}

/**
 * @brief Button scale animation execution callback
 */
static void __button_scale_exec_cb(void *var, int32_t value)
{
    // value: 100-120, button scale percentage
    int32_t button_size = (CIRCLE_BUTTON_SIZE * value) / 100;
    int32_t button_radius = button_size / 2;
    
    // Only update button size, shadow remains fixed
    lv_obj_set_size(sg_ui.circle_button, button_size, button_size);
    lv_obj_set_style_radius(sg_ui.circle_button, button_radius, LV_PART_MAIN);
    
    // Re-center the button
    lv_obj_center(sg_ui.circle_button);
}

/**
 * @brief Button scale animation completion callback
 */
static void __button_scale_ready_cb(lv_anim_t *anim)
{
    if (sg_ui.is_button_pressed) {
        // If in pressed state, start scaling up
        lv_anim_set_values(&sg_ui.button_scale_anim, 100, 120);
        lv_anim_set_repeat_count(&sg_ui.button_scale_anim, 1);
        lv_anim_start(&sg_ui.button_scale_anim);
        sg_ui.is_button_pressed = false; // Reset state, next animation will be scale down
    }
}

/**
 * @brief Touch event callback
 */
static void __touch_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    
    // Ignore touch events before boot animation completes
    if (!sg_ui.boot_fade_completed) {
        return;
    }
    
    if (code == LV_EVENT_PRESSED) {
        PR_INFO("Button pressed - starting scale animation");
        
        // Stop current animation
        lv_anim_del(&sg_ui.circle_button, NULL);
        
        // Initialize animation
        lv_anim_init(&sg_ui.button_scale_anim);
        lv_anim_set_var(&sg_ui.button_scale_anim, &sg_ui.circle_button);
        lv_anim_set_exec_cb(&sg_ui.button_scale_anim, __button_scale_exec_cb);
        lv_anim_set_time(&sg_ui.button_scale_anim, BUTTON_SCALE_DURATION);
        lv_anim_set_ready_cb(&sg_ui.button_scale_anim, __button_scale_ready_cb);
        lv_anim_set_path_cb(&sg_ui.button_scale_anim, lv_anim_path_ease_out);
        
        // Start scale up animation
        sg_ui.is_button_pressed = true;
        lv_anim_set_values(&sg_ui.button_scale_anim, 100, 120);
        lv_anim_set_repeat_count(&sg_ui.button_scale_anim, 1);
        lv_anim_start(&sg_ui.button_scale_anim);
        
    } else if (code == LV_EVENT_RELEASED || code == LV_EVENT_PRESS_LOST) {
        PR_INFO("Button released - starting scale back and jumping to nav");
        
        // Stop current animation
        lv_anim_del(&sg_ui.circle_button, NULL);
        
        // Start scale down animation
        sg_ui.is_button_pressed = false;
        lv_anim_set_values(&sg_ui.button_scale_anim, 120, 100);
        lv_anim_set_repeat_count(&sg_ui.button_scale_anim, 1);
        lv_anim_start(&sg_ui.button_scale_anim);
        
        // Immediately jump to navigation page when finger is released
        ui_manager_show_navigation_page();
    }
}

/**
 * @brief Create container
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
 * @brief Create background
 */
static void __ui_create_background(void)
{
    sg_ui.background = lv_obj_create(sg_ui.container);
    lv_obj_set_size(sg_ui.background, LV_PCT(100), LV_PCT(100));
    lv_obj_set_pos(sg_ui.background, 0, 0);
    lv_obj_clear_flag(sg_ui.background, LV_OBJ_FLAG_SCROLLABLE);
    lv_obj_set_style_bg_color(sg_ui.background, lv_color_hex(0xD4F0F7), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_ui.background, LV_OPA_TRANSP, LV_PART_MAIN);  // Initially transparent
    lv_obj_set_style_border_width(sg_ui.background, 0, LV_PART_MAIN);
}

/**
 * @brief Create circular shadow
 */
static void __ui_create_circle_shadow(void)
{
    sg_ui.circle_shadow = lv_obj_create(sg_ui.container);
    lv_obj_set_size(sg_ui.circle_shadow, CIRCLE_SHADOW_SIZE, CIRCLE_SHADOW_SIZE);
    lv_obj_center(sg_ui.circle_shadow);
    lv_obj_clear_flag(sg_ui.circle_shadow, LV_OBJ_FLAG_SCROLLABLE);
    
    // Set shadow style
    lv_obj_set_style_bg_color(sg_ui.circle_shadow, lv_color_hex(0xE8F4FD), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_ui.circle_shadow, LV_OPA_TRANSP, LV_PART_MAIN);  // Initially transparent
    lv_obj_set_style_border_width(sg_ui.circle_shadow, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_ui.circle_shadow, CIRCLE_SHADOW_RADIUS, LV_PART_MAIN);
    
    // Add shadow effect
    lv_obj_set_style_shadow_width(sg_ui.circle_shadow, 20, LV_PART_MAIN);
    lv_obj_set_style_shadow_color(sg_ui.circle_shadow, lv_color_hex(0xA8D8EA), LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(sg_ui.circle_shadow, LV_OPA_30, LV_PART_MAIN);
    lv_obj_set_style_shadow_spread(sg_ui.circle_shadow, 5, LV_PART_MAIN);
    lv_obj_set_style_shadow_ofs_x(sg_ui.circle_shadow, 2, LV_PART_MAIN);
    lv_obj_set_style_shadow_ofs_y(sg_ui.circle_shadow, 3, LV_PART_MAIN);
}

/**
 * @brief Create circular button
 */
static void __ui_create_circle_button(void)
{
    sg_ui.circle_button = lv_obj_create(sg_ui.container);
    lv_obj_set_size(sg_ui.circle_button, CIRCLE_BUTTON_SIZE, CIRCLE_BUTTON_SIZE);
    lv_obj_center(sg_ui.circle_button);
    lv_obj_clear_flag(sg_ui.circle_button, LV_OBJ_FLAG_SCROLLABLE);
    
    // Set button style
    lv_obj_set_style_bg_color(sg_ui.circle_button, lv_color_hex(0xA8D8EA), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_ui.circle_button, LV_OPA_TRANSP, LV_PART_MAIN);  // Initially transparent
    lv_obj_set_style_border_width(sg_ui.circle_button, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_ui.circle_button, CIRCLE_BUTTON_RADIUS, LV_PART_MAIN);
    
    // Create button text
    sg_ui.button_label = lv_label_create(sg_ui.circle_button);
    lv_label_set_text(sg_ui.button_label, "Believe");
    lv_obj_set_style_text_color(sg_ui.button_label, lv_color_hex(0x333333), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_ui.button_label, &lv_font_montserrat_24, LV_PART_MAIN);
    lv_obj_center(sg_ui.button_label);
    
    // Add touch event (only for button)
    lv_obj_add_event_cb(sg_ui.circle_button, __touch_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(sg_ui.circle_button, __touch_event_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(sg_ui.circle_button, __touch_event_cb, LV_EVENT_PRESS_LOST, NULL);
}

/**
 * @brief Create WiFi status display
 */
static void __ui_create_wifi_status(void)
{
    sg_ui.wifi_label = lv_label_create(sg_ui.container);
    lv_label_set_text(sg_ui.wifi_label, FONT_AWESOME_WIFI_OFF);
    lv_obj_set_style_text_color(sg_ui.wifi_label, lv_color_hex(0x666666), LV_PART_MAIN);
    
    extern const lv_font_t font_awesome_16_4;
    lv_obj_set_style_text_font(sg_ui.wifi_label, &font_awesome_16_4, LV_PART_MAIN);
    
    lv_obj_set_style_text_opa(sg_ui.wifi_label, LV_OPA_TRANSP, LV_PART_MAIN);  // Initially transparent
    lv_obj_set_size(sg_ui.wifi_label, 30, 30);  // Set fixed size to ensure visibility
    lv_obj_align(sg_ui.wifi_label, LV_ALIGN_TOP_RIGHT, -15, 15);  // Top right, increase margin
    
    PR_INFO("WiFi label created on wait page");
}



/**
 * @brief Start fade animation from black to bright
 */
static void __start_boot_fade_animation(void)
{
    lv_anim_init(&sg_ui.boot_fade_anim);
    lv_anim_set_var(&sg_ui.boot_fade_anim, &sg_ui.background);
    lv_anim_set_exec_cb(&sg_ui.boot_fade_anim, __boot_fade_exec_cb);
    lv_anim_set_time(&sg_ui.boot_fade_anim, BOOT_FADE_DURATION);
    lv_anim_set_ready_cb(&sg_ui.boot_fade_anim, __boot_fade_ready_cb);
    lv_anim_set_path_cb(&sg_ui.boot_fade_anim, lv_anim_path_ease_out);
    
    // From transparent(0) to opaque(255)
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
    (void)ui_font; // wakeup page does not use font
    
    // Clear state
    memset(&sg_ui, 0, sizeof(UI_WAKEUP_T));
    sg_ui.current_state = WAKEUP_STATE_HIDDEN;
    sg_ui.boot_fade_completed = false;
    sg_ui.is_button_pressed = false;
    
    // Create UI components (order matters: background -> shadow -> button -> wifi)
    __ui_create_container();
    __ui_create_background();
    __ui_create_circle_shadow();
    __ui_create_circle_button();
    __ui_create_wifi_status();
    
    // Start fade animation from black to bright, then show wait state
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
    
    // Ensure button and shadow return to original size and position
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
    // Stop all animations
    lv_anim_del(&sg_ui.circle_button, NULL);
    lv_anim_del(&sg_ui, NULL);
    
    // Hide entire container
    lv_obj_add_flag(sg_ui.container, LV_OBJ_FLAG_HIDDEN);
    
    sg_ui.current_state = WAKEUP_STATE_HIDDEN;
    return 0;
}

/**
 * @brief Get current state
 */
int ui_wakeup_get_state(void)
{
    return sg_ui.current_state;
}

// UI interface functions (required by ui_display.h)
void ui_set_user_msg(const char *text)
{
    // wakeup page does not display user messages
}

void ui_set_assistant_msg(const char *text)
{
    // wakeup page does not display assistant messages
}

void ui_set_system_msg(const char *text)
{
    // wakeup page does not display system messages
}

void ui_set_emotion(const char *emotion)
{
    // Eyes function removed
}

void ui_set_status(const char *status)
{
    // Wakeup page does not need status display
}

void ui_set_notification(const char *notification)
{
    // Wakeup page does not need notification display
}

void ui_set_network(char *wifi_icon)
{
    if (wifi_icon == NULL) {
        return;
    }
    
    // Update WiFi icon on wait page
    if (sg_ui.wifi_label) {
        lv_label_set_text(sg_ui.wifi_label, wifi_icon);
    }
    
    PR_INFO("WiFi status updated: %s", wifi_icon);
}
    
void ui_set_chat_mode(const char *chat_mode)
{
    // Wakeup page does not need chat mode display
}



#endif 