# Retro Monitor

Retro Monitor 是一套本地优先的硬件状态监控与复古显示系统。它把 macOS / Windows / OpenWrt 设备的遥测数据统一成稳定的 `/telemetry` 接口，再由 Home Assistant 聚合为 `desktop_current_*` 等实体，最终驱动 SSD1322 OLED 与 ESP32-C3 VFD 显示终端。

项目当前重点不是做一个云端监控平台，而是为家庭实验室、软路由、桌面主机和实体显示屏提供一条低延迟、可离线、可维护的本地链路。

## 当前状态

| 模块 | 状态 | 说明 |
| --- | --- | --- |
| macOS Agent | 可用主线 | Go agent 已作为当前 LaunchAgent 服务路径 |
| Python Agent | 保留 | 早期原型与兼容测试面，不再是 macOS 后台服务主线 |
| Windows Agent | 可用 | `.NET 8` 采集端已完成，并已在 Windows 目标机完成编译、传感器、服务和 HA 接入测试 |
| Home Assistant 集成 | 可用 | 负责拉取、校验、暴露遥测实体 |
| `desktop_current_*` 聚合层 | 可用 | 为 OLED / VFD 提供稳定电脑状态源 |
| SSD1322 OLED 固件 | 可用 | ESPHome 固件已接入 HA 聚合实体 |
| ESP32-C3 VFD 固件 | 可用原型 | 已跑通显示、控制实体、动画和亮度同步 |
| OpenWrt 路由器遥测 | 可用路径 | 通过 CGI + HA REST sensor 接入 |

最近验证记录见 [docs/project-progress-zh.md](docs/project-progress-zh.md)。

## 功能特性

- 固定 v1 桌面遥测协议：所有字段稳定，缺失值返回 `null`。
- 后台固定频率采样：HTTP 请求读取缓存快照，不触发实时采样。
- macOS 原生采集：Go agent 读取 AppleSMC、IOKit GPU、NVMe SMART、网络与磁盘活动。
- Home Assistant 本地轮询：无需云服务，使用 `local_polling` 集成模型。
- 多电脑源聚合：macOS / Windows 可共用 `desktop_current_*` 输出层。
- 显示控制解耦：遥测归 `retro_monitor`，亮度、页面、动画、电源等控制归 ESPHome 设备自身。
- OLED / VFD 双显示终端：同时支持像素型 SSD1322 OLED 和字符型 016ST106INK VFD。
- OpenWrt 路由器页面：可显示 WAN、CPU、内存、温度等基础路由状态。

## 系统架构

```text
macOS Go Agent       Windows Agent       OpenWrt CGI
     |                    |                  |
     | GET /telemetry     | GET /telemetry   | REST JSON
     v                    v                  v
Home Assistant retro_monitor + packages/templates
     |
     | desktop_current_* / router_* entities
     v
ESPHome SSD1322 OLED + ESP32-C3 VFD
```

当前边界固定为：

- Agent 只负责采集和提供遥测数据。
- Home Assistant 负责拉取、校验、实体化和跨设备聚合。
- ESPHome 设备负责显示逻辑、亮度、页面、动画和设备侧控制。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `go-agent/` | 当前 macOS Go 遥测服务 |
| `src/retro_monitor_agent/` | 早期 Python 遥测原型 |
| `windows-agent/` | Windows `.NET 8` 遥测服务、安装脚本和打包脚本 |
| `homeassistant/custom_components/retro_monitor/` | Home Assistant 自定义集成 |
| `homeassistant/packages/` | HA 聚合实体和路由器 REST sensor 配置 |
| `esphome/oled_display_p1_demo.yaml` | 当前 SSD1322 OLED 固件 |
| `esphome/vfd_016st106ink_ha_monitor.yaml` | 当前 ESP32-C3 VFD 固件 |
| `openwrt/` | 路由器端遥测脚本和 CGI 包装 |
| `deploy/macos/` | macOS LaunchAgent 模板 |
| `scripts/` | macOS 服务安装/卸载脚本 |
| `tools/oled-preview/` | OLED 布局本地浏览器预览 |
| `docs/` | 协议、设计、进度和硬件资料 |
| `tests/` | Python agent 与 HA 集成单元测试 |

## 环境要求

### macOS Agent

- macOS / Hackintosh 环境。
- Go，版本以 `go-agent/go.mod` 为准。
- 可选：Intel Power Gadget，用于尝试读取平台功耗。

### Python 原型

- Python `>=3.9`。
- `psutil>=7.2,<8`。

### Windows Agent

- Windows 10 / 11。
- `.NET 8 SDK`。
- 部分硬件传感器需要管理员权限。

### Home Assistant

- 支持手动安装自定义集成的 Home Assistant。
- 推荐启用 `packages`，便于加载 `homeassistant/packages/*.yaml`。

### ESPHome

- ESPHome 环境。
- SSD1322 OLED 或 ESP32-C3 + 016ST106INK VFD 硬件。
- 正确配置 `esphome/secrets.yaml`。

## 快速开始

### 1. 启动 macOS Go Agent

开发运行：

```bash
cd /path/to/retro-monitor/go-agent
go run ./cmd/retro-monitor-agent --provider macos --host 0.0.0.0 --port 8125 --sample-interval 500ms
```

检查接口：

```bash
curl http://127.0.0.1:8125/telemetry
```

返回应为一个完整 JSON 对象，并包含 `device_id`、`hostname`、`platform`、`timestamp`、`source_ok`、`cpu_temp` 等字段。

### 2. 安装为 macOS 后台服务

```bash
cd /path/to/retro-monitor
./scripts/install_macos_agent.sh
```

安装脚本会：

- 构建 `go-agent/bin/retro-monitor-agent`。
- 写入 `~/Library/LaunchAgents/com.ian.retromonitor.agent.plist`。
- 以 `0.0.0.0:8125` 启动 agent。

查看服务状态：

```bash
launchctl print gui/$(id -u)/com.ian.retromonitor.agent
```

重启服务：

```bash
launchctl kickstart -k gui/$(id -u)/com.ian.retromonitor.agent
```

查看日志：

```text
~/Library/Logs/retro-monitor/agent.stdout.log
~/Library/Logs/retro-monitor/agent.stderr.log
```

卸载服务：

```bash
cd /path/to/retro-monitor
./scripts/uninstall_macos_agent.sh
```

### 3. 运行 Python 原型

Python 版本主要用于历史对照、mock 数据和测试。

```bash
cd /path/to/retro-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m retro_monitor_agent --provider mock --port 8125
```

运行 Python macOS provider：

```bash
python -m retro_monitor_agent --provider macos --port 8125 --sample-interval 0.5
```

## Home Assistant 使用说明

### 安装自定义集成

手动安装方式：

```bash
cp -R homeassistant/custom_components/retro_monitor \
  /path/to/homeassistant/config/custom_components/
```

然后重启 Home Assistant。

本仓库也提供了针对当前软路由环境的部署脚本：

```bash
cd /path/to/retro-monitor
./deploy_to_ha.sh
```

注意：`deploy_to_ha.sh` 内部写死了当前环境的路由器地址和 HA 配置路径，给其他环境使用前需要先改脚本顶部变量。

### 添加桌面遥测设备

在 Home Assistant 中：

1. 打开 `设置 -> 设备与服务`。
2. 添加集成 `Retro Monitor`。
3. 填写 agent 地址。

常用配置：

| 字段 | macOS 示例 |
| --- | --- |
| Host | `<desktop-agent-ip>` |
| Port | `8125` |
| Path | `/telemetry` |
| Scan interval | `1` 或按需调整 |

集成会先请求 `http://<host>:<port><path>` 并校验 payload。校验通过后才会保存配置。

### 启用聚合实体

把 package 文件复制到 HA 配置目录：

```bash
mkdir -p /path/to/homeassistant/config/packages
cp homeassistant/packages/retro_monitor_desktop_current.yaml \
  /path/to/homeassistant/config/packages/
```

确保 `configuration.yaml` 中启用了 packages：

```yaml
homeassistant:
  packages: !include_dir_named packages
```

重启 Home Assistant 后，应出现这些稳定实体：

- `sensor.desktop_current_display_payload`
- `sensor.desktop_current_cpu_temperature`
- `sensor.desktop_current_cpu_load`
- `sensor.desktop_current_cpu_power`
- `sensor.desktop_current_gpu_temperature`
- `sensor.desktop_current_gpu_load`
- `sensor.desktop_current_memory_usage`
- `sensor.desktop_current_fan_speed_max`
- `sensor.desktop_current_disk_temperature_max`
- `sensor.desktop_current_system_power_estimated`
- `binary_sensor.desktop_current_source_ok`

OLED 和 VFD 应优先消费 `desktop_current_*`，不要直接绑定某一台电脑的原始实体。

## ESPHome 显示端使用说明

### SSD1322 OLED

当前主文件：

```text
esphome/oled_display_p1_demo.yaml
```

常用命令：

```bash
esphome config esphome/oled_display_p1_demo.yaml
esphome run esphome/oled_display_p1_demo.yaml
```

辅助文件：

- `esphome/oled_display_rescue.yaml`：救援固件。
- `esphome/oled_display_p1_demo.crash-early-oled-update.yaml`：早期崩溃版本快照。
- `tools/oled-preview/index.html`：浏览器布局预览。

### ESP32-C3 VFD

当前主文件：

```text
esphome/vfd_016st106ink_ha_monitor.yaml
```

当前验证过的引脚映射：

| VFD 信号 | ESP32-C3 GPIO |
| --- | --- |
| `RST` | `GPIO0` |
| `CS` | `GPIO1` |
| `CP` | `GPIO4` |
| `DA` | `GPIO5` |
| `EN` | `GPIO6` |

常用命令：

```bash
esphome config esphome/vfd_016st106ink_ha_monitor.yaml
esphome run esphome/vfd_016st106ink_ha_monitor.yaml
```

当前设备侧控制包括：

- `Display Power`
- `Brightness`
- `Animation`
- `Sleep Timeout`
- `Auto Rotate Interval`
- `WiFi Signal`
- `Restart`

## OpenWrt 路由器遥测使用说明

路由器端由两个文件组成：

- `openwrt/router_telemetry.sh`：采集 OpenWrt / iStoreOS 状态并输出 JSON。
- `openwrt/router_telemetry.cgi`：CGI 包装，输出 HTTP JSON 响应头。

参考安装路径：

```bash
scp openwrt/router_telemetry.sh root@<router-ip>:/usr/local/bin/router_telemetry.sh
scp openwrt/router_telemetry.cgi root@<router-ip>:/www/cgi-bin/retro-monitor-router
ssh root@<router-ip> "chmod +x /usr/local/bin/router_telemetry.sh /www/cgi-bin/retro-monitor-router"
```

测试：

```bash
curl http://<router-ip>/cgi-bin/retro-monitor-router
```

Home Assistant package：

```bash
cp homeassistant/packages/retro_monitor_router.yaml \
  /path/to/homeassistant/config/packages/
```

当前 `retro_monitor_router.yaml` 默认从 Home Assistant 容器内访问：

```text
http://127.0.0.1/cgi-bin/retro-monitor-router
```

如果 HA 不和路由器共享网络命名空间，需要把该地址改成路由器实际 IP。

## Windows Agent 使用说明

Windows 实现位于：

```text
windows-agent/RetroMonitor.WindowsAgent/
```

目标：

- 保持 `GET /telemetry` 协议不变。
- 使用 `LibreHardwareMonitorLib` 读取硬件传感器。
- 使用 Windows API / counters 读取 CPU、内存、网络和磁盘活动。
- 作为 Windows Service 长期运行。

当前状态：

- Windows 采集端已经完成。
- 已在 Windows 目标机完成 `dotnet restore` / `dotnet build`。
- 已通过 `dotnet run -- --dump-sensors` 完成真实传感器枚举。
- 已验证 `/telemetry` 返回完整 desktop schema，`platform == "windows"`。
- 已验证 Windows Service 安装和启动。
- 已验证 Home Assistant 可接入该 Windows source。
- 已验证 `desktop_current_*` 聚合层可消费 Windows 数据。

开发运行：

```powershell
cd C:\path\to\retro-monitor\windows-agent\RetroMonitor.WindowsAgent
dotnet restore
dotnet build
dotnet run
```

传感器枚举：

```powershell
dotnet run -- --dump-sensors
```

打包：

```powershell
cd C:\path\to\retro-monitor
.\windows-agent\package-windows-agent.ps1
```

打包产物默认输出到：

```text
windows-agent\package\RetroMonitorWindowsAgent.zip
```

服务安装脚本：

```powershell
.\windows-agent\install-windows-agent.ps1
```

维护注意：

- 本仓库所在 macOS 环境只有 .NET runtime，没有 .NET SDK，不能在本机复跑 Windows 编译测试。
- 后续修改 Windows agent 后，应在 Windows 10 / 11 + `.NET 8 SDK` 环境重新执行 build、sensor dump、service install 和 `/telemetry` 校验。
- 传感器名称仍是按 `LibreHardwareMonitor` 输出做启发式匹配；换新硬件时应先看 `--dump-sensors` 输出。

## 遥测协议

桌面 agent 必须暴露：

```text
GET /telemetry
```

响应要求：

- `Content-Type: application/json`
- 返回一个完整 JSON object。
- 所有 schema 字段都必须存在。
- 缺失传感器值使用 `null`，不要省略字段。
- `timestamp` 使用 UTC ISO 8601。
- `source_ok=false` 表示数据退化或过期，但单个字段仍可能有效。

核心字段：

```text
device_id
hostname
platform
timestamp
source_ok
cpu_temp
cpu_load
cpu_clock
cpu_power
gpu_temp
gpu_load
gpu_clock
gpu_power
memory_used_mb
memory_total_mb
memory_percent
fan_rpm_max
fan_rpm_avg
disk_temp_max
disk_activity_percent
net_up_bps
net_down_bps
system_power_estimated
```

完整协议见 [docs/telemetry-spec.md](docs/telemetry-spec.md)。

## 开发与测试

运行 Python / Home Assistant 单测：

```bash
cd /path/to/retro-monitor
source .venv/bin/activate
pytest -q
```

运行 Go agent 单测：

```bash
cd /path/to/retro-monitor/go-agent
go test ./...
```

当前已知验证结果：

- `pytest -q`：`51 passed`
- `go test ./...`：通过；macOS SDK 会提示 `IOMasterPort` deprecated warning
- Windows agent：已在 Windows 目标机完成编译、传感器枚举、`/telemetry`、服务安装和 HA 接入测试

说明：当前 macOS 工作区不能复跑 Windows `.NET 8 SDK` 测试；Windows 端验证应以目标机结果为准。

## 常见问题

### Home Assistant 添加集成时提示无法连接

先在 HA 所在机器或容器内测试：

```bash
curl http://<agent-host>:8125/telemetry
```

确认：

- agent 正在运行。
- `host` 和 `port` 可从 HA 网络访问。
- path 是 `/telemetry`。
- 返回内容是 JSON，而不是 HTML 错误页或空响应。

### HA 能看到原始设备，但 OLED / VFD 不更新

优先检查聚合实体：

- `sensor.desktop_current_display_payload`
- `binary_sensor.desktop_current_source_ok`

显示端应绑定 `desktop_current_*`，不要绑定旧的 `iandeimac_*` 或单设备实体。

### macOS 服务启动后没有数据

检查 LaunchAgent 和日志：

```bash
launchctl print gui/$(id -u)/com.ian.retromonitor.agent
tail -n 100 ~/Library/Logs/retro-monitor/agent.stderr.log
```

也可以临时前台运行：

```bash
cd /path/to/retro-monitor/go-agent
go run ./cmd/retro-monitor-agent --provider macos --host 127.0.0.1 --port 8125 --sample-interval 500ms
```

### Windows 端部分字段是 `null`

这是允许的。不同主板、GPU、硬盘控制器暴露的 `LibreHardwareMonitor` 传感器不同。先运行：

```powershell
dotnet run -- --dump-sensors
```

再根据真实传感器名称调整匹配规则。

### `system_power_estimated` 是否等于真实墙插功耗

不是。当前它是显示和趋势参考值，优先尝试直接平台功耗，拿不到时使用 `cpu_power + gpu_power + 20W base` 的保守估算。

## 重要文档

- [docs/project-progress-zh.md](docs/project-progress-zh.md)：当前进度和真实状态。
- [docs/telemetry-spec.md](docs/telemetry-spec.md)：桌面遥测协议。
- [docs/homeassistant-communication-spec.md](docs/homeassistant-communication-spec.md)：HA 通信契约。
- [docs/homeassistant-ux-design-zh.md](docs/homeassistant-ux-design-zh.md)：HA 实体与 UX 设计。
- [docs/macos-agent-service.md](docs/macos-agent-service.md)：macOS 后台服务。
- [docs/windows-agent-ai-handoff-zh.md](docs/windows-agent-ai-handoff-zh.md)：Windows 后续接手说明。
- [docs/openwrt-router-integration.md](docs/openwrt-router-integration.md)：路由器接入方案。
- [docs/esp32-screen-beginner-guide-zh.md](docs/esp32-screen-beginner-guide-zh.md)：ESP32 屏幕接线、刷写和接入小白教程。
- [docs/oled-preview.md](docs/oled-preview.md)：OLED 本地预览。
- [docs/vfd-progress-zh.md](docs/vfd-progress-zh.md)：VFD 分支进度。
- [docs/backup/](docs/backup/)：过时说明、旧方案和归档材料。

## 发布前检查清单

- `pytest -q` 通过。
- `go test ./...` 通过。
- macOS agent 可返回完整 `/telemetry` JSON。
- Home Assistant 可以新增或重新加载 `Retro Monitor` 集成。
- `desktop_current_*` 聚合实体可用。
- OLED / VFD ESPHome 配置校验通过。
- Windows 发布前如有代码改动，应在 Windows 目标机重新完成 `dotnet build`、`--dump-sensors`、服务安装、`/telemetry` 和 HA 接入校验。
