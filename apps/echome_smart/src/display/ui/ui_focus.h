#ifndef __UI_FOCUS_H__
#define __UI_FOCUS_H__

#include "lvgl.h"
#include "ui_display.h"

// Focus页面初始化
int ui_focus_init(UI_FONT_T *ui_font);

// Focus页面显示/隐藏
void ui_focus_show(void);
void ui_focus_hide(void);

// 设置专注时间
void ui_focus_set_time(float time);

// 设置WiFi状态
void ui_focus_set_network(char *wifi_icon);

#endif // __UI_FOCUS_H__ 