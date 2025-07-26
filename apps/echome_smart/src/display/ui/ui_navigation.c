#include "ui_navigation.h"
#include "ui_manager.h"
#include "ui_focus.h"
#include "font_awesome_symbols.h"
#include "tuya_log.h"
#include "tal_api.h"
#include <stdio.h>

// Navigation page related macro definitions
#define NAV_START_BUTTON_SIZE 120
#define NAV_START_BUTTON_RADIUS 60
#define NAV_SLIDER_WIDTH 200
#define NAV_SLIDER_HEIGHT 30
#define NAV_TIME_MIN 0.0f
#define NAV_TIME_MAX 2.0f

// Navigation page UI structure
typedef struct {
    lv_obj_t *container;           // Page container
    lv_obj_t *background;          // Background
    lv_obj_t *nav_start_button;    // Start button
    lv_obj_t *nav_start_label;     // Start button text
    lv_obj_t *nav_time_slider;     // Time slider
    lv_obj_t *nav_time_label;      // Time display label
    lv_obj_t *nav_wifi_label;      // WiFi status display
    
    float selected_time;               // Selected focus time (hours)
} UI_NAVIGATION_T;

static UI_NAVIGATION_T sg_nav = {0};

// Forward declarations
static void __ui_create_navigation_container(void);
static void __ui_create_navigation_background(void);
static void __ui_create_navigation_start_button(void);
static void __ui_create_navigation_time_slider(void);
static void __ui_create_navigation_wifi_status(void);
static void __start_button_event_cb(lv_event_t *e);
static void __time_slider_event_cb(lv_event_t *e);
static lv_color_t __get_slider_gradient_color(float value);

/**
 * @brief Initialize navigation page
 */
int ui_navigation_init(UI_FONT_T *ui_font)
{
    (void)ui_font; // Navigation page doesn't use fonts
    
    // Clear state
    memset(&sg_nav, 0, sizeof(UI_NAVIGATION_T));
    sg_nav.selected_time = 1.0f;  // Default 1 hour
    
    // Create UI components
    __ui_create_navigation_container();
    __ui_create_navigation_background();
    __ui_create_navigation_start_button();
    __ui_create_navigation_time_slider();
    __ui_create_navigation_wifi_status();
    
    // Initially hidden
    lv_obj_add_flag(sg_nav.container, LV_OBJ_FLAG_HIDDEN);
    
    PR_INFO("Navigation page initialized");
    return 0;
}

/**
 * @brief Show navigation page
 */
void ui_navigation_show(void)
{
    lv_obj_clear_flag(sg_nav.container, LV_OBJ_FLAG_HIDDEN);
    PR_INFO("Navigation page shown");
}

/**
 * @brief Hide navigation page
 */
void ui_navigation_hide(void)
{
    lv_obj_add_flag(sg_nav.container, LV_OBJ_FLAG_HIDDEN);
    PR_INFO("Navigation page hidden");
}

/**
 * @brief Get selected focus time
 */
float ui_navigation_get_selected_time(void)
{
    return sg_nav.selected_time;
}

/**
 * @brief Set focus time
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
 * @brief Create navigation page container
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
 * @brief Create navigation page background
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
 * @brief Create start button
 */
static void __ui_create_navigation_start_button(void)
{
    sg_nav.nav_start_button = lv_obj_create(sg_nav.container);
    lv_obj_set_size(sg_nav.nav_start_button, NAV_START_BUTTON_SIZE, NAV_START_BUTTON_SIZE);
    lv_obj_align(sg_nav.nav_start_button, LV_ALIGN_CENTER, 0, -30);  // button coordinates
    lv_obj_clear_flag(sg_nav.nav_start_button, LV_OBJ_FLAG_SCROLLABLE);
    
    // Set start button style
    lv_obj_set_style_bg_color(sg_nav.nav_start_button, lv_color_hex(0x529ACC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_nav.nav_start_button, LV_OPA_30, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_nav.nav_start_button, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_nav.nav_start_button, NAV_START_BUTTON_RADIUS, LV_PART_MAIN);
    
    // Create start button text
    sg_nav.nav_start_label = lv_label_create(sg_nav.nav_start_button);
    lv_label_set_text(sg_nav.nav_start_label, "Start");
    lv_obj_set_style_text_color(sg_nav.nav_start_label, lv_color_hex(0x333333), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_nav.nav_start_label, &lv_font_montserrat_24, LV_PART_MAIN);
    lv_obj_center(sg_nav.nav_start_label);
    
    // Add start button click event
    lv_obj_add_event_cb(sg_nav.nav_start_button, __start_button_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(sg_nav.nav_start_button, __start_button_event_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(sg_nav.nav_start_button, __start_button_event_cb, LV_EVENT_PRESS_LOST, NULL);
}

/**
 * @brief Create time slider
 */
static void __ui_create_navigation_time_slider(void)
{
    sg_nav.nav_time_slider = lv_slider_create(sg_nav.container);
    lv_obj_set_size(sg_nav.nav_time_slider, NAV_SLIDER_WIDTH, NAV_SLIDER_HEIGHT);
    lv_obj_align(sg_nav.nav_time_slider, LV_ALIGN_BOTTOM_MID, 0, -40);
    lv_slider_set_range(sg_nav.nav_time_slider, 0, 100);
    lv_slider_set_value(sg_nav.nav_time_slider, 50, LV_ANIM_OFF);  // Default 1.0 hour
    
    // Set slider style
    lv_obj_set_style_bg_color(sg_nav.nav_time_slider, lv_color_hex(0xE0E0E0), LV_PART_MAIN);
    lv_obj_set_style_bg_color(sg_nav.nav_time_slider, lv_color_hex(0xB0DAF0), LV_PART_INDICATOR);
    lv_obj_set_style_bg_color(sg_nav.nav_time_slider, lv_color_hex(0x529ACC), LV_PART_KNOB);
    
    // Add slider events
    lv_obj_add_event_cb(sg_nav.nav_time_slider, __time_slider_event_cb, LV_EVENT_VALUE_CHANGED, NULL);
    lv_obj_add_event_cb(sg_nav.nav_time_slider, __time_slider_event_cb, LV_EVENT_PRESSING, NULL);
    
    // Create time display label
    sg_nav.nav_time_label = lv_label_create(sg_nav.container);
    lv_obj_set_style_text_color(sg_nav.nav_time_label, lv_color_hex(0x333333), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_nav.nav_time_label, &lv_font_montserrat_14, LV_PART_MAIN);
    lv_obj_align(sg_nav.nav_time_label, LV_ALIGN_BOTTOM_MID, 0, -80);
    
    // Set initial time display
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
 * @brief Create navigation page WiFi status display
 */
static void __ui_create_navigation_wifi_status(void)
{
    sg_nav.nav_wifi_label = lv_label_create(sg_nav.container);
    lv_label_set_text(sg_nav.nav_wifi_label, FONT_AWESOME_WIFI_OFF);
    lv_obj_set_style_text_color(sg_nav.nav_wifi_label, lv_color_hex(0x666666), LV_PART_MAIN);
    
    extern const lv_font_t font_awesome_16_4;
    lv_obj_set_style_text_font(sg_nav.nav_wifi_label, &font_awesome_16_4, LV_PART_MAIN);
    
    lv_obj_set_size(sg_nav.nav_wifi_label, 30, 30);  // Set fixed size to ensure visibility
    lv_obj_align(sg_nav.nav_wifi_label, LV_ALIGN_TOP_RIGHT, -15, 15);  // Keep consistent with wait page
}



/**
 * @brief Start button event callback
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
        
        // Set focus page time
        ui_focus_set_time(sg_nav.selected_time);
        
        // Send to computer via UART
        const char *serial_msg = "start\n";
        tal_uart_write(TUYA_UART_NUM_0, (const uint8_t *)serial_msg, strlen(serial_msg));
        PR_INFO("Serial message sent: %s", serial_msg);

        
        ui_manager_show_focus_page();
    }
}

/**
 * @brief Time slider event callback
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
 * @brief Get slider gradient color
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
 * @brief Set WiFi status
 */
void ui_navigation_set_network(char *wifi_icon)
{
    if (wifi_icon == NULL) {
        return;
    }
    
    // Update navigation page WiFi icon
    if (sg_nav.nav_wifi_label) {
        lv_label_set_text(sg_nav.nav_wifi_label, wifi_icon);
    }
    
    PR_INFO("Navigation WiFi status updated: %s", wifi_icon);
} 