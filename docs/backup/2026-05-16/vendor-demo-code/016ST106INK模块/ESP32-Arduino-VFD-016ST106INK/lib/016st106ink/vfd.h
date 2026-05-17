#ifndef __VFD_H__
#define __VFD_H__

#/**************************************************************************
 * @file    vfd.h
 * @brief   简单的 VFD 驱动头文件（接口声明与引脚定义）。
 *
 * 该头文件提供对 016ST106INK 型 VFD 的基础控制接口：初始化、
 * 电源/亮度控制、清屏及打印字符串。对外以 C 接口导出以便在
 * C/C++ 项目中使用。
 *************************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

#if defined(ARDUINO)
#include <Arduino.h>
#else
#define HIGH 1
#define LOW 0
#endif

#define VFD_PIN_RST GPIO_NUM_0 
#define VFD_PIN_CS  GPIO_NUM_1 
#define VFD_PIN_CP  GPIO_NUM_12 
#define VFD_PIN_DA  GPIO_NUM_18 
#define VFD_PIN_EN  GPIO_NUM_19 

    /**
     * @brief 抽象化 IO 操作，默认映射为 Arduino 的 digitalWrite。
     * @note 如果在非 Arduino 环境使用，可在移植时替换该宏实现。
     * @param pin 引脚编号
     * @param level 电平，使用 HIGH/LOW
     */
#define VFD_IO_Write(pin,level) digitalWrite(pin,level)

#/**
 * @brief 精确延时（微秒），默认映射为 Arduino 的 delayMicroseconds。
 * @param us 延时的微秒数
 */
#define VFD_DelayUs(us)      delayMicroseconds(us)
#define VFD_DelayMs(ms)      delay(ms)


 /**
  * @brief 初始化 VFD 硬件接口与控制器
  *
  * 配置 GPIO 引脚为输出、复位 VFD 并执行必要的启动序列。
  */
    void VFD_Init(void);

    /**
     * @brief 打开或关闭 VFD 电源（逻辑控制）
     * @param on 0 表示关闭，非 0 表示打开
     */
    void VFD_SetPower(uint8_t on);

    /**
     * @brief 设置显示亮度
     * @param brightness 亮度值（范围 0-255）
     */
    void VFD_SetBrightness(uint8_t brightness);

    /**
     * @brief 清除显示内容并将光标/地址复位到初始位置
     */
    void VFD_Clear(void);

    /**
     * @brief 在指定行打印字符串
     * @param line 要写入的行号（从 0 开始，取值范围依模块而定）
     * @param str  C 字符串
     */
    void VFD_PrintString(uint8_t line, const char* str);

    /**
     * @brief 设置指定图标的显示状态
     * @param pos 图标位置索引（从 0 开始）
     * @param col1 图标的第一列颜色显示状态（0=关闭，非0=打开）
     * @param col2 图标的第二列颜色显示状态（0=关闭，非0=打开）
     */
    void VFD_SetIconNative(uint8_t pos, uint8_t col1, uint8_t col2);

#ifdef __cplusplus
}
#endif


#endif