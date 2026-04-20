# P2 页面规划：折线趋势页

本文档用于规划 OLED `P2` 页面。该页面的重点不是继续堆叠更多瞬时数字，而是通过折线与轻量动态元素，把“功率、负载、温度、流量”的变化趋势直观呈现出来。

## 目标

P2 的主要目标：

- 强化“动态感”和“监控感”
- 让用户在远距离下也能看出系统状态变化
- 不破坏当前已经跑通的 `P1` 主信息页
- 在 ESP32 稳定性优先的前提下，逐步引入趋势图

P2 的设计原则：

- `P1` 负责读数
- `P2` 负责趋势和氛围
- `P2` 以效果呈现为主，但不能明显增加 OLED 停刷风险

## 当前前提

当前系统已经具备：

- Mac desktop telemetry
- Router telemetry
- Home Assistant `display payload`
- ESP32 双页轮播
- `MAC PANEL` / `ROUTER PANEL` 两个 `P1` 型页面

当前 OLED 的主文件是：

- `/Users/ian/retro-monitor/esphome/oled_display_p1_demo.yaml`

当前 Home Assistant 侧已经有一个为 OLED / VFD 共用的电脑聚合 payload：

- `sensor.desktop_current_display_payload`
- `sensor.istoreos_display_payload`

当前 payload 是“单帧快照”，还不包含历史数组。

## P2 页面定位

建议将 `P2` 先定义为：

- `P2 TREND`

第一阶段只做 **Mac 趋势页**，暂不把 Router 趋势塞进首版 P2。

理由：

- Mac 端已经有更丰富的功率和温度数据
- `cpu_power / gpu_load / system_power_estimated / memory_percent` 的趋势效果更明显
- Router 趋势可以作为后续 `P3` 或 `P2R` 的单独扩展

## 推荐的信息架构

### 方案 A：主推荐方案

P2 分为三层：

- 顶部：页头
- 中部：两条核心折线图
- 底部：3 个小指标和状态标签

建议布局：

1. 顶部页头
- 左：`NOX V1.09`
- 中：`P2 TREND`
- 右：`LIVE`
- 最右角：闪烁状态块

2. 中部图区
- 上图：`SYSTEM POWER`
- 下图：`GPU LOAD` 或 `CPU TEMP`

3. 底部摘要
- `CPU 058W`
- `GPU 021%`
- `MEM 046%`

适合优先展示的指标：

- 图 1：`system_power_estimated`
- 图 2：`gpu_load`

备选组合：

- `cpu_power` + `gpu_load`
- `cpu_temp` + `memory_percent`

### 为什么不推荐首版做三图并列

在 `256x64` 上同时画三张折线图的问题很明显：

- 图区高度不够
- 标签和趋势线会互相抢空间
- 视觉效果会变得碎

两条横向折线更适合这块长条屏。

## 实现路线：两阶段

## 阶段 1：ESP32 本地 Ring Buffer 原型

这是最快能把效果做出来的路线。

### 思路

继续复用当前 HA 发来的单帧 payload，在 ESP32 本地维护一组固定长度 ring buffer。

例如：

- `system_power_estimated` -> 32 点历史
- `gpu_load` -> 32 点历史
- `memory_percent` -> 32 点历史

ESP32 每次收到新 payload 时：

- 把最新值写入 buffer
- 更新写入位置
- 页面渲染时按 buffer 画折线

### 优点

- 开发最快
- 不需要改 Agent
- 不需要先扩 Home Assistant payload 协议
- 能立刻验证“折线效果在这块屏上是否成立”

### 缺点

- 历史只存在 ESP32 内存里
- 重启即丢失
- 页面切换/断连时趋势连续性较差
- 多设备统一显示逻辑会分散到固件端

### 适合用途

- P2 第一版视觉原型
- 快速确定图线密度、线宽、采样点数、标签布局

## 阶段 2：Home Assistant 聚合趋势 Payload 正式版

这是正式版的推荐实现。

### 思路

由 Home Assistant 插件或聚合层维护短期历史序列，再输出一个专门给 OLED 用的趋势 payload。

建议新增：

- `Display Trend Payload`

例如对 desktop profile：

- `sensor.desktop_current_display_trend_payload`

内容不再是单帧快照，而是压缩后的短历史窗口。

### 推荐 payload 结构

不要继续把长 JSON 历史数组塞进普通 `state` 字符串。

推荐方案：

- `state` 保持短字符串，例如 `ok`
- 历史数据放进 attribute，例如：
  - `sp`: system power 历史数组
  - `gl`: gpu load 历史数组
  - `mp`: memory percent 历史数组
  - `ts`: 样本时间间隔或时间戳

原因：

- Home Assistant 普通 state 长度不适合承载完整趋势数组
- attribute 更适合携带稍长的图形数据

### 优点

- 历史由中间层统一维护
- ESP32 固件逻辑更轻
- 重启后趋势更快恢复
- 后续可扩展到 Router / Windows / 多设备

### 缺点

- 需要修改 HA 集成
- 需要新增 payload 契约
- 首版开发量高于本地 ring buffer

### 适合用途

- P2 正式版本
- 多设备长期演进

## 推荐实施决策

我的建议不是二选一，而是：

1. 先做阶段 1，本地 ring buffer 把 P2 效果跑起来
2. P2 视觉定型后，再做阶段 2，把历史上移到 HA

这样可以把“界面验证”与“数据架构收口”拆开，降低风险。

## 折线图渲染建议

## 图线数量

首版建议：

- 每页只画 2 条主折线

不建议首版：

- 3 条以上同时叠加
- 面积图
- 平滑曲线
- 抗锯齿

原因：

- SSD1322 256x64 可用像素有限
- ESPHome lambda 渲染越复杂，越容易重新引入停刷问题

## 点数

建议点数：

- `24` 或 `32` 点

原因：

- 足够体现走势
- 对 256 像素宽度比较友好
- 不会让折线过于密集

## 采样间隔

建议图线采样节奏：

- 与当前有效显示节奏保持一致
- 首版以 `500ms` 或 `1s` 为单位

建议先用：

- `1s * 32 点`

也就是大约展示最近 `32s` 的变化。

这样比 `500ms * 32 点` 更稳，趋势也更容易看懂。

## 线条风格

建议：

- 单像素折线
- 不做填充
- 只用亮度层次区分主次

例如：

- 主线：亮白
- 次线：中灰
- 基准线/边框：暗灰

## 页面视觉建议

P2 既然以效果为主，视觉语言应和 P1 有区别。

建议：

- 保留相同页头风格，保证系列一致
- 减少竖向栏位分割线
- 中心区域改成更宽的图形面
- 把数字做成图形的注释，而不是主角

推荐视觉重心：

- 图优先
- 数字次之
- 装饰性微元素少量保留

## P2 首版字段建议

首版建议只用这些字段：

- `system_power_estimated`
- `gpu_load`
- `memory_percent`
- `cpu_power`

推荐组合：

- 主图：`system_power_estimated`
- 次图：`gpu_load`
- 底部摘要：`cpu_power` / `memory_percent`

原因：

- 变化明显
- 视觉表现力强
- 与“功率等参数”的目标最贴近

## 不建议首版直接放进 P2 的内容

- Router 上下行趋势
- WAN uptime
- disk temperature
- 过多文字标签
- 历史最大值/最小值说明
- 多设备切换逻辑

这些都适合后续版本，不适合 P2 第一版。

## 对当前代码的影响范围

阶段 1 主要改：

- `/Users/ian/retro-monitor/esphome/oled_display_p1_demo.yaml`

需要新增：

- `P2 TREND` 页面
- ring buffer globals
- 写入逻辑
- 折线绘制函数
- 页面轮播接入

阶段 2 主要改：

- `/Users/ian/retro-monitor/homeassistant/custom_components/retro_monitor/sensor.py`
- 可能还包括：
  - `const.py`
  - `entity.py`
  - `docs/homeassistant-communication-spec.md`

## 风险与约束

当前最关键约束不是“怎么画线”，而是“不要把 ESP32 再压崩”。

因此首版 P2 必须遵守：

- 不增加大量新的实体订阅
- 不引入高频复杂动画
- 不用抗锯齿或逐帧插值
- 不恢复自定义高频 `component.update` 调度链

## 推荐实施顺序

1. 先在本地 OLED preview 工具中做一版 `P2 TREND` 静态构图
2. 在 ESP32 端用本地 ring buffer 做出第一版动态折线
3. 调整折线点数、上下图比例、底部摘要布局
4. 观察稳定性
5. 如果视觉和稳定性都成立，再把趋势历史上移到 HA 聚合 payload

## 当前结论

P2 的正确方向不是“继续往 P1 里塞更多值”，而是：

- 用少量高变化指标
- 做更强的趋势感
- 让页面承担“状态氛围”和“系统脉搏”的角色

当前最合理的实施路径是：

- **先用 ESP32 本地 ring buffer 做视觉原型**
- **再把历史趋势正式上移到 Home Assistant**

这条路线风险最低，也最符合当前项目的开发节奏。
