# Windows Agent AI 维护接手文档

更新日期: 2026-05-16

本文档给后续在 **Windows 系统** 上维护 Retro Monitor Windows 采集端的 AI agent 使用。

Windows 采集端已经进入可用维护状态。当前状态是：

- 代码实现已完成
- 已在 Windows 目标机完成编译测试
- 已完成真实传感器枚举
- 已验证 `/telemetry` 输出
- 已验证 Windows Service 安装和启动
- 已验证 Home Assistant 接入
- 已验证 `desktop_current_*` 聚合层可消费 Windows 数据

注意：当前 macOS 工作区只有 .NET runtime，没有 .NET SDK，不能在本机复跑 Windows 编译测试。Windows 端验证以目标 Windows 机器结果为准。

---

## 1. 当前真实状态

Windows 端路径：

- [windows-agent/README.md](../windows-agent/README.md)
- [Program.cs](../windows-agent/RetroMonitor.WindowsAgent/Program.cs)
- [WindowsTelemetryProvider.cs](../windows-agent/RetroMonitor.WindowsAgent/Services/WindowsTelemetryProvider.cs)
- [HardwareMonitorReader.cs](../windows-agent/RetroMonitor.WindowsAgent/Services/HardwareMonitorReader.cs)
- [SystemMetricsReader.cs](../windows-agent/RetroMonitor.WindowsAgent/Services/SystemMetricsReader.cs)
- [TelemetrySampler.cs](../windows-agent/RetroMonitor.WindowsAgent/Services/TelemetrySampler.cs)
- [TelemetrySnapshot.cs](../windows-agent/RetroMonitor.WindowsAgent/Models/TelemetrySnapshot.cs)
- [AgentOptions.cs](../windows-agent/RetroMonitor.WindowsAgent/Configuration/AgentOptions.cs)
- [RetroMonitor.WindowsAgent.csproj](../windows-agent/RetroMonitor.WindowsAgent/RetroMonitor.WindowsAgent.csproj)
- [appsettings.json](../windows-agent/RetroMonitor.WindowsAgent/appsettings.json)
- [install-windows-agent.ps1](../windows-agent/install-windows-agent.ps1)
- [package-windows-agent.ps1](../windows-agent/package-windows-agent.ps1)
- [installer/install.ps1](../windows-agent/installer/install.ps1)
- [installer/uninstall.ps1](../windows-agent/installer/uninstall.ps1)

当前实现：

- `.NET 8`
- `ASP.NET Core`
- `Microsoft.Extensions.Hosting.WindowsServices`
- `LibreHardwareMonitorLib`
- 后台固定周期采样
- `/telemetry` 返回缓存快照
- `--dump-sensors` 输出传感器清单
- 支持源码发布安装和 zip 打包安装

---

## 2. 已验证闭环

Windows 目标机已完成以下闭环：

1. `dotnet restore`
2. `dotnet build`
3. `dotnet run -- --dump-sensors`
4. `dotnet run`
5. 访问 `http://127.0.0.1:8125/telemetry`
6. 校验完整 desktop schema
7. 确认 `platform == "windows"`
8. 安装并启动 Windows Service
9. 在 Home Assistant 中新增 Windows source
10. 确认 `desktop_current_*` 聚合层可消费 Windows 数据

这意味着 Windows 端已经达到“可用完成态”，后续工作以维护和回归验证为主。

---

## 3. 必须保持的接口契约

Windows agent 必须继续暴露：

- `GET /telemetry`
- 返回一个完整 JSON object
- 所有 schema 字段都必须存在
- 缺失值统一为 `null`

核心字段在 [TelemetrySnapshot.cs](../windows-agent/RetroMonitor.WindowsAgent/Models/TelemetrySnapshot.cs) 建模：

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

不要改字段名。不要省略字段。新增字段时必须保持旧字段兼容。

参考：

- [windows-agent-integration.md](windows-agent-integration.md)
- [telemetry-spec.md](telemetry-spec.md)
- [project-progress-zh.md](project-progress-zh.md)

---

## 4. 当前代码设计

### 4.1 运行模型

入口：

- [Program.cs](../windows-agent/RetroMonitor.WindowsAgent/Program.cs)

模型：

- `ASP.NET Core` 提供 HTTP 服务
- 后台 `TelemetrySampler` 固定周期采样
- `/telemetry` 返回最近缓存快照
- 不是请求驱动采样
- `--dump-sensors` 走独立传感器枚举模式

默认参数：

- `Host = 0.0.0.0`
- `Port = 8125`
- `SampleIntervalMilliseconds = 500`
- `SlowIntervalMilliseconds = 2000`
- `SystemPowerBaseWatts = 20.0`

### 4.2 `SystemMetricsReader`

文件：

- [SystemMetricsReader.cs](../windows-agent/RetroMonitor.WindowsAgent/Services/SystemMetricsReader.cs)

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

注意：网络速率通过两次采样的字节差计算，首次采样可能为 `null`。

### 4.3 `HardwareMonitorReader`

文件：

- [HardwareMonitorReader.cs](../windows-agent/RetroMonitor.WindowsAgent/Services/HardwareMonitorReader.cs)

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

维护重点：

- 换新硬件时先运行 `dotnet run -- --dump-sensors`
- 再核对 `PickCpuTemperature`、`PickCpuClock`、`PickCpuPower`、`PickGpuMetric`
- 不要在没有传感器清单的情况下盲目改匹配规则

### 4.4 `WindowsTelemetryProvider`

文件：

- [WindowsTelemetryProvider.cs](../windows-agent/RetroMonitor.WindowsAgent/Services/WindowsTelemetryProvider.cs)

负责：

- 组装最终 `TelemetrySnapshot`
- 合并 fast / slow metrics
- 设置 `timestamp`
- 设置 `device_id`
- 估算 `system_power_estimated`
- 判断 `source_ok`

当前 `system_power_estimated` 策略：

- 优先使用 `LibreHardwareMonitor` 暴露的直接整机/总功耗类传感器
- 拿不到时回退到 `cpu_power + gpu_power + base_watts`

---

## 5. 回归验证顺序

后续任何 Windows agent 修改，都按这个顺序回归：

```powershell
cd C:\path\to\retro-monitor\windows-agent\RetroMonitor.WindowsAgent
dotnet restore
dotnet build
dotnet run -- --dump-sensors
dotnet run
```

然后检查：

- `http://127.0.0.1:8125/telemetry`
- JSON 是否完整
- 所有 schema 字段是否都存在
- 缺失字段是否是 `null`
- `platform` 是否是 `windows`
- `device_id` / `hostname` 是否稳定
- `source_ok` 是否符合预期

服务安装回归：

```powershell
cd C:\path\to\retro-monitor
.\windows-agent\install-windows-agent.ps1
```

打包回归：

```powershell
cd C:\path\to\retro-monitor
.\windows-agent\package-windows-agent.ps1
```

Home Assistant 回归：

- 新增或重载 `Retro Monitor` Windows source
- 确认 Windows desktop 实体在线
- 确认 `desktop_current_*` 可选择 Windows 数据

---

## 6. 维护时不要做的事

- 不要改字段名
- 不要省略 `null` 字段
- 不要为了某一台机器的传感器名称破坏通用 fallback
- 不要把显示控制塞回 Windows agent
- 不要让 HTTP 请求变成实时采样触发器
- 不要把 `system_power_estimated` 描述成墙插实测功耗

---

## 7. 当前仍需长期观察的点

- 不同 Windows 硬件上的 `LibreHardwareMonitor` 传感器命名差异
- macOS / Windows 同时在线时 `desktop_current_*` 的选源稳定性
- Windows Service 重启、系统冷启动后的恢复行为
- `system_power_estimated` 在不同硬件上的参考价值

---

## 8. 后续 agent 输出建议

维护完成后，建议用这个结构汇报：

1. 改了哪些文件
2. 是否保持 telemetry schema 兼容
3. `dotnet build` 结果
4. `--dump-sensors` 是否仍能看到关键传感器
5. `/telemetry` 样本是否完整
6. Windows Service 是否正常
7. HA 是否能接入或重载
8. `desktop_current_*` 是否正常消费 Windows 数据
