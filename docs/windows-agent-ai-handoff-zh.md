# Windows Agent AI 接手文档

更新日期: 2026-04-28

本文档给后续在 **Windows 系统** 上继续工作的 AI agent 使用。

目标不是介绍项目背景，而是让接手方在**没有当前会话上下文**的情况下，能直接继续完成：

- Windows 端编译
- 传感器验证
- `/telemetry` 输出校验
- 接入 Home Assistant
- 为后续 OLED / VFD 共用电脑状态源做好验证

---

## 1. 你接手时应该先知道的事实

### 1.1 当前真实状态

Windows 端不是空白工程，已经有一套独立实现骨架，路径在：

- [windows-agent/README.md](/Users/ian/retro-monitor/windows-agent/README.md)
- [Program.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Program.cs)
- [WindowsTelemetryProvider.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/WindowsTelemetryProvider.cs)
- [HardwareMonitorReader.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/HardwareMonitorReader.cs)
- [SystemMetricsReader.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/SystemMetricsReader.cs)
- [TelemetrySampler.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/TelemetrySampler.cs)
- [TelemetrySnapshot.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Models/TelemetrySnapshot.cs)
- [AgentOptions.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Configuration/AgentOptions.cs)
- [RetroMonitor.WindowsAgent.csproj](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/RetroMonitor.WindowsAgent.csproj)
- [appsettings.json](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/appsettings.json)

### 1.2 当前最重要的判断

Windows 端目前处于：

- 架构已定
- 代码骨架已落地
- 但**尚未在真实 Windows 机器上完成首轮编译与传感器验证**

因此你不应该假设：

- 项目已经编译通过
- 传感器名称匹配规则已经正确
- `LibreHardwareMonitor` 一定能在目标机器上拿到完整 CPU / GPU / 风扇 / 磁盘温度

### 1.3 当前整体系统已经为 Windows 做好的准备

Home Assistant 和显示端已经按“多电脑源”准备好了：

- `retro_monitor` 负责遥测数据，不再负责显示控制
- HA 中存在 `desktop_current_*` 聚合层
- OLED 与 VFD 后续都消费 `desktop_current_*`

这意味着：  
**只要 Windows agent 输出符合既有 desktop schema，就可以接入现有系统，而不需要再改 OLED/VFD 主逻辑。**

参考文档：

- [windows-agent-integration.md](/Users/ian/retro-monitor/docs/windows-agent-integration.md)
- [project-progress-zh.md](/Users/ian/retro-monitor/docs/project-progress-zh.md)
- [telemetry-spec.md](/Users/ian/retro-monitor/docs/telemetry-spec.md)

---

## 2. 必须遵守的接口契约

Windows agent 必须继续暴露：

- `GET /telemetry`
- 返回一个完整 JSON object
- 所有 schema 字段都必须存在
- 缺失值统一为 `null`

当前 schema 的核心字段在 [TelemetrySnapshot.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Models/TelemetrySnapshot.cs) 已经建模完成，字段包括：

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

不要改字段名。不要省略字段。

---

## 3. 当前代码设计

### 3.1 运行模型

入口在 [Program.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Program.cs)。

当前模型是：

- `ASP.NET Core` 提供 HTTP 服务
- 后台 `TelemetrySampler` 固定周期采样
- `/telemetry` 返回最近缓存快照
- 不是请求驱动采样

当前默认参数在 [appsettings.json](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/appsettings.json)：

- `Host = 0.0.0.0`
- `Port = 8125`
- `SampleIntervalMilliseconds = 500`
- `SlowIntervalMilliseconds = 2000`
- `SystemPowerBaseWatts = 20.0`

### 3.2 采集职责分层

#### `SystemMetricsReader`

文件：

- [SystemMetricsReader.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/SystemMetricsReader.cs)

负责：

- `cpu_load`
- `memory_used_mb`
- `memory_total_mb`
- `memory_percent`
- `disk_activity_percent`
- `net_up_bps`
- `net_down_bps`

实现方式：

- `PerformanceCounter`
- `GlobalMemoryStatusEx`
- `NetworkInterface.GetAllNetworkInterfaces()`

注意：

- 网络速率当前是通过两次采样的字节差计算，输出单位是 `bit/s`
- 首次采样网络值可能是 `null`

#### `HardwareMonitorReader`

文件：

- [HardwareMonitorReader.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/HardwareMonitorReader.cs)

负责：

- `cpu_temp`
- `cpu_clock`
- `cpu_power`
- `gpu_temp`
- `gpu_load`
- `gpu_clock`
- `gpu_power`
- `fan_rpm_max`
- `fan_rpm_avg`
- `disk_temp_max`
- 直接系统功耗候选值

实现方式：

- `LibreHardwareMonitorLib`

这里有最重要的风险：

- 现在的匹配规则是启发式的
- 必须通过目标 Windows 机器上的真实传感器名称来验证

#### `WindowsTelemetryProvider`

文件：

- [WindowsTelemetryProvider.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/WindowsTelemetryProvider.cs)

负责：

- 组装最终 `TelemetrySnapshot`
- 合并 fast/slow metrics
- 设置 `timestamp`
- 设置 `device_id`
- 估算 `system_power_estimated`
- 判断 `source_ok`

当前 `system_power_estimated` 策略：

- 优先使用 `LibreHardwareMonitor` 暴露的直接整机/总功耗类传感器
- 拿不到时回退到：
  - `cpu_power + gpu_power + base_watts`

当前 `source_ok` 判定策略：

- 只要核心指标里有足够多可用值，就会设为 `true`

---

## 4. Windows 机器上的第一轮工作顺序

按这个顺序做，不要跳步骤。

### 第一步：确认环境

在 Windows 机器上确认：

1. `dotnet --info`
2. 确保是 `.NET 8 SDK`，不是只有 runtime
3. 确保可以访问本仓库

最低要求：

- Windows 10 / 11
- `.NET 8 SDK`
- 最好管理员权限

### 第二步：编译

在 Windows PowerShell 中：

```powershell
cd C:\path\to\retro-monitor\windows-agent\RetroMonitor.WindowsAgent
dotnet restore
dotnet build
```

目标：

- 先拿到第一轮编译是否通过
- 如果失败，优先修项目依赖、命名空间、包版本和平台兼容问题

### 第三步：先做传感器枚举

先不要急着直接跑服务，先看传感器：

```powershell
dotnet run -- --dump-sensors
```

当前 `Program.cs` 已支持这个模式。

目标是确认目标机器上这些东西到底有没有被 `LibreHardwareMonitor` 暴露出来：

- CPU 温度
- CPU 功率
- CPU 时钟
- GPU 温度
- GPU 负载
- GPU 功率
- 风扇
- 磁盘温度
- 任何 “System / Total / Input” 类功耗传感器

### 第四步：锁第一台机器的传感器规则

看 `--dump-sensors` 输出后，重点审查 [HardwareMonitorReader.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/HardwareMonitorReader.cs) 中这些方法是否匹配到了真实传感器：

- `PickCpuTemperature`
- `PickCpuClock`
- `PickCpuPower`
- `PickGpuMetric`

如果目标机器的传感器名称和当前 heuristics 不匹配，要先修这些规则。

不要直接在 HA 里接一个“字段大量为 null”的版本。

### 第五步：直接跑 HTTP 服务

```powershell
dotnet run
```

然后访问：

```text
http://127.0.0.1:8125/telemetry
```

检查：

- JSON 是否完整
- 所有 schema 字段是否都存在
- 缺失字段是否是 `null`
- `platform` 是否是 `windows`
- `device_id` / `hostname` 是否稳定
- `source_ok` 是否符合预期

### 第六步：接入 Home Assistant

在 HA 中新增一个 `Retro Monitor` 条目：

- `Host`: Windows 机器 IP
- `Port`: `8125`
- `Path`: `/telemetry`
- `Scan interval`: 先用 `1`

接入后确认：

- 是否创建了一组 Windows desktop 实体
- 这些实体是否都在线
- `desktop_current_*` 是否能正确选择 Windows 作为当前源

---

## 5. 在 Windows 机器上必须优先关注的具体问题

### 5.1 `PerformanceCounter` 可用性

当前代码用了 `PerformanceCounter`：

- CPU
- Disk

在某些系统上可能：

- 首次值异常
- 缺权限
- 类别不存在

如果出现问题，先确认是环境问题还是代码问题。

### 5.2 `LibreHardwareMonitor` 传感器命名不一致

这是首机验证中最可能需要改的地方。

不要假设：

- 所有机器都有 `Package`
- 所有 GPU 功耗都叫 `Total`
- 所有 CPU 时钟都叫 `Core Average`

必须基于 `--dump-sensors` 输出修规则。

### 5.3 `source_ok` 语义

当前 `source_ok` 在 [WindowsTelemetryProvider.cs](/Users/ian/retro-monitor/windows-agent/RetroMonitor.WindowsAgent/Services/WindowsTelemetryProvider.cs) 里比较宽松。

接手时要评估：

- 当前规则是否过宽
- 是否会在关键指标全空时仍误报 `true`

但不要一开始就收得过严。  
目标是先让它稳定反映“这台机器的数据是否足够用于显示端”。

### 5.4 `system_power_estimated`

当前这是估算值，不是精确硬件实测。

优先级：

1. 先确认有没有直接系统功耗类传感器
2. 没有就接受当前 `cpu + gpu + base`
3. 不要为了追求整机功耗精度阻塞整个 Windows 端首轮接入

---

## 6. 你不应该做的事

在首轮 Windows 接手中，不建议一开始就做这些：

- 不要先改 OLED / VFD 固件逻辑
- 不要先发散去做 UI 设计
- 不要先做 Windows/macOS 自动切源花活
- 不要先做服务安装脚本美化
- 不要先追求所有字段全部精确可用

首轮目标只有三个：

1. 编译通过
2. `/telemetry` 输出完整 schema
3. HA 接入成功并能进入 `desktop_current_*`

---

## 7. 推荐验收标准

当你认为 Windows 端完成“第一轮可用”时，至少应满足：

1. `dotnet build` 在真实 Windows 机器上通过
2. `dotnet run -- --dump-sensors` 可以输出传感器清单
3. `dotnet run` 后 `/telemetry` 正常返回完整 JSON
4. `platform == "windows"`
5. 关键字段至少有一批真实值：
   - `cpu_temp`
   - `cpu_load`
   - `gpu_temp`
   - `gpu_load`
   - `memory_percent`
   - `net_up_bps`
   - `net_down_bps`
6. HA 能接入该 Windows source
7. `desktop_current_*` 能在只有 Windows 在线时正常工作

---

## 8. 建议你完成后的输出格式

接手完成后，建议用这个结构汇报：

1. 编译是否通过  
2. `--dump-sensors` 看到了哪些关键传感器  
3. `/telemetry` 实测样本  
4. 哪些字段已有真实值  
5. 哪些字段仍为 `null`  
6. HA 接入是否成功  
7. `desktop_current_*` 是否选到了 Windows  
8. 下一步还缺什么

---

## 9. 当前最有价值的下一步

如果你是后续 AI agent，最应该优先做的只有这一件事：

**在真实 Windows 机器上完成第一轮 `dotnet build -> --dump-sensors -> /telemetry -> HA 接入` 闭环。**

只要这个闭环跑通，后面的 OLED/VFD、HA 聚合层、双电脑源切换都已经有现成落点。
