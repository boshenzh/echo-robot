#ifndef __UI_MANAGER_H__
#define __UI_MANAGER_H__

#include "lvgl.h"
#include "ui_display.h"

// Page state enumeration
typedef enum {
    UI_PAGE_WAKEUP = 0,      // Wakeup waiting page
    UI_PAGE_NAVIGATION,      // Navigation settings page
    UI_PAGE_FOCUS,          // Focus mode page
    UI_PAGE_MAX
} UI_PAGE_E;

// Page manager structure
typedef struct {
    UI_PAGE_E current_page;  // Current page
    bool page_initialized[UI_PAGE_MAX];  // Page initialization status
} UI_MANAGER_T;

// Page manager interface functions
int ui_manager_init(UI_FONT_T *ui_font);
void ui_manager_switch_page(UI_PAGE_E target_page);
UI_PAGE_E ui_manager_get_current_page(void);
bool ui_manager_is_page_visible(UI_PAGE_E page);

// Page switching functions
void ui_manager_show_wakeup_page(void);
void ui_manager_show_navigation_page(void);
void ui_manager_show_focus_page(void);

#endif // __UI_MANAGER_H__ 