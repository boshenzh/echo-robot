#ifndef __UI_NAVIGATION_H__
#define __UI_NAVIGATION_H__

#include "lvgl.h"
#include "ui_display.h"

// Navigation页面初始化
int ui_navigation_init(UI_FONT_T *ui_font);

// Navigation页面显示/隐藏
void ui_navigation_show(void);
void ui_navigation_hide(void);

// 获取选择的专注时间
float ui_navigation_get_selected_time(void);

// 设置专注时间
void ui_navigation_set_selected_time(float time);

// 设置WiFi状态
void ui_navigation_set_network(char *wifi_icon);

#endif // __UI_NAVIGATION_H__ 