# Retro Monitor

Retro Monitor 是一个本地运行的桌面状态监控屏项目。

它把 macOS、Windows 或 OpenWrt 设备的温度、负载、内存、网络等状态采集出来，送进 Home Assistant，再显示到一块 ESP32 驱动的 SSD1322 OLED 屏幕上。

## 入门文档

第一次使用建议按下面顺序看：

1. [采集端配置教程](docs/collector-setup-guide-zh.md)
2. [Home Assistant 端配置教程](docs/ha-setup-guide-zh.md)
3. [硬件连接及烧录教程](docs/hardware-flashing-guide-zh.md)

## 这个项目解决什么问题

如果你想做一个放在桌面上的实体小屏幕，用来显示电脑或软路由的状态，Retro Monitor 提供了一条完整链路：

```text
采集端 -> Home Assistant -> ESPHome -> ESP32 + OLED 屏幕
```

它不依赖云服务，适合家庭实验室、桌面主机、软路由和本地自动化环境。

## 当前公开版本包含什么

| 模块 | 说明 |
| --- | --- |
| macOS 采集端 | Go 实现，提供 `/telemetry` HTTP 接口 |
| Windows 采集端 | .NET 8 实现，支持 Windows Service |
| OpenWrt 采集脚本 | 采集软路由基础状态 |
| Home Assistant 集成 | 拉取采集端数据并创建实体 |
| Home Assistant packages | 生成统一的 `desktop_current_*` 聚合实体 |
| ESPHome OLED 固件 | 驱动 SSD1322 256x64 OLED 屏幕 |

## 最终效果

公开版本的目标是让一块 OLED 屏幕显示：

- CPU 温度、负载、功耗
- GPU 温度、负载、功耗
- 内存占用
- 硬盘温度
- 风扇转速
- 网络上传/下载
- 软路由状态

不同硬件能读取到的传感器不同，缺失值会显示为空或退化状态，这是正常情况。

## 仓库结构

| 路径 | 用途 |
| --- | --- |
| `go-agent/` | macOS 采集端 |
| `windows-agent/` | Windows 采集端 |
| `src/retro_monitor_agent/` | Python 原型与测试辅助 |
| `homeassistant/custom_components/retro_monitor/` | Home Assistant 自定义集成 |
| `homeassistant/packages/` | Home Assistant 聚合实体配置 |
| `openwrt/` | OpenWrt 路由器采集脚本 |
| `esphome/` | ESPHome OLED 固件 |
| `docs/` | 入门教程和协议说明 |
| `tools/oled-preview/` | OLED 布局预览工具 |

## 硬件要求

公开版本默认使用：

- ESP32 开发板
- SSD1322 256x64 OLED 屏幕
- 杜邦线
- USB 数据线
- 可运行 Home Assistant 的设备

详细接线和刷写步骤见 [硬件连接及烧录教程](docs/hardware-flashing-guide-zh.md)。

## 软件要求

- Home Assistant
- ESPHome
- Go，运行 macOS 采集端时需要
- .NET 8 SDK，运行或打包 Windows 采集端时需要
- Python 3.9+，运行测试或 Python 原型时需要

## 遥测接口

采集端统一暴露：

```text
GET /telemetry
```

返回值是一个 JSON 对象。完整字段说明见 [遥测协议](docs/telemetry-spec.md)。

## 许可协议

本项目使用 GNU General Public License v3.0 发布。见 [LICENSE](LICENSE)。
