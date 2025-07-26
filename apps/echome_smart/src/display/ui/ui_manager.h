#ifndef __UI_MANAGER_H__
#define __UI_MANAGER_H__

#include "lvgl.h"
#include "ui_display.h"

// 页面状态枚举
typedef enum {
    UI_PAGE_WAKEUP = 0,      // 开机等待页面
    UI_PAGE_NAVIGATION,      // 导航设置页面
    UI_PAGE_FOCUS,          // 专注模式页面
    UI_PAGE_MAX
} UI_PAGE_E;

// 页面管理器结构体
typedef struct {
    UI_PAGE_E current_page;  // 当前页面
    bool page_initialized[UI_PAGE_MAX];  // 页面初始化状态
} UI_MANAGER_T;

// 页面管理器接口函数
int ui_manager_init(UI_FONT_T *ui_font);
void ui_manager_switch_page(UI_PAGE_E target_page);
UI_PAGE_E ui_manager_get_current_page(void);
bool ui_manager_is_page_visible(UI_PAGE_E page);

// 页面切换函数
void ui_manager_show_wakeup_page(void);
void ui_manager_show_navigation_page(void);
void ui_manager_show_focus_page(void);

#endif // __UI_MANAGER_H__ 