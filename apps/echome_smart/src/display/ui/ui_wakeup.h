/**
 * @file ui_wakeup.h
 * @brief Header file for Wakeup UI Display
 *
 * This header file defines the interface for the wakeup UI display module,
 * including wait state, wakeup animations, and touch event handling.
 *
 * @copyright Copyright (c) 2021-2025 Tuya Inc. All Rights Reserved.
 *
 */

#ifndef __UI_WAKEUP_H__
#define __UI_WAKEUP_H__

#include "tuya_cloud_types.h"
#include "ui_display.h"

#ifdef __cplusplus
extern "C" {
#endif

/***********************************************************
************************macro define************************
***********************************************************/

/***********************************************************
***********************typedef define***********************
***********************************************************/
typedef enum {
    WAKEUP_STATE_HIDDEN = 0,    // Hidden state
    WAKEUP_STATE_WAIT,          // Standby state: display circular button, background #CEFF7E
    WAKEUP_STATE_WAKE_ANIMATION, // Animation state: button left-right movement animation
    WAKEUP_STATE_MAX
} WAKEUP_STATE_E;

/***********************************************************
********************function declaration********************
***********************************************************/

/**
 * @brief Initialize wakeup UI
 * @param ui_font UI font configuration
 * @return 0 on success, -1 on failure
 */
int ui_wakeup_init(UI_FONT_T *ui_font);

/**
 * @brief Show wait page (green background, blue circle button)
 * @return 0 on success
 */
int ui_wakeup_show_wait(void);

/**
 * @brief Start wakeup animation sequence (button moving animation)
 * @return 0 on success
 */
int ui_wakeup_start_animation(void);

/**
 * @brief Hide wakeup UI
 * @return 0 on success
 */
int ui_wakeup_hide(void);

/**
 * @brief Get current wakeup state
 * @return Current state
 */
int ui_wakeup_get_state(void);

#ifdef __cplusplus
}
#endif

#endif /* __UI_WAKEUP_H__ */ 