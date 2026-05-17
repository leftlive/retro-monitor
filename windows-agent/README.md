# Windows Agent

本目录包含 Retro Monitor 的 Windows 原生采集端。

## 当前状态

Windows 采集端已经完成，并已在 Windows 目标机通过测试。

已验证内容：

- `dotnet restore` / `dotnet build`
- `dotnet run -- --dump-sensors`
- `dotnet run` 后访问 `http://127.0.0.1:8125/telemetry`
- 完整 desktop telemetry schema 输出
- `platform == "windows"`
- Windows Service 安装和启动
- Home Assistant `Retro Monitor` 集成接入
- `desktop_current_*` 聚合层消费 Windows 数据

说明：当前 macOS 工作区只有 .NET runtime，没有 .NET SDK，不能在本机复跑 Windows 编译测试。Windows 端验证以目标 Windows 机器结果为准。

## 目标

- 保持既有 `GET /telemetry` 合约不变。
- 后台固定周期采样，HTTP 请求返回缓存快照。
- 使用 `LibreHardwareMonitorLib` 读取 CPU、GPU、风扇、磁盘温度和功耗类硬件传感器。
- 使用 Windows 原生 counters / API 读取 CPU 负载、内存、网络和磁盘活动。
- 支持 Windows Service 长期运行。

## 运行

在 Windows PowerShell 中：

```powershell
cd C:\path\to\retro-monitor\windows-agent\RetroMonitor.WindowsAgent
dotnet restore
dotnet build
dotnet run
```

然后打开：

```text
http://127.0.0.1:8125/telemetry
```

## 传感器枚举

查看目标机器上 `LibreHardwareMonitor` 暴露的真实传感器：

```powershell
dotnet run -- --dump-sensors
```

换新硬件或调整传感器匹配规则前，先保存并核对这份输出。

## 打包

在仓库根目录运行：

```powershell
.\windows-agent\package-windows-agent.ps1
```

默认生成：

```text
windows-agent\package\RetroMonitorWindowsAgent.zip
```

## 服务安装

从源码发布并安装服务：

```powershell
.\windows-agent\install-windows-agent.ps1
```

从打包产物安装服务：

```powershell
.\install.ps1
```

卸载服务：

```powershell
.\uninstall.ps1
```

## 配置

配置位于 `RetroMonitor.WindowsAgent/appsettings.json` 的 `RetroMonitor` 节点。

默认值：

- host: `0.0.0.0`
- port: `8125`
- sample interval: `500ms`
- slow interval: `2000ms`
- system power base watts: `20`

## 维护注意

- 缺失字段必须返回 `null`，不要省略字段。
- 部分硬件传感器需要管理员权限。
- `LibreHardwareMonitor` 覆盖情况依赖主板、GPU、硬盘控制器和驱动。
- 换新硬件后，先运行 `--dump-sensors`，再判断是否需要调整 `HardwareMonitorReader` 的匹配规则。
- 修改 Windows agent 后，需要在 Windows 目标机重新执行 build、sensor dump、`/telemetry`、service install 和 HA 接入验证。
