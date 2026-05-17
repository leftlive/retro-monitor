# Retro-Monitor VFD UI 调试进度与设计规范总结

**最后更新**：2026-04-20

本文档汇总了截止到当前对 `016ST106INK` VFD 监视器 UI 的全部调试成果、设计逻辑及排版标准。

## 1. 核心设计语言 (Design Language)

*   **极简主义风格**：采用单像素笔画厚度（Single-pixel stroke）、4 像素宽度、左下角对齐重绘 CPU/GPU 核心字符。
*   **空间利用最大化**：引入 `write_cgram_7x5` 驱动升级，解锁完整 7 像素物理高度，实现分栏长竖线。
*   **动态交互**：统一 1 秒周期的心跳闪烁（Blink）逻辑，用于状态警告与 UI 分类。

## 2. 双页轮播系统

系统每 **10 秒** 自动切换页面，并通过右侧 `SP A` / `SP B` 图标指示当前页面。

### 第一屏 (Page 0) — 核心概览 (`SP B` 亮起)

| 行 | 位置 | 内容 | 格式 |
| :--- | :--- | :--- | :--- |
| Line 1 | 0-2 | CPU | 4px 宽自定义字模 |
| Line 1 | 3 | 分隔符 | 7px 竖线 + 2x2 闪烁方块 |
| Line 1 | 4-6 | GPU | 4px 宽自定义字模 |
| Line 1 | 7 | 分隔符 | 同上 |
| Line 2 | 0-2 | CPU 温度 | `XX℃` |
| Line 2 | 3 | 分隔竖线 | 纯竖线（常驻） |
| Line 2 | 4-6 | GPU 温度 | `XX℃` |
| Line 2 | 7 | 分隔竖线 | 纯竖线（常驻） |
| Line 2 | 8-10 | CPU 负载 | `X%` 或 `XX%`（动态对齐） |
| Line 2 | 11-15 | 整机功率 | `⚡XXXw` |

### 第二屏 (Page 1) — 系统详情 (`SP A` 亮起)

| 行 | 位置 | 内容 | 格式 |
| :--- | :--- | :--- | :--- |
| Line 1 | 0-2 | MEM | 标准 ROM 字符 |
| Line 1 | 3 | 分隔符 | 7px 竖线 + 2x2 闪烁方块 |
| Line 1 | 4-6 | FAN | 标准 ROM 字符 |
| Line 1 | 7 | 分隔符 | 同上 |
| Line 2 | 0-2 | 内存占用 | `XX%` |
| Line 2 | 3 | 分隔竖线 | 纯竖线（常驻） |
| Line 2 | 4-8 | 风扇最高转速 | `XXXXr` 或 ` XXXr`（右对齐） |
| Line 2 | 9-10 | 空白 | 留白 |
| Line 2 | 11-15 | 整机功率 | `⚡XXXw`（与第一屏共享） |

## 3. 页面切换动画 — 矩阵解码 + 亮度呼吸

切换动画分为三个阶段，总时长约 860ms：

1.  **Phase 1 — 暗场衰减 (250ms)**：亮度分 5 步从 `0xE0` 降至接近全黑，模拟 VFD 荧光粉断电余辉。
2.  **Phase 2 — 矩阵解码 + 亮度恢复 (605ms)**：所有字符位变为随机十六进制噪声 (`0-9 A-F`)，然后从左到右逐个"锁定"到目标值。亮度同步从最低线性恢复到最高。分隔符和功率段在解码期间保持稳定不参与动画。
3.  **Phase 3 — 最终锁定**：亮度归位到 `0xE0`，翻页并重启计时。

## 4. 开机动画 — BIOS 风格自检序列

开机动画总时长约 10 秒，分为四个阶段：

1.  **全格预热 (Glow Up)**：所有像素方块点亮，亮度从 0 呼吸式上升到最高。
2.  **图标自检 (Diagnostic)**：右侧 ADRAM 图标从左到右依次扫描点亮。
3.  **十六进制滚动 (BIOS Hex Scroll)**：第一行显示 `LOADING NOX-OS`，第二行快速滚动随机十六进制地址。
4.  **系统就绪 (SYSTEM READY)**：短暂停留后切入正常 UI。

## 5. 电源管理

| 功能 | 触发条件 | 行为 |
| :--- | :--- | :--- |
| 自动息屏 | 3 分钟无数据 | 调用 `set_power(false)` 关闭高压，停止 UI 渲染 |
| 自动唤醒 | `cpu_temp` 收到新值 | 调用 `begin(0xE0)` 完整重初始化（含 CGRAM 恢复） |

## 6. 当前部署信息

*   **修改文件**：
    *   `esphome/vfd_016st106ink_ha_monitor.yaml` — 主配置与渲染逻辑
    *   `esphome/includes/vfd_016st106ink/vfd_016st106ink.h` — 底层 VFD 驱动
*   **USB 烧录命令**：
    ```bash
    cd /path/to/retro-monitor && .venv/bin/esphome run esphome/vfd_016st106ink_ha_monitor.yaml
    ```
*   **当前订阅的 HA 实体**：
    *   `cpu_temperature`, `cpu_load`, `cpu_power`
    *   `gpu_temperature`, `gpu_load`
    *   `memory_usage`, `fan_speed_max`
    *   `system_power_estimated`, `data_source_ok`

---
**调试记录人**：Antigravity (AI coding assistant)
**当前状态**：全部功能已闭合。双页轮播、矩阵解码切换动画、BIOS 风格开机动画、自动息屏/唤醒均已实现并验证。
