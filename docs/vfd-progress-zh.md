# VFD 分支进度整理

## 当前结论

`ESP32-C3 SuperMini + 016ST106INK` 的 VFD 分支已经从“可行性验证”进入“可用原型 + 视觉打磨”阶段。

目前不再是纯文档或纯思路阶段，而是已经具备：

- 屏幕点亮
- 驱动跑通
- Wi-Fi 联网
- ESPHome 接入
- Home Assistant 接入
- 电脑端实体联动
- 自定义字形能力
- 启动动画与页面过渡动画

## 2026-04-20 当前更新

VFD 终端程序已经收口到 ESPHome 设备侧控制模型:

- 数据源改为 `desktop_current_*` 聚合实体
- HA 亮度设置现在会贯穿启动动画、页面切换动画和最终锁定状态
- 页面切换动画结束后不会再把亮度硬编码恢复到 100%
- 数据从断开/等待恢复到可用后，会先播放 `boot_seq`，再显示数据页面
- Wi-Fi 信号强度以 `dBm` 诊断实体暴露在 VFD ESPHome 设备下

当前用户可见控制实体:

- `Display Power`
- `Brightness`
- `Animation`
- `Sleep Timeout`
- `Auto Rotate Interval`
- `Restart`
- `WiFi Signal`

## 已完成项

### 1. 硬件链路打通

已验证：

- ESP32-C3 SuperMini 可以正常烧录。
- VFD 模块可以正常点亮。
- VFD 模块通过当前驱动可输出两行字符。
- 亮度控制可用。
- 图标位控制可用。

当前 VFD 版本实际使用的引脚不是原始厂商 Demo 的默认值，而是针对 SuperMini 外露引脚重新适配：

- `RST = GPIO0`
- `CS = GPIO1`
- `CP = GPIO4`
- `DA = GPIO5`
- `EN = GPIO6`

这套映射已经通过点亮测试验证。

### 2. 最小点亮 Demo

文件：

- `esphome/vfd_016st106ink_smoke_test.yaml`

状态：

- 已完成
- 用于静态文字与基础轮播测试
- 用于验证供电、引脚、VFD 初始化、亮度和原生图标位

定位：

- 这是“硬件冒烟测试版”
- 后续仍应保留，作为回退和排障入口

### 3. ESPHome 自定义驱动移植

文件：

- `esphome/includes/vfd_016st106ink/vfd_016st106ink.h`

当前驱动能力：

- bit-bang 串行发送
- 亮度设置
- 两行字符写入
- 图标位控制
- 按字节打印
- `CGRAM` 自定义字形写入
- `5x5` 与 `7x5` 字形辅助写入
- 开机初始化

说明：

- 这个头文件已经不是最初的简单移植版
- 它已经成为 VFD 分支的核心驱动层

### 4. HA 数据接入

文件：

- `esphome/vfd_016st106ink_ha_monitor.yaml`

状态：

- 已完成接入
- 可以通过 ESPHome 从 HA 拉取电脑端实体
- 已与 `retro_monitor` 自定义集成联动

当前接入的电脑端实体包括：

- `sensor.desktop_current_cpu_temperature`
- `sensor.desktop_current_cpu_load`
- `sensor.desktop_current_cpu_power`
- `sensor.desktop_current_gpu_temperature`
- `sensor.desktop_current_gpu_load`
- `sensor.desktop_current_memory_usage`
- `sensor.desktop_current_fan_speed_max`
- `sensor.desktop_current_system_power_estimated`
- `binary_sensor.desktop_current_source_ok`

说明：

- 当前文件中已经出现“只接入部分实体”的收缩趋势
- 实现已不再是“把所有字段全塞进去”的早期状态

### 5. Home Assistant 服务端整理

路由器上的 Home Assistant Docker 已完成以下调整：

- `retro_monitor` 自定义集成已部署到 HA 配置目录
- 电脑端 telemetry host 已从内网域名改为固定 IP：
  - `<desktop-agent-ip>`
- OLED 旧服务链路保留
- VFD 新设备链路新增

结果：

- OLED 与 VFD 共用同一个 HA 服务端
- 电脑端数据源统一走当前 `retro_monitor` 服务端

### 6. Wi-Fi 兼容性修正

VFD 设备早期曾出现：

- `Auth Expired`
- 多 AP 同名 SSID 连接不稳定

当前已修正为：

- 固定 `BSSID`
- 固定 `channel`
- 启用 `fast_connect`
- 保持 `power_save_mode: none`

结果：

- `retro-vfd-monitor` 已可稳定连接 `<your-wifi-ssid>`
- 已成功回连 HA API

## 当前实现状态

### 1. 代码状态已经超出原始 PRD

文件：

- `docs/esp32c3-vfd-product-requirements-zh.md`

这份文档仍然是分支最完整的产品需求说明，但当前真实实现已经明显超出了其中“先做纯静态、再做 2-4 页简轮播”的阶段。

原因：

- 现在代码里已经出现启动动画、页面切换动画、自动熄屏、闪烁分隔符、特殊字形、双页面状态机等更高阶行为。

所以当前分支状态应理解为：

- PRD 仍有效
- 但实现已经进入“高级原型”阶段

### 2. 最新 VFD 终端实现

文件：

- `esphome/vfd_016st106ink_ha_monitor.yaml`

当前实现包含：

- `boot_seq`
  - 启动自检序列
  - 亮度渐入
  - 图标诊断
  - BIOS/HEX 风格加载动画
- `page_transition`
  - 淡出
  - Matrix Decode 风格过渡
  - 页面切换后再锁定
- 自动熄屏逻辑
- 数据恢复后自动上电逻辑
- 分隔符闪烁
- 图标位随状态变化
- 双页面数据结构

说明：

- 这份文件目前应视为“VFD 终端最新实现主文件”
- 它优先于最初的 VFD PRD 中的简单显示草案

### 3. 自定义字形系统

文件：

- `esphome/includes/vfd_016st106ink/vfd_016st106ink.h`

当前字形系统能力：

- `write_cgram`
- `write_cgram_bitmap`
- `write_cgram_7x5`
- `load_retro_glyphs`

当前已设计并加载的字形包括：

- `C`
- `P`
- `U`
- `G`
- 分隔符闪烁字形
- 特殊温度字符
- 功率符号

最近进展：

- 已经针对“字形横躺”问题引入列写入逻辑
- 已针对“底部不对齐”问题引入底边下沉策略

说明：

- 目前字形系统已经具备继续美术级微调的基础
- 后续优化重点不再是“能不能写自定义字形”，而是“字形美观程度”

## 当前未完成项

### 1. 实机观察亮度修复

亮度修复已经刷入 VFD，但仍需要在真实屏幕上做一次确认：

- 在 HA 中把 `Brightness` 调低
- 等待自动切页动画
- 确认动画结束后亮度保持为 HA 设定值

### 2. 后续视觉微调

当前 VFD 页面逻辑已冻结在双页终端风格，后续只建议做低风险微调：

- 自定义字形细节
- 功率符号可读性
- 图标位映射
- 动画节奏

### 3. 文档未完全跟上代码

现在最明显的问题是：

- `docs/esp32c3-vfd-product-requirements-zh.md` 偏产品定义
- 但没有一份文档准确描述当前 YAML 里已经实现到什么程度

本文件就是为了补这个缺口。

## 已验证结果

当前已验证过的真实结果：

- ESP32-C3 可通过 ESPHome 烧录
- VFD 已点亮
- VFD 已显示文字
- VFD 已连接 Wi-Fi
- VFD 已连接 HA API
- VFD 已读取电脑端实体
- `retro_monitor` 服务端已改用 `<desktop-agent-ip>`
- OLED 旧版服务未被破坏

## 当前风险

### 1. 代码快于文档

当前实现推进速度快于文档同步速度。后续如果继续高频改页面逻辑，建议同步更新本文件。

### 2. 字形迭代成本高

VFD 的 `CGRAM` 只有 8 个自定义字符位，字形设计必须非常克制，不能无限增加风格元素。

### 3. VFD 不是像素屏

任何“看起来像字体设计”的需求，最终都必须落回：

- 5x7 字符框
- 8 个自定义字符限制
- 两行固定字符位

所以设计空间有限，必须不断在“有设计感”和“可读性”之间取平衡。

## 推荐下一步

1. 冻结当前 VFD 页面结构  
   先决定最终是单页、双页还是双页加启动动画，不要继续同时保留多种路线。

2. 收口特殊字形  
   先把 `CPU / GPU / 分隔方块 / 功率符号 / 温度字符` 这 5 类字形定稿。

3. 再做一次“视觉验收版”固件  
   只为了看效果，不再同时改功能逻辑。

4. 文档同步  
   每次 VFD 版式定稿后，回写到：
   - `docs/esp32c3-vfd-product-requirements-zh.md`
   - 本文件

## 当前最重要的文件

如果只看最关键入口，优先级建议是：

1. `esphome/vfd_016st106ink_ha_monitor.yaml`
2. `esphome/includes/vfd_016st106ink/vfd_016st106ink.h`
3. `docs/esp32c3-vfd-product-requirements-zh.md`
4. `docs/project-progress-zh.md`

这 4 个文件基本能说明当前 VFD 分支和主线服务端的真实状态。
