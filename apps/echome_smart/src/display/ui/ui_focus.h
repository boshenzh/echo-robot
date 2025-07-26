#ifndef __UI_FOCUS_H__
#define __UI_FOCUS_H__

#include "lvgl.h"
#include "ui_display.h"

// Focus page initialization
int ui_focus_init(UI_FONT_T *ui_font);

// Focus page show/hide
void ui_focus_show(void);
void ui_focus_hide(void);

// Set focus time
void ui_focus_set_time(float time);

// Set WiFi status
void ui_focus_set_network(char *wifi_icon);

#endif // __UI_FOCUS_H__ 