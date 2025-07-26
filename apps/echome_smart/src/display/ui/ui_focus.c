#include "ui_focus.h"
#include "ui_manager.h"
#include "../font/font_awesome_symbols.h"
#include "tuya_log.h"
#include "tal_uart.h"
#include <stdio.h>
#include <math.h>

// Focus page UI structure
typedef struct {
    lv_obj_t *container;           // Page container
    lv_obj_t *background;          // Background
    lv_obj_t *progress_ring;       // Circular progress bar
    lv_obj_t *time_label;          // Countdown display label
    lv_obj_t *status_label;        // Status display label
    lv_obj_t *stop_button;         // Stop/continue button
    lv_obj_t *stop_label;          // Stop/continue button text
    lv_obj_t *finish_button;       // Finish button
    lv_obj_t *finish_label;        // Finish button text
    lv_obj_t *move_button;         // Move back button
    lv_obj_t *move_label;          // Move back button text
    lv_obj_t *wifi_label;          // WiFi status display
    lv_timer_t *timer;             // Countdown timer
    
    float total_time;              // Total focus time (hours)
    float remaining_time;          // Remaining time (hours)
    bool is_running;               // Whether countdown is running
    bool is_paused;                // Whether paused
} UI_FOCUS_T;

static UI_FOCUS_T sg_focus = {0};

// Forward declarations
static void __ui_create_focus_container(void);
static void __ui_create_focus_background(void);
static void __ui_create_focus_progress_ring(void);
static void __ui_create_focus_time_label(void);
static void __ui_create_focus_status_label(void);
static void __ui_create_focus_stop_button(void);
static void __ui_create_focus_finish_button(void);
static void __ui_create_focus_move_button(void);
static void __ui_create_focus_wifi_status(void);
static void __focus_timer_cb(lv_timer_t *timer);
static void __stop_button_event_cb(lv_event_t *e);
static void __finish_button_event_cb(lv_event_t *e);
static void __move_button_event_cb(lv_event_t *e);
static void __update_time_display(void);
static void __update_progress_ring(void);

/**
 * @brief Initialize focus page
 */
int ui_focus_init(UI_FONT_T *ui_font)
{
    (void)ui_font; // Focus page doesn't use fonts
    
    // Clear state
    memset(&sg_focus, 0, sizeof(UI_FOCUS_T));
    sg_focus.total_time = 1.0f;      // Default 1 hour
    sg_focus.remaining_time = 1.0f;  // Default 1 hour
    sg_focus.is_running = false;
    sg_focus.is_paused = false;
    
    // Create UI components
    __ui_create_focus_container();
    __ui_create_focus_background();
    __ui_create_focus_progress_ring();
    __ui_create_focus_time_label();
    __ui_create_focus_status_label();
    __ui_create_focus_stop_button();
    __ui_create_focus_finish_button();
    __ui_create_focus_move_button();
    __ui_create_focus_wifi_status();
    
    // Initially hidden
    lv_obj_add_flag(sg_focus.container, LV_OBJ_FLAG_HIDDEN);
    
    PR_INFO("Focus page initialized");
    return 0;
}

/**
 * @brief Show focus page
 */
void ui_focus_show(void)
{
    lv_obj_clear_flag(sg_focus.container, LV_OBJ_FLAG_HIDDEN);
    
    // Reset state
    sg_focus.is_running = true;
    sg_focus.is_paused = false;
    sg_focus.remaining_time = sg_focus.total_time;
    
    // Reset UI display
    lv_label_set_text(sg_focus.status_label, "");
    lv_label_set_text(sg_focus.stop_label, "Stop");
    
    // Send duration signal to UART (in minutes)
    int total_minutes = (int)(sg_focus.total_time * 60);
    char serial_msg[32];
    sprintf(serial_msg, "%d\n", total_minutes);
    tal_uart_write(TUYA_UART_NUM_0, (const uint8_t *)serial_msg, strlen(serial_msg));
    PR_INFO("Serial message sent: %s (duration in minutes)", serial_msg);
    
    // Create timer, update every second
    sg_focus.timer = lv_timer_create(__focus_timer_cb, 1000, NULL);
    
    // Update display
    __update_time_display();
    __update_progress_ring();
    
    PR_INFO("Focus page shown with %.1f hours", sg_focus.total_time);
}

/**
 * @brief Hide focus page
 */
void ui_focus_hide(void)
{
    lv_obj_add_flag(sg_focus.container, LV_OBJ_FLAG_HIDDEN);
    
    // Stop timer
    if (sg_focus.timer) {
        lv_timer_del(sg_focus.timer);
        sg_focus.timer = NULL;
    }
    
    sg_focus.is_running = false;
    sg_focus.is_paused = false;
    PR_INFO("Focus page hidden");
}

/**
 * @brief Set focus time
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
 * @brief Create focus page container
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
 * @brief Create focus page background
 */
static void __ui_create_focus_background(void)
{
    sg_focus.background = lv_obj_create(sg_focus.container);
    lv_obj_set_size(sg_focus.background, LV_PCT(100), LV_PCT(100));
    lv_obj_set_pos(sg_focus.background, 0, 0);
    lv_obj_clear_flag(sg_focus.background, LV_OBJ_FLAG_SCROLLABLE);
    // Use nav page background color
    lv_obj_set_style_bg_color(sg_focus.background, lv_color_hex(0xD8E2EC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_focus.background, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_focus.background, 0, LV_PART_MAIN);
}

/**
 * @brief Create focus page circular progress bar
 */
static void __ui_create_focus_progress_ring(void)
{
    sg_focus.progress_ring = lv_arc_create(sg_focus.container);
    lv_obj_set_size(sg_focus.progress_ring, 200, 200);
    lv_obj_align(sg_focus.progress_ring, LV_ALIGN_CENTER, 0, -20);
    
    // Set circular progress bar style
    lv_arc_set_range(sg_focus.progress_ring, 0, 100);
    lv_arc_set_value(sg_focus.progress_ring, 100);
    lv_arc_set_bg_angles(sg_focus.progress_ring, 0, 360);
    
    // Set circular progress bar colors - use unified color
    lv_obj_set_style_arc_color(sg_focus.progress_ring, lv_color_hex(0xE0E0E0), LV_PART_MAIN);  // Background ring
    lv_obj_set_style_arc_color(sg_focus.progress_ring, lv_color_hex(0x529ACC), LV_PART_INDICATOR);  // Progress ring
    lv_obj_set_style_arc_width(sg_focus.progress_ring, 8, LV_PART_MAIN);
    lv_obj_set_style_arc_width(sg_focus.progress_ring, 8, LV_PART_INDICATOR);
    
    // Hide circular progress bar knob
    lv_obj_set_style_arc_width(sg_focus.progress_ring, 0, LV_PART_KNOB);
}

/**
 * @brief Create focus page time display label
 */
static void __ui_create_focus_time_label(void)
{
    sg_focus.time_label = lv_label_create(sg_focus.container);
    lv_obj_set_style_text_color(sg_focus.time_label, lv_color_hex(0x333333), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_focus.time_label, &lv_font_montserrat_24, LV_PART_MAIN);
    lv_obj_align(sg_focus.time_label, LV_ALIGN_CENTER, 0, -20);
    
    // Set initial text
    lv_label_set_text(sg_focus.time_label, "01:00:00");
}

/**
 * @brief Create focus page status display label
 */
static void __ui_create_focus_status_label(void)
{
    sg_focus.status_label = lv_label_create(sg_focus.container);
    lv_obj_set_style_text_color(sg_focus.status_label, lv_color_hex(0x666666), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_focus.status_label, &lv_font_montserrat_14, LV_PART_MAIN);
    lv_obj_align(sg_focus.status_label, LV_ALIGN_CENTER, 0, 80);
    
    // Do not display status text
    lv_label_set_text(sg_focus.status_label, "");
}

/**
 * @brief Focus page stop/continue button
 */
static void __ui_create_focus_stop_button(void)
{
    sg_focus.stop_button = lv_obj_create(sg_focus.container);
    lv_obj_set_size(sg_focus.stop_button, 80, 40);
    lv_obj_align(sg_focus.stop_button, LV_ALIGN_CENTER, -90, 120);  // Left shift
    lv_obj_clear_flag(sg_focus.stop_button, LV_OBJ_FLAG_SCROLLABLE);
    

    lv_obj_set_style_bg_color(sg_focus.stop_button, lv_color_hex(0x529ACC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_focus.stop_button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_focus.stop_button, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_focus.stop_button, 20, LV_PART_MAIN);
    
    // Stop button text
    sg_focus.stop_label = lv_label_create(sg_focus.stop_button);
    lv_label_set_text(sg_focus.stop_label, "Stop");
    lv_obj_set_style_text_color(sg_focus.stop_label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_focus.stop_label, &lv_font_montserrat_14, LV_PART_MAIN);
    lv_obj_center(sg_focus.stop_label);
    
    // Stop button click event
    lv_obj_add_event_cb(sg_focus.stop_button, __stop_button_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(sg_focus.stop_button, __stop_button_event_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(sg_focus.stop_button, __stop_button_event_cb, LV_EVENT_PRESS_LOST, NULL);
}

/**
 * @brief Focus page finish button
 */
static void __ui_create_focus_finish_button(void)
{
    sg_focus.finish_button = lv_obj_create(sg_focus.container);
    lv_obj_set_size(sg_focus.finish_button, 80, 40);
    lv_obj_align(sg_focus.finish_button, LV_ALIGN_CENTER, 90, 120);  // Right shift
    lv_obj_clear_flag(sg_focus.finish_button, LV_OBJ_FLAG_SCROLLABLE);
    
    // Finish button style 
    lv_obj_set_style_bg_color(sg_focus.finish_button, lv_color_hex(0x529ACC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_focus.finish_button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_focus.finish_button, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_focus.finish_button, 20, LV_PART_MAIN);
    
    // Finish button text
    sg_focus.finish_label = lv_label_create(sg_focus.finish_button);
    lv_label_set_text(sg_focus.finish_label, "Finish");
    lv_obj_set_style_text_color(sg_focus.finish_label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_focus.finish_label, &lv_font_montserrat_14, LV_PART_MAIN);
    lv_obj_center(sg_focus.finish_label);
    
    // Finish button click event
    lv_obj_add_event_cb(sg_focus.finish_button, __finish_button_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(sg_focus.finish_button, __finish_button_event_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(sg_focus.finish_button, __finish_button_event_cb, LV_EVENT_PRESS_LOST, NULL);
}

/**
 * @brief Focus page move back button
 */
static void __ui_create_focus_move_button(void)
{
    sg_focus.move_button = lv_obj_create(sg_focus.container);
    lv_obj_set_size(sg_focus.move_button, 80, 40);
    lv_obj_align(sg_focus.move_button, LV_ALIGN_CENTER, 0, 120);  // Center placement
    lv_obj_clear_flag(sg_focus.move_button, LV_OBJ_FLAG_SCROLLABLE);
    
    // Move back button style 
    lv_obj_set_style_bg_color(sg_focus.move_button, lv_color_hex(0x529ACC), LV_PART_MAIN);
    lv_obj_set_style_bg_opa(sg_focus.move_button, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_width(sg_focus.move_button, 0, LV_PART_MAIN);
    lv_obj_set_style_radius(sg_focus.move_button, 20, LV_PART_MAIN);
    
    // Move back button text
    sg_focus.move_label = lv_label_create(sg_focus.move_button);
    lv_label_set_text(sg_focus.move_label, "echo");
    lv_obj_set_style_text_color(sg_focus.move_label, lv_color_white(), LV_PART_MAIN);
    lv_obj_set_style_text_font(sg_focus.move_label, &lv_font_montserrat_14, LV_PART_MAIN);
    lv_obj_center(sg_focus.move_label);
    
    // Move back button click event
    lv_obj_add_event_cb(sg_focus.move_button, __move_button_event_cb, LV_EVENT_PRESSED, NULL);
    lv_obj_add_event_cb(sg_focus.move_button, __move_button_event_cb, LV_EVENT_RELEASED, NULL);
    lv_obj_add_event_cb(sg_focus.move_button, __move_button_event_cb, LV_EVENT_PRESS_LOST, NULL);
}

/**
 * @brief Focus page WiFi status display
 */
static void __ui_create_focus_wifi_status(void)
{
    sg_focus.wifi_label = lv_label_create(sg_focus.container);
    lv_label_set_text(sg_focus.wifi_label, FONT_AWESOME_WIFI_OFF);
    lv_obj_set_style_text_color(sg_focus.wifi_label, lv_color_hex(0x666666), LV_PART_MAIN);
    
    extern const lv_font_t font_awesome_16_4;
    lv_obj_set_style_text_font(sg_focus.wifi_label, &font_awesome_16_4, LV_PART_MAIN);
    
    lv_obj_set_size(sg_focus.wifi_label, 30, 30);  // Set fixed size to ensure visibility
    lv_obj_align(sg_focus.wifi_label, LV_ALIGN_TOP_RIGHT, -15, 15);  // Keep consistent with other pages
}

/**
 * @brief Countdown timer callback
 */
static void __focus_timer_cb(lv_timer_t *timer)
{
    (void)timer;
    
    if (!sg_focus.is_running || sg_focus.is_paused) {
        return;
    }
    
    // Reduce remaining time (decrease by 1/3600 hours per second)
    sg_focus.remaining_time -= 1.0f / 3600.0f;
    
    if (sg_focus.remaining_time <= 0) {
        // Countdown finished
        sg_focus.remaining_time = 0;
        sg_focus.is_running = false;
        
        // Stop timer
        if (sg_focus.timer) {
            lv_timer_del(sg_focus.timer);
            sg_focus.timer = NULL;
        }
        
        // Update status display
        lv_label_set_text(sg_focus.status_label, "Time's Up!");
        lv_label_set_text(sg_focus.stop_label, "Done");
        lv_label_set_text(sg_focus.finish_label, "Done");
        
        PR_INFO("Focus session completed");
    }
    
    // Update display
    __update_time_display();
    __update_progress_ring();
}

/**
 * @brief Stop/continue button event callback
 */
static void __stop_button_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    
    if (code == LV_EVENT_PRESSED) {
        PR_INFO("Stop/Continue button pressed");
        
    } else if (code == LV_EVENT_RELEASED || code == LV_EVENT_PRESS_LOST) {
        PR_INFO("Stop/Continue button released");
        
        if (sg_focus.is_paused) {
            // If paused, continue countdown
            PR_INFO("Continuing focus session");
            sg_focus.is_paused = false;
            sg_focus.is_running = true;
            
            // Recreate timer
            sg_focus.timer = lv_timer_create(__focus_timer_cb, 1000, NULL);
            
            // Update button text and status
            lv_label_set_text(sg_focus.stop_label, "Stop");
            lv_label_set_text(sg_focus.status_label, "");
            
        } else if (sg_focus.is_running) {
            // If countdown is running, pause
            PR_INFO("Pausing focus session");
            sg_focus.is_paused = true;
            sg_focus.is_running = false;
            
            // Stop timer
            if (sg_focus.timer) {
                lv_timer_del(sg_focus.timer);
                sg_focus.timer = NULL;
            }
            
            // Update button text and status
            lv_label_set_text(sg_focus.stop_label, "Continue");
            lv_label_set_text(sg_focus.status_label, "");
            
        } else {
            // If countdown has finished, return to navigation page
            PR_INFO("Focus session completed, returning to navigation");
            ui_manager_show_navigation_page();
        }
    }
}

/**
 * @brief Finish button event callback
 */
static void __finish_button_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    
    if (code == LV_EVENT_PRESSED) {
        PR_INFO("Finish button pressed");
        
    } else if (code == LV_EVENT_RELEASED || code == LV_EVENT_PRESS_LOST) {
        PR_INFO("Finish button released");
        
        // Stop timer
        if (sg_focus.timer) {
            lv_timer_del(sg_focus.timer);
            sg_focus.timer = NULL;
        }
        
        // Reset state
        sg_focus.is_running = false;
        sg_focus.is_paused = false;
        
        // Update status display
        lv_label_set_text(sg_focus.status_label, "Finished");
        lv_label_set_text(sg_focus.stop_label, "Done");
        
        // Send reset signal to UART
        const char *serial_msg = "reset\n";
        tal_uart_write(TUYA_UART_NUM_0, (const uint8_t *)serial_msg, strlen(serial_msg));
        PR_INFO("Serial message sent: %s", serial_msg);
        
        PR_INFO("Focus session finished by user");
        
        // Return to navigation page
        ui_manager_show_navigation_page();
    }
}

/**
 * @brief Move back button event callback
 */
static void __move_button_event_cb(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    
    if (code == LV_EVENT_PRESSED) {
        PR_INFO("Move button pressed");
        
    } else if (code == LV_EVENT_RELEASED || code == LV_EVENT_PRESS_LOST) {
        PR_INFO("Move button released");
        
        // Send move signal to UART
        const char *serial_msg = "move\n";
        tal_uart_write(TUYA_UART_NUM_0, (const uint8_t *)serial_msg, strlen(serial_msg));
        PR_INFO("Serial message sent: %s", serial_msg);
        
        // Page does not change, continue displaying current page
    }
}

/**
 * @brief Update time display
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
 * @brief Update circular progress bar
 */
static void __update_progress_ring(void)
{
    if (!sg_focus.progress_ring) {
        return;
    }
    
    // Calculate progress percentage
    float progress = 0.0f;
    if (sg_focus.total_time > 0) {
        progress = (sg_focus.remaining_time / sg_focus.total_time) * 100.0f;
    }
    
    // Set circular progress bar value
    lv_arc_set_value(sg_focus.progress_ring, (int16_t)progress);
}

/**
 * @brief Set WiFi status
 */
void ui_focus_set_network(char *wifi_icon)
{
    if (wifi_icon == NULL) {
        return;
    }
    
    // Focus page WiFi icon
    if (sg_focus.wifi_label) {
        lv_label_set_text(sg_focus.wifi_label, wifi_icon);
    }
    
    PR_INFO("Focus WiFi status updated: %s", wifi_icon);
} 