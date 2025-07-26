#ifndef __UI_NAVIGATION_H__
#define __UI_NAVIGATION_H__

#include "lvgl.h"
#include "ui_display.h"

// Navigation page initialization
int ui_navigation_init(UI_FONT_T *ui_font);

// Navigation page show/hide
void ui_navigation_show(void);
void ui_navigation_hide(void);

// Get selected focus time
float ui_navigation_get_selected_time(void);

// Set focus time
void ui_navigation_set_selected_time(float time);

// Set WiFi status
void ui_navigation_set_network(char *wifi_icon);

#endif // __UI_NAVIGATION_H__ 