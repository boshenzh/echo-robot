#include "ui_manager.h"
#include "ui_wakeup.h"
#include "ui_navigation.h"
#include "ui_focus.h"
#include "tuya_log.h"

static UI_MANAGER_T sg_ui_manager = {0};

/**
 * @brief 初始化页面管理器
 */
int ui_manager_init(UI_FONT_T *ui_font)
{
    // 清空状态
    memset(&sg_ui_manager, 0, sizeof(UI_MANAGER_T));
    sg_ui_manager.current_page = UI_PAGE_WAKEUP;
    
    // 初始化各个页面
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
 * @brief 切换页面
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
    
    // 隐藏当前页面
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
    
    // 显示目标页面
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
 * @brief 获取当前页面
 */
UI_PAGE_E ui_manager_get_current_page(void)
{
    return sg_ui_manager.current_page;
}

/**
 * @brief 检查页面是否可见
 */
bool ui_manager_is_page_visible(UI_PAGE_E page)
{
    if (page >= UI_PAGE_MAX) {
        return false;
    }
    return (sg_ui_manager.current_page == page);
}

/**
 * @brief 显示wakeup页面
 */
void ui_manager_show_wakeup_page(void)
{
    ui_manager_switch_page(UI_PAGE_WAKEUP);
}

/**
 * @brief 显示navigation页面
 */
void ui_manager_show_navigation_page(void)
{
    ui_manager_switch_page(UI_PAGE_NAVIGATION);
}

/**
 * @brief 显示focus页面
 */
void ui_manager_show_focus_page(void)
{
    ui_manager_switch_page(UI_PAGE_FOCUS);
} 