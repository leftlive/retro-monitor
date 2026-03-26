# ESP32 OLED 端交接文档

本文档用于给后续 agent 快速接手当前 ESP32 + SSD1322 显示端开发。

## 当前目标

当前 ESP32 端负责：

- 通过 ESPHome 驱动 `SSD1322 256x64`
- 从 Home Assistant 订阅 Mac 和 Router 两套实体
- 在 OLED 上轮播显示：
  - `MAC PANEL`
  - `ROUTER PANEL`

当前主文件：

- `/Users/ian/retro-monitor/esphome/oled_display_p1_demo.yaml`

相关文档：

- `/Users/ian/retro-monitor/docs/ssd1322-16pin-4spi-wiring.md`
- `/Users/ian/retro-monitor/docs/oled-preview.md`

## 当前硬件与接线

模组：`SSD1322 16-pin 4SPI`

ESP32 接线固定为：

- `SCL` -> `GPIO18`
- `SDA` -> `GPIO23`
- `DC` -> `GPIO16`
- `RES` -> `GPIO17`
- `CS` -> `GPIO5`
- `RD` -> `GND`
- `WR` -> `GND`

注意：

- `GPIO5` 是 strapping pin，ESPHome 会持续告警
- 目前它能工作，但这仍是潜在风险点

## 当前显示结构

### Page 1: `MAC PANEL`

- 栏 1: `CPU`
  - 主值：`cpu_temp`
  - 辅助：`cpu_load`、`cpu_power`
- 栏 2: `MEM`
  - 主值：`memory_percent`
  - 辅助：`memory_used`、`disk_temp_max`
- 栏 3: `GPU`
  - 主值：`gpu_temp`
  - 辅助：`gpu_load`、`system_power_estimated`

### Page 2: `ROUTER PANEL`

- 栏 1: `NET`
  - 双大字：`router_net_down` / `router_net_up`
- 栏 2: `CPU`
  - 主值：`router_cpu_temp`
  - 辅助：`router_cpu_load`、`router_wan_uptime`
- 栏 3: `MEM`
  - 主值：`router_memory_percent`
  - 辅助：`router_memory_used`、`router_memory_total`

页头：

- 左侧：`NOX V1.09`
- 中间：`MAC PANEL` / `ROUTER PANEL`
- 右侧：`READY` / `ALERT`
- 右上角：闪烁状态块

## 当前刷新链路

当前系统时间点上的目标频率是：

- Go Agent 采样：`500ms`
- Home Assistant `retro_monitor`：
  - Mac：`scan_interval = 0.5`
  - Router：`scan_interval = 0.5`
- ESP32 OLED：
  - `display.update_interval = 500ms`

另外，ESP32 侧对大部分 Home Assistant sensor 都加了：

- `filters: throttle: 500ms`

目的是：

- 限制 ESPHome 接收状态的频率
- 避免被高频状态流直接淹没

## 当前 OLED 端只订阅的实体

为减轻压力，已经从 OLED 端移除了很多“没上屏”的订阅项。

当前保留的 Mac 侧订阅：

- `cpu_temp`
- `cpu_load`
- `cpu_power`
- `gpu_temp`
- `gpu_load`
- `memory_used`
- `memory_percent`
- `disk_temp_max`
- `system_power`
- `source_ok`

当前保留的 Router 侧订阅：

- `router_net_down`
- `router_net_up`
- `router_cpu_temp`
- `router_cpu_load`
- `router_memory_used`
- `router_memory_total`
- `router_memory_percent`
- `router_wan_uptime`
- `router_source_ok`

已经从 ESP32 YAML 中移除的订阅包括：

- `cpu_clock`
- `gpu_clock`
- `gpu_power`
- `fan_rpm_max`
- `router_net_util`
- `router_net_link`
- `router_wan_up`

## 已确认的结论

### 1. “屏幕不刷新”多数情况下不是 HA 停了

多次排查确认：

- HA 的 Mac / Router 实体仍在持续更新
- Go Agent 仍在正常提供 `/telemetry`
- 路由器 Router endpoint 也仍在正常返回数据

所以主要问题不在数据源。

### 2. “屏幕不刷新”也不总是 ESP32 全板离线

多次出现的情况是：

- `python3 -m esphome logs ...` 仍能连上设备
- ESPHome API 握手正常
- 但 OLED 画面已经阶段性停住

这说明：

- 设备活着
- 网络活着
- API 活着
- 但显示刷新链路或主循环被卡住

### 3. 自定义重绘调度方案不稳定

曾经尝试过：

- `display.update_interval: never`
- 通过 `on_value -> script.execute -> component.update`

结论：

- 这个方案长期运行不稳定
- 设备在线时也可能不再重绘
- 已经回退，不建议恢复

### 4. 状态流过密大概率是核心诱因之一

更可信的根因方向是：

- Home Assistant 状态更新过于频繁
- ESP32 同时处理：
  - Wi-Fi
  - ESPHome API 状态流
  - 多实体订阅
  - SSD1322 渲染
  - 字体绘制
  - 双页轮播
  - 闪烁页头元素

长时间运行后，显示链路可能进入“在线但不更新”的状态。

## 已做过的稳定性修复

### 已保留

- `logger.level: WARN`
- `logger.baud_rate: 0`
- `api.reboot_timeout: 2min`
- `wifi.reboot_timeout: 2min`
- `wifi.power_save_mode: none`
- `last_ha_state_ms` watchdog
- 如果 `5min` 收不到任何 HA 状态变化：
  - 自动执行 restart button

### 已撤销

- 自定义 `script + component.update` 事件驱动刷新

## 当前仍存在的问题

### 1. 阶段性不刷新问题未被彻底证明解决

虽然已经多轮减载，但“运行一段时间后画面停住”仍然是核心未结问题。

当前最新方向是：

- 更少订阅
- 更少状态频率
- 恢复原生 `display.update_interval`

但这需要继续观察。

### 2. 当前 `0.5s` 是高压档

现在整条链路已经提到 `0.5s`：

- HA 轮询 `0.5s`
- OLED 更新 `0.5s`
- Sensor throttle `0.5s`

这对 ESP32 来说已经接近高压模式。它也可能重新引入稳定性问题。

### 3. `retro-monitor-display.local` 有时能 API 连接，但 ICMP 不通

现象：

- ESPHome logs 可连接
- `ping retro-monitor-display.local` 有时丢包或完全不通

这说明不能把 `ping` 当成唯一在线判断。

### 4. `GPIO5` 仍是隐患

当前 `CS` 仍在 `GPIO5`，这是硬件层面的稳定性风险。

## 最近一次稳定可知的固件版本

最近一次通过 USB 实际刷入的版本：

- `config_hash = 0x95fea76a`
- `build_time_str = 2026-03-26 19:04:42 +0800`

但在此之后，配置仍继续被调整过；后续接手 agent 应重新以当前工作树为准，而不是只认这个 hash。

## 最近一次风险操作记录

在把 HA `scan_interval` 提到 `0.5s` 时，曾误伤过：

- `/mnt/nvme0n1-5/Configs/HomeAssistant/.storage/core.config_entries`

原因：

- 用了不安全的文本替换命令，破坏了 JSON entry 中的 `data` 字段

之后已经恢复并重新写对，但后续任何 agent 都应注意：

- 修改 `.storage/core.config_entries` 时必须先备份
- 必须用精确替换
- 不要再用松散的 `perl` 替换整段 JSON

## 当前推荐排查顺序

如果屏幕再次出现“不刷新”：

1. 先查 HA 数据是否仍在更新
   - Mac
   - Router
2. 再查 ESPHome API 是否还能握手
3. 如果 HA 正常、API 正常、画面不动：
   - 优先判断为“显示端冻结”
4. 不要先怀疑 Go Agent

## 当前推荐下一步

### 优先级 1：做真正的可观测诊断版固件

建议新增一份专门的诊断 YAML，而不是继续直接改正式版：

- `oled_display_debug.yaml`

诊断版应增加：

- 每次 `display` 刷新时打点
- 每次 page 切换打点
- 每次关键 sensor 到值打点
- 主循环卡顿告警

目标是区分：

- 是 sensor 状态不再进板子
- 还是状态进来了但 display 不再重绘
- 还是 page 轮播逻辑卡住

### 优先级 2：必要时回退到 `1s`

如果 `0.5s` 再次触发冻结：

- 保留 Go Agent `500ms`
- 保留 HA `0.5s` 或 `1s`
- 先把 OLED `display.update_interval` 回退到 `1s`
- sensor `throttle` 也回退到 `1s`

原因：

- 目前系统瓶颈更像在 ESP32，而不是后端

### 优先级 3：降低 UI 负载

可以考虑继续降载：

- 降低页头闪烁频率
- 降低轮播切页频率
- 移除部分进度条
- 减少大字重绘频率
- 在 Router 页减少文字排版复杂度

### 优先级 4：硬件引脚调整

若软件优化后仍有偶发异常，建议评估：

- 把 `CS` 从 `GPIO5` 挪到非 strapping pin

## 常用命令

### 配置检查

```bash
cd /Users/ian/retro-monitor
python3 -m esphome config esphome/oled_display_p1_demo.yaml
```

### OTA 刷写

```bash
cd /Users/ian/retro-monitor
python3 -m esphome run esphome/oled_display_p1_demo.yaml --device retro-monitor-display.local
```

### USB 刷写

```bash
cd /Users/ian/retro-monitor
python3 -m esphome run esphome/oled_display_p1_demo.yaml --device /dev/cu.usbserial-1470
```

### 查看设备日志

```bash
cd /Users/ian/retro-monitor
python3 -m esphome logs esphome/oled_display_p1_demo.yaml --device retro-monitor-display.local
```

## 给后续 agent 的直接建议

不要先从 HA 或 Go Agent 下手。  
如果问题再次出现，优先把 ESP32 端做成“可观测”而不是继续盲调刷新率。

最推荐的动作顺序：

1. 新建诊断版 YAML
2. 给 display 刷新、page 切换、关键 sensor 到值加日志
3. 长时间观察冻结前后的设备日志
4. 再决定是否回退 `0.5s -> 1s`
