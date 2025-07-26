#include "ui_manager.h"
#include "ui_wakeup.h"
#include "ui_navigation.h"
#include "ui_focus.h"
#include "tuya_log.h"

static UI_MANAGER_T sg_ui_manager = {0};

/**
 * @brief Initialize page manager
 */
int ui_manager_init(UI_FONT_T *ui_font)
{
    // Clear state
    memset(&sg_ui_manager, 0, sizeof(UI_MANAGER_T));
    sg_ui_manager.current_page = UI_PAGE_WAKEUP;
    
    // Initialize each page
    int ret = ui_wakeup_init(ui_font);
    if (ret != 0) {
        PR_ERR("Failed to init wakeup page");
        return ret;
    }
    sg_ui_manager.page_initialized[UI_PAGE_WAKEUP] = true;
    
    ret = ui_navigation_init(ui_font);
    if (ret != 0) {
        PR_ERR("Failed to init navigation page");
        return ret;
    }
    sg_ui_manager.page_initialized[UI_PAGE_NAVIGATION] = true;
    
    ret = ui_focus_init(ui_font);
    if (ret != 0) {
        PR_ERR("Failed to init focus page");
        return ret;
    }
    sg_ui_manager.page_initialized[UI_PAGE_FOCUS] = true;
    
    PR_INFO("UI Manager initialized successfully");
    return 0;
}

/**
 * @brief Switch to target page
 */
void ui_manager_switch_page(UI_PAGE_E target_page)
{
    if (target_page >= UI_PAGE_MAX) {
        PR_ERR("Invalid page: %d", target_page);
        return;
    }
    
    if (!sg_ui_manager.page_initialized[target_page]) {
        PR_ERR("Page %d not initialized", target_page);
        return;
    }
    
    // Hide current page
    switch (sg_ui_manager.current_page) {
    case UI_PAGE_WAKEUP:
        ui_wakeup_hide();
        break;
    case UI_PAGE_NAVIGATION:
        ui_navigation_hide();
        break;
    case UI_PAGE_FOCUS:
        ui_focus_hide();
        break;
    default:
        break;
    }
    
    // Show target page
    switch (target_page) {
    case UI_PAGE_WAKEUP:
        ui_wakeup_show_wait();
        break;
    case UI_PAGE_NAVIGATION:
        ui_navigation_show();
        break;
    case UI_PAGE_FOCUS:
        ui_focus_show();
        break;
    default:
        break;
    }
    
    sg_ui_manager.current_page = target_page;
    PR_INFO("Switched to page: %d", target_page);
}

/**
 * @brief Get current page
 */
UI_PAGE_E ui_manager_get_current_page(void)
{
    return sg_ui_manager.current_page;
}

/**
 * @brief Check if page is visible
 */
bool ui_manager_is_page_visible(UI_PAGE_E page)
{
    if (page >= UI_PAGE_MAX) {
        return false;
    }
    return (sg_ui_manager.current_page == page);
}

/**
 * @brief Show wakeup page
 */
void ui_manager_show_wakeup_page(void)
{
    ui_manager_switch_page(UI_PAGE_WAKEUP);
}

/**
 * @brief Show navigation page
 */
void ui_manager_show_navigation_page(void)
{
    ui_manager_switch_page(UI_PAGE_NAVIGATION);
}

/**
 * @brief Show focus page
 */
void ui_manager_show_focus_page(void)
{
    ui_manager_switch_page(UI_PAGE_FOCUS);
} 