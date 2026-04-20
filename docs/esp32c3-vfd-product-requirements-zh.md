# ESP32-C3 SuperMini + 016ST106INK VFD 复古监控屏需求梳理

## 1. 项目定位

本分支项目使用 `ESP32-C3 SuperMini` 与 `016ST106INK` VFD 屏幕模块，制作一款简易功能的复古科技风电脑状态监控屏。

它不是 SSD1322 OLED 主项目的缩小版，而是一个独立的“复古终端状态牌”分支：

- 视觉优先级高于信息密度。
- 只显示电脑端状态，不接路由器数据。
- 数据复用 Home Assistant 上已有的 ESPHome / integration 实体。
- 显示逻辑必须适配 VFD 固定字符屏，而不是像像素屏一样排复杂仪表盘。

## 2. 资料阅读结论

已阅读的关键资料：

- `016ST106INK模块/说明.txt`
- `ESP32-Arduino-VFD-016ST106INK/platformio.ini`
- `ESP32-Arduino-VFD-016ST106INK/src/main.cpp`
- `ESP32-Arduino-VFD-016ST106INK/lib/016st106ink/vfd.h`
- `ESP32-Arduino-VFD-016ST106INK/lib/016st106ink/vfd.c`
- `ESP32-C3黑SuperMini焊针下/疑难解答.txt`
- `ESP32-C3黑SuperMini焊针下/使用手册链接.txt`
- `ESP32-C3黑SuperMini焊针下/esp32c3_wifi/esp32c3_wifi.ino`
- `ESP32-C3黑SuperMini焊针下/esp32c3BLE/esp32c3BLE.ino`
- `016ST106INK模块/引脚定义.png`
- `ESP32-C3黑SuperMini焊针下/引脚图.jpg`
- `ESP32-C3黑SuperMini焊针下/原理图.png`
- `SCH_Schematic1_2026-01-18.pdf`
- `PCB_PCB1_2026-01-18.pdf`
- `016ST106INK 电路原理图.pdf`
- `013ST084GINK_A_03中文.pdf`
- `013ST084GINK_A_03.pdf`
- `yamaha_r-n402_r-n402d_sm_en.pdf`
- `简易字模提取表.xlsx`

说明：

- `.pio/` 下构建产物与 `.DS_Store` 不作为需求依据。
- `013ST084GINK` 是其他型号规格书，只能作为 VFD 驱动/时序参考，不能直接等同于 `016ST106INK`。
- `yamaha_r-n402_r-n402d_sm_en.pdf` 的价值主要是参考传统音响 VFD 的“短文本 + 模式状态 + 自检风格”，不是硬件驱动依据。

## 3. 硬件约束

### 3.1 VFD 显示能力

现有驱动代码已暴露的实际能力：

- 第 1 行：最多 8 字符。
- 第 2 行：最多 16 字符。
- 支持 7 个原生图标位，调用 `VFD_SetIconNative(pos, col1, col2)`。
- 支持全局亮度，范围 `5-255`，驱动中低于 5 会被钳制。
- 支持清屏与字符串打印。
- 当前示例以滚动下行文本为主。

这意味着本项目不能采用 OLED 方案中的三栏复杂布局、趋势图、柱状图等视觉结构。VFD 应采用“短码、状态词、轮播页、图标灯”的表达方式。

### 3.2 VFD 驱动接口

从 `vfd.h` 和 `vfd.c` 可确认当前驱动引脚定义：

- `RST`: `GPIO_NUM_0`
- `CS`: `GPIO_NUM_1`
- `CP`: `GPIO_NUM_12`
- `DA`: `GPIO_NUM_18`
- `EN`: `GPIO_NUM_19`

驱动协议特征：

- 使用类 SPI 的手动 bit-bang。
- 数据按 LSB first 发送。
- `CP` 上升沿移位。
- `CS` 高电平禁止串行传输。
- 初始化包含时序设置、亮度设置、正常点亮命令。

### 3.3 电源与时序参考

从原理图与参考规格书可确认：

- 模块侧存在 VFD 高压驱动，原理图中出现 `VCC_32V`。
- 逻辑侧使用 `3.3V / 5V` 相关电源域。
- 参考规格书中 VFD 典型驱动电源约 `VH=32V`，逻辑电源建议 `VDD=4.5-5.5V`。
- 参考规格书强调电源顺序：`VDD` 与 `VH` 同时开启，或先 `VDD` 后 `VH`；关闭时同时关闭，或先关 `VH` 后关 `VDD`。
- 串行时钟参考上限约 `0.5MHz`。

当前模块已集成升压/驱动电路，因此软件层主要控制 `EN`、`RST`、`CS/CP/DA` 与亮度，不应直接假设裸管驱动条件。

### 3.4 ESP32-C3 SuperMini 约束

从资料与疑难解答可确认：

- 使用 ESP32-C3 SuperMini，PlatformIO 示例目标为 `esp32-c3-devkitm-1`。
- 上传失败时可能需要手动进入下载模式。
- 上传完成后可能需要按 `RESET` 才执行。
- Arduino 串口打印需要启用 `USB CDC On Boot`。
- 板载可用 GPIO 较少，VFD 已占用 5 个控制脚。

ESP32-C3 SuperMini 适合本分支，因为本项目只需要 Wi-Fi、少量 GPIO、短文本刷新，不需要复杂图形缓冲。

## 4. 产品目标

### 4.1 MVP 目标

做出一台“桌面复古电脑状态 VFD 牌”：

- 能通过 Wi-Fi 接入 Home Assistant。
- 从 HA 读取电脑状态实体。
- VFD 显示电脑关键状态。
- 支持 2-4 个短页面自动轮播。
- 支持基础亮度控制。
- 视觉风格具有复古科技设备感。

### 4.2 非目标

MVP 不做：

- 路由器页面。
- 趋势图。
- 图形仪表盘。
- 多设备选择。
- BLE 控制。
- 本地 Web 配置页面。
- 复杂动画。
- 中文显示。
- 高密度全字段展示。

## 5. 数据来源与边界

本分支不直接访问 macOS Agent。

推荐数据链路：

```text
macOS telemetry agent -> Home Assistant integration -> ESPHome VFD node -> 016ST106INK
```

VFD 节点只消费 HA 实体，不参与底层采集。

首版只消费电脑端字段：

- `cpu_temp`
- `cpu_load`
- `cpu_clock`
- `cpu_power`
- `gpu_temp`
- `gpu_load`
- `gpu_clock`
- `gpu_power`
- `memory_percent`
- `fan_rpm_max`
- `disk_temp_max`
- `system_power_estimated`
- `source_ok`

可选字段：

- `net_up_bps`
- `net_down_bps`

网络速率字段在 VFD 首版不建议作为主显示内容，因为 16 字符约束下表达成本偏高。

## 6. 显示设计原则

### 6.1 视觉优先

VFD 屏幕本身就是核心视觉资产，因此设计应强调：

- 短码。
- 全大写。
- 固定宽度数字。
- 设备自检语言。
- 状态灯/图标辅助。
- 慢节奏轮播。
- 类音响/工业仪表的模式感。

应避免：

- 把 OLED 的三栏 UI 硬塞进 VFD。
- 长句子。
- 多单位混排。
- 小数过多。
- 一屏显示超过 3 个指标。

### 6.2 字符格式

建议显示格式：

- 温度：`CPU 062C`
- 负载：`LOAD 047%`
- 功耗：`PWR 128W`
- 频率：`CLK 5.3G`
- 风扇：`FAN 1820`
- 内存：`MEM 060%`
- 磁盘温度：`DSK 041C`
- 状态：`SYS READY`

数值建议：

- 温度使用 3 位整数。
- 负载使用 3 位整数百分比。
- 功耗使用 3 位整数 W。
- 频率显示为 GHz，保留 1 位小数。
- 风扇显示整数 RPM，但可省略 `RPM` 以节省字符。

### 6.3 单位换算位置

单位换算应放在 VFD/ESPHome 显示端。

原因：

- Agent 和 HA integration 保持规范化原始单位。
- HA 不承担展示格式职责。
- VFD 与 OLED 的显示格式不同，终端应自行决定如何压缩单位。

换算规则：

- `cpu_clock` / `gpu_clock`: `MHz -> GHz`，显示为 `x.xG`
- `memory_used_mb` / `memory_total_mb`: `MiB -> GiB`，但 VFD 首版优先显示百分比
- `net_*_bps`: `bit/s -> Mbps` 或 `MB/s`，但首版不作为主显示
- 温度、负载、功耗直接取整数显示

## 7. 页面结构建议

### 7.1 Page A: 系统总览

用途：默认主页面。

```text
SYS READY
CPU62 GPU54 M60
```

或更复古：

```text
NOX READY
C062 G054 M060
```

字段：

- `source_ok`
- `cpu_temp`
- `gpu_temp`
- `memory_percent`

### 7.2 Page B: CPU 页面

```text
CPU 062C
LOAD047 P086W
```

字段：

- `cpu_temp`
- `cpu_load`
- `cpu_power`

可替换第二行：

```text
CLK5.3G FAN1820
```

### 7.3 Page C: GPU 页面

```text
GPU 054C
LOAD021 P142W
```

字段：

- `gpu_temp`
- `gpu_load`
- `gpu_power`

### 7.4 Page D: Power / Thermal 页面

```text
PWR 286W
DSK041 FAN1820
```

字段：

- `system_power_estimated`
- `disk_temp_max`
- `fan_rpm_max`

### 7.5 Error / Degraded 页面

当 `source_ok=false` 或 HA 数据不可用：

```text
LINK WARN
WAIT TELEMETRY
```

当 Wi-Fi 未连接：

```text
WIFI LINK
CONNECTING...
```

当 HA API 未连接：

```text
HA LINK
STANDBY
```

## 8. 图标位使用建议

当前 VFD 驱动支持 7 个图标位。由于资料未完整标注每个图标的含义，MVP 先按“状态灯”使用，不强绑定图标语义。

建议映射：

- Icon 0: Wi-Fi / HA link
- Icon 1: source ok
- Icon 2: CPU hot
- Icon 3: GPU hot
- Icon 4: power high
- Icon 5: auto rotate
- Icon 6: alert

阈值建议：

- CPU hot: `cpu_temp >= 80`
- GPU hot: `gpu_temp >= 80`
- Power high: `system_power_estimated >= 250`
- Alert: `source_ok=false`

图标刷新应与页面刷新同步，不需要高频闪烁。可在异常状态下做 1Hz 慢闪。

## 9. 交互与刷新

### 9.1 刷新频率

建议：

- 数据从 HA 侧每 `1-2s` 更新即可。
- VFD 屏幕刷新不应过快，建议 `500ms-1000ms`。
- 页面轮播间隔建议 `4-6s`。

VFD 的观感来自稳定亮度和短文本切换，不来自高帧率动画。

### 9.2 动效策略

首版动效只保留：

- 页面切换时短暂清屏。
- 下排短文本滚动，限诊断/待机页面使用。
- 异常图标慢闪。

不建议：

- 跑马灯常驻主页面。
- 快速闪烁。
- 频繁全屏重写。

## 10. ESPHome 实现策略

建议新建独立 ESPHome 分支配置，不复用 SSD1322 的显示 YAML。

原因：

- VFD 是字符屏，不是像素屏。
- 驱动需要自定义 C/C++ include。
- 页面状态机不同。
- 字体、坐标、图形渲染概念不适用。

实现结构：

```text
esphome/
  vfd_016st106ink_demo.yaml
  includes/
    vfd_016st106ink/
      vfd.c
      vfd.h
```

ESPHome 侧职责：

- Wi-Fi / API / OTA。
- 从 HA 拉实体。
- 做单位换算与短文本格式化。
- 调用 VFD 驱动打印两行字符。
- 控制图标位。
- 控制页面轮播。

## 11. MVP 验收标准

硬件验收：

- ESP32-C3 能正常烧录。
- VFD 能上电点亮。
- 亮度可设置。
- 第一行 8 字符正常显示。
- 第二行 16 字符正常显示。
- 图标位至少能点亮/关闭。

数据验收：

- 能通过 HA 获取电脑状态。
- 数据断开时显示 `LINK WARN` 或等价状态。
- 温度、负载、功耗显示值和 HA 实体一致。
- 单位换算无明显错误。

视觉验收：

- 一屏内容不拥挤。
- 关键数字一眼可读。
- 页面切换有设备感。
- 整体观感接近复古音响/VFD 工业设备，而不是普通调试串口输出。

## 12. 风险与待确认

### 12.1 VFD 字符集

当前驱动直接写 ASCII 字符码，但 VFD 的 CGROM 字符集是否完整支持所有 ASCII 仍需实测。

首版应只使用：

- A-Z
- 0-9
- 空格
- `%`
- `.`
- `/`
- `-`

避免使用：

- 中文
- 特殊符号
- 箭头
- 复杂单位符号

### 12.2 引脚冲突

当前 VFD 示例使用：

- GPIO0
- GPIO1
- GPIO12
- GPIO18
- GPIO19

ESP32-C3 SuperMini 的启动/串口/JTAG 行为可能导致部分引脚在烧录或启动时有风险，需要实测确认。

### 12.3 HA 实体命名

另一个 agent 正在处理 HA integration，最终实体名可能变化。VFD ESPHome 配置应通过 substitutions 集中维护实体名。

### 12.4 供电能力

VFD 模块含升压电路，功耗可能明显高于 OLED。需要确认 USB 供电稳定性，尤其是高亮度下的启动电流。

## 13. 推荐下一步

1. 建立 `vfd_016st106ink_demo.yaml`。
2. 将现有 PlatformIO 驱动移植为 ESPHome include。
3. 先做纯本地静态文字测试：
   - `NOX READY`
   - `CPU62 GPU54 M60`
4. 再接入 HA 实体。
5. 实测 7 个 icon 位的真实图案并建立映射表。
6. 根据实测字符宽度与亮度，收敛最终 4 页面轮播逻辑。
7. 最后再决定是否加入待机跑马灯与异常慢闪。

## 14. 分支命名建议

建议分支或工作主题命名：

```text
esp32c3-vfd-monitor
```

该分支目标是形成一个轻量、可独立烧录、专注复古 VFD 观感的电脑状态监控屏，而不是替代 SSD1322 主项目。
