# Windows Agent 接手与测试文档

本文档用于把 Windows 平台的数据采集端交给其他 agent 或工程师继续接手，并明确：

- Windows 版 agent 如何在目标机器上运行与验证
- Windows 版和 macOS 版在 Home Assistant 通信逻辑上是否一致
- 当前 OLED 的 `P1` 页面能否直接切换为 Windows 数据
- 如果希望在 Mac 不启动时由 Windows 接管 `P1`，应如何实现

## 1. 当前结论

### 1.1 HA 通信逻辑是否一致

**一致。**

只要 Windows agent 输出的是当前固定的 desktop telemetry schema，Home Assistant 端会按和 macOS 完全相同的方式处理：

- 同样是 `GET /telemetry`
- 同样返回一个完整 JSON object
- 同样要求所有字段存在，缺失值为 `null`
- 同样走 `retro_monitor` 插件里的 desktop profile 校验逻辑

也就是说，**HA 集成本身不区分“这是 Mac 还是 Windows”，它只区分 payload 是否属于 desktop schema。**

当前验证逻辑位置：

- `/Users/ian/retro-monitor/homeassistant/custom_components/retro_monitor/validator.py`

其中 desktop payload 只要求具备这组字段：

- `device_id`
- `hostname`
- `platform`
- `timestamp`
- `source_ok`
- `cpu_temp`
- `cpu_load`
- `cpu_clock`
- `cpu_power`
- `gpu_temp`
- `gpu_load`
- `gpu_clock`
- `gpu_power`
- `memory_used_mb`
- `memory_total_mb`
- `memory_percent`
- `fan_rpm_max`
- `fan_rpm_avg`
- `disk_temp_max`
- `disk_activity_percent`
- `net_up_bps`
- `net_down_bps`
- `system_power_estimated`

因此，**Windows agent 只要遵守这份 schema，就能直接作为第二台 desktop 设备接入 HA。**

### 1.2 Mac 不启动时，Windows 数据是否能直接替换 P1

**可以，但当前不是自动替换，只能“手动切换”或“通过 HA 中间层做抽象”。**

原因是当前 OLED 的 `P1` 页面使用的是写死的 HA 实体名。

当前配置文件：

- `/Users/ian/retro-monitor/esphome/oled_display_p1_demo.yaml`

里面的 `P1` 数据绑定目前是：

- `sensor.iandeimac_local_cpu_temperature`
- `sensor.iandeimac_local_gpu_temperature`
- `sensor.iandeimac_local_memory_usage`
- 以及其它 `sensor.iandeimac_local_*`

这意味着：

- 如果 Mac 不启动，这些实体会变成 `unavailable`
- OLED 不会自动去找 Windows 那台 desktop 设备的数据

所以当前状态是：

- **协议兼容：是**
- **HA 插件兼容：是**
- **OLED 当前配置自动切换：否**

## 2. 推荐的接手测试方式

建议先按“最少改动”的方式验证 Windows agent，不要一开始就改 OLED 逻辑。

### 阶段 A：只验证 Windows agent 是否能进 HA

目标：

- Windows agent 在本机正常输出 `/telemetry`
- HA 能新增一条 Windows desktop config entry
- HA 能正常生成 Windows desktop 实体

### 阶段 B：再决定如何让 OLED 使用 Windows 数据

推荐分两种策略：

#### 策略 1：直接把 P1 改绑到 Windows 实体

适合：

- 当前主要只想测试 Windows 端
- 短期内不需要 Mac 和 Windows 动态切换

做法：

- 把 `oled_display_p1_demo.yaml` 顶部 substitutions 中的 `ha_cpu_temp`、`ha_gpu_temp`、`ha_memory_percent` 等从 `sensor.iandeimac_local_*` 改成 Windows 实体名
- 重新刷 OLED 固件

优点：

- 最简单
- 开发量最低

缺点：

- 以后如果再切回 Mac，还要再改一遍 YAML

#### 策略 2：在 HA 中做一组“稳定别名实体”

适合：

- 后续希望 Mac / Windows 可以互相切换
- 不希望 OLED 每次换数据源就重新改 YAML

做法：

- 在 HA 中创建一组 template sensors 或 helpers，例如：
  - `sensor.desktop_current_cpu_temperature`
  - `sensor.desktop_current_gpu_temperature`
  - `sensor.desktop_current_memory_usage`
  - `binary_sensor.desktop_current_source_ok`
- 由 HA 决定这些稳定实体当前指向 Mac 还是 Windows
- OLED 始终只绑定这组稳定实体

优点：

- OLED 固件不需要来回改
- 后续最容易做“当前桌面设备来源切换”

缺点：

- 需要额外做一层 HA 抽象

### 推荐结论

当前建议：

1. **先用策略 1 验证 Windows agent**
2. Windows 端稳定后，再升级到策略 2

这是当前性价比最高的路径。

## 3. Windows Agent 当前代码位置

Windows 版 agent 当前在：

- `/Users/ian/retro-monitor/windows-agent/`

关键文件：

- `/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Program.cs`
- `/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/WindowsTelemetryProvider.cs`
- `/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/HardwareMonitorReader.cs`
- `/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/SystemMetricsReader.cs`
- `/Users/ian/retro-monitor/docs/windows-agent-integration.md`

## 4. Windows 机器上的测试步骤

### 4.1 环境要求

目标 Windows 机器需要：

- Windows 10 / 11
- `.NET 8 SDK`
- 最好具备管理员权限

说明：

- 当前这套代码是在一台只有 .NET Runtime、没有 SDK 的环境下生成的
- 所以代码已经落地，但**还没有在本机完成编译**
- 最终 build 和验证必须在 Windows 机器上做

### 4.2 首次运行

进入项目：

```powershell
cd C:\path\to\retro-monitor\windows-agent\RetroMonitor.WindowsAgent
dotnet restore
dotnet build
```

先查看传感器原始列表：

```powershell
dotnet run -- --dump-sensors
```

目的：

- 确认这台 Windows 机器上 `LibreHardwareMonitor` 能看到哪些传感器
- 特别确认：
  - CPU 温度
  - GPU 温度 / 负载
  - 风扇
  - 磁盘温度

再启动 agent：

```powershell
dotnet run
```

打开：

```text
http://127.0.0.1:8125/telemetry
```

检查返回是否满足：

- JSON 格式正确
- 所有 schema 字段都存在
- 缺失字段为 `null`
- `platform` 为 `windows`

## 5. 接入 Home Assistant 的步骤

Windows agent 跑起来后，在 HA 里新增一个 `Retro Monitor` 配置项：

- `Host`: Windows 机器地址或主机名
- `Port`: `8125`
- `Path`: `/telemetry`
- `Scan interval`: 建议先用 `1`

接入成功后，HA 会生成一组新的 desktop 实体。

这些实体名会以 Windows 的 `hostname` 为前缀，而不是 `iandeimac_local_*`。

例如如果 Windows 主机名是 `winbox`，实体可能类似：

- `sensor.winbox_cpu_temperature`
- `sensor.winbox_gpu_temperature`
- `sensor.winbox_memory_usage`
- `binary_sensor.winbox_data_source_ok`

## 6. 和 macOS 版本的关键差异

### 通信层

**没有本质差异。**

Windows 版和 macOS 版对 HA 来说都只是一个 desktop telemetry endpoint。

### 采集层

差异主要在底层实现：

- macOS：当前主线是 Go agent + 原生底层接口
- Windows：当前主线是 `.NET + LibreHardwareMonitor + Windows counters`

但这对 HA 不重要，只要输出 schema 一样即可。

## 7. 当前不建议做的事

在 Windows agent 还没有验证跑通前，不建议：

- 先改 HA 插件协议
- 先改 OLED 页面结构
- 先做 Mac / Windows 自动切换逻辑
- 先要求 Windows 端完全追平所有极端硬件字段

先把这三件事做成：

1. Windows agent 能编译
2. `/telemetry` 正常
3. HA 正常生成实体

然后再继续 OLED 侧切换。

## 8. 推荐下一步

最推荐的顺序是：

1. 在 Windows 机器上编译并运行 agent
2. 用 `--dump-sensors` 锁定首台机器的传感器映射
3. 接入 HA，确认实体完整
4. 临时把 `P1` 改绑到 Windows 实体，验证 OLED 显示
5. 如果验证通过，再设计“Mac / Windows 共用 P1 的 HA 抽象层”

## 9. 最终结论

- **Windows 版与 macOS 版在 HA 通信逻辑上是一致的**
- **Windows 数据可以替换 P1，但当前不是自动替换**
- **当前最稳的做法是：先手动改绑 P1 到 Windows 实体做验证**
- **如果以后要长期支持 Mac / Windows 两套桌面设备共用 P1，建议在 HA 中增加稳定别名实体层**
