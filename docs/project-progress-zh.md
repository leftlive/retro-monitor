# Retro Monitor 项目进度汇总

更新日期: 2026-05-16

## 当前系统边界

Retro Monitor 现在拆成四条明确链路:

- macOS telemetry agent: 负责采集电脑端数据并提供 `/telemetry`
- Home Assistant `retro_monitor`: 负责拉取、校验、暴露遥测实体
- Home Assistant template package: 负责生成 `desktop_current_*` 聚合实体，兼容后续 macOS / Windows 双电脑源
- ESPHome OLED / VFD: 负责屏幕本地显示、亮度、页面、动画和电源控制

当前原则已经固定:

- 数据归 `retro_monitor`
- 显示控制归具体 ESPHome 设备
- OLED 与 VFD 共用 HA 里的 `desktop_current_*` 电脑状态源

## macOS Agent

当前状态:

- `/telemetry` 由后台固定频率采样缓存驱动，默认采样间隔为 `0.5s`
- 不再由 HTTP 请求直接触发实时采样
- 当前 macOS LaunchAgent 已迁移到 Go agent，安装脚本会先构建 `go-agent/bin/retro-monitor-agent`
- macOS provider 已使用直接系统接口为主，不依赖 CLI 工具采集核心字段
- `system_power_estimated` 使用保守估算: `cpu_power + gpu_power + 20W base`

已验证字段覆盖:

- CPU 温度、负载、频率、功耗
- GPU 温度、负载、频率、功耗
- 内存占用
- 风扇最大/平均转速
- NVMe 磁盘温度
- 磁盘活动度
- 网络上下行速率
- 估算整机功耗

说明:

- Python agent 仍保留在 `src/retro_monitor_agent/`，用于历史原型对照和单测覆盖，但不再是 macOS 后台服务主线
- 整机功耗目前仍是估算，不是墙插或平台级实测值

## Windows Agent

当前状态:

- Windows 采集端已经完成，并已在 Windows 目标机通过测试
- `.NET 8` ASP.NET Core 服务提供 `GET /telemetry`
- `LibreHardwareMonitorLib` 负责 CPU / GPU / 风扇 / 磁盘温度等硬件传感器
- Windows API / counters 负责 CPU 负载、内存、磁盘活动度、网络速率等系统指标
- 后台 `TelemetrySampler` 固定周期采样，HTTP 请求读取缓存快照
- 支持 `dotnet run -- --dump-sensors` 输出真实传感器清单
- 支持 Windows Service 安装和打包脚本

已验证:

- `dotnet restore` / `dotnet build` 在 Windows 目标机通过
- `--dump-sensors` 可输出目标机真实传感器清单
- `/telemetry` 返回完整 desktop schema，缺失字段按协议返回 `null`
- `platform` 正确输出为 `windows`
- Windows Service 可安装并启动
- Home Assistant 可新增 Windows source
- `desktop_current_*` 聚合层可消费 Windows 数据

说明:

- 当前 macOS 工作区只有 .NET runtime，不能在本机复跑 Windows `.NET 8 SDK` 编译测试
- 后续更换硬件或修改传感器匹配规则时，应重新运行 `--dump-sensors` 核对传感器命名

## Home Assistant

当前状态:

- `retro_monitor` 自定义集成已部署到路由器 HA Docker
- 电脑端配置项固定使用 `<desktop-agent-ip>:8125/telemetry`
- 路由器端配置项保留 `127.0.0.1:80/cgi-bin/retro-monitor-router`
- `retro_monitor` 现在只暴露遥测数据实体和状态实体
- 旧的 `select/number/switch` 显示控制平台已删除
- `async_remove_config_entry_device` 已补齐，删除监控设备时会移除对应 config entry
- coordinator 已修复 `Session is closed` 的重启边界问题

当前聚合实体:

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

说明:

- `sensor.iandeimac_local_display_payload` 保留为隐藏的内部源实体
- OLED / VFD 不应直接消费旧的 `iandeimac_*` 实体
- Windows source 已验证可按同一 desktop schema 接入，并可被 `desktop_current_*` 聚合层选择

## OLED 终端

当前主文件:

- `esphome/oled_display_p1_demo.yaml`

当前状态:

- 最新 OLED 固件已通过 OTA 刷入
- OLED 通过 `sensor.desktop_current_display_payload` 消费电脑端数据
- OLED 控制实体已迁移到 ESPHome 设备自身
- 已修复启动阶段调用 `id(oled).update()` 导致的 SSD1322 SPI 未初始化崩溃
- `baud_rate` 已恢复为 `0`，默认关闭 USB/UART 串口日志
- 新增 `API Diagnostics` 开关，用于通过 ESPHome API 切换远程日志级别

OLED 设备侧控制:

- `Display Power`
- `Brightness`
- `Current Page`
- `Auto Rotate`
- `Auto Rotate Interval`
- `API Diagnostics`

保留的排障文件:

- `esphome/oled_display_rescue.yaml`: 稳定救援固件
- `esphome/oled_display_p1_demo.crash-early-oled-update.yaml`: 早期崩溃版本快照

## VFD 终端

当前主文件:

- `esphome/vfd_016st106ink_ha_monitor.yaml`

当前状态:

- ESP32-C3 SuperMini + 016ST106INK VFD 已跑通
- 当前引脚映射已验证:
  - `RST = GPIO0`
  - `CS = GPIO1`
  - `CP = GPIO4`
  - `DA = GPIO5`
  - `EN = GPIO6`
- VFD 驱动支持两行字符、亮度、图标位、CGRAM 自定义字形
- VFD 使用 `desktop_current_*` 电脑聚合实体
- VFD 亮度设置已修复，页面切换动画结束后会恢复到 HA 设定亮度
- 数据从断开/等待恢复到可用后，会先播放 `boot_seq`，再进入数据页面

VFD 设备侧控制:

- `Display Power`
- `Brightness`
- `Animation`
- `Sleep Timeout`
- `Auto Rotate Interval`
- `WiFi Signal`
- `Restart`

## 当前验证

最近完成的验证:

- Python / HA 单测: `51 passed`
- Go agent 单测: `go test ./...` 通过，仅有 macOS SDK `IOMasterPort` deprecation warning
- OLED ESPHome config: 通过
- VFD ESPHome config: 通过
- OLED OTA: 成功
- VFD OTA: 成功
- OLED API / OTA 端口在线
- VFD API / OTA 端口在线
- HA `retro_monitor` 加载无新的 `Session is closed` 错误
- Windows agent: 编译、传感器枚举、`/telemetry`、Windows Service、HA 接入和 `desktop_current_*` 聚合验证通过

## 仍需跟踪

- HA UI 中删除 `retro_monitor` 监控设备的完整用户路径需要再做一次人工确认
- OLED 的 Wi-Fi 百分比信号实体仍需去掉 `signal_strength` device class，避免 HA 日志告警
- Windows agent 后续若换新硬件，需要重新用 `--dump-sensors` 核对传感器命名
- macOS / Windows 同时在线时的 `desktop_current_*` 选源策略可继续做长时间稳定性观察
- VFD 亮度修复已刷入，需要在真实屏幕上观察一次切页动画后的亮度保持效果
