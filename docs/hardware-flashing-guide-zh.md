# 硬件连接及烧录教程

这份教程面向第一次使用 ESP32 和 OLED 屏幕的用户。

公开版本使用 SSD1322 256x64 OLED 屏幕。

## 1. 你需要准备什么

- ESP32 开发板
- SSD1322 256x64 OLED 屏幕
- USB 数据线
- 杜邦线
- 已安装 ESPHome 的电脑
- 已配置好的 Home Assistant

## 2. 接线

当前固件使用 4SPI 模式。

| OLED 引脚 | 接到 ESP32 |
| --- | --- |
| `VSS` / `GND` | `GND` |
| `VCC` | 按屏幕模块要求接 `3V3` 或 `5V` |
| `SCL` / `D0` | `GPIO18` |
| `SDA` / `D1` | `GPIO23` |
| `CS` | `GPIO5` |
| `DC` | `GPIO16` |
| `RES` / `RST` | `GPIO17` |
| `RD` | `GND` |
| `WR` | `GND` |
| `D2-D7` | 不接 |

更完整的引脚说明见 [SSD1322 接线说明](ssd1322-16pin-4spi-wiring.md)。

## 3. 准备 Wi-Fi 密码

复制示例文件：

```bash
cp esphome/secrets.example.yaml esphome/secrets.yaml
```

编辑 `esphome/secrets.yaml`：

```yaml
wifi_ssid: "你的 Wi-Fi 名称"
wifi_password: "你的 Wi-Fi 密码"
fallback_ap_password: "临时配网热点密码"
```

不要把 `esphome/secrets.yaml` 提交到 Git。

## 4. 第一次刷写

用 USB 线把 ESP32 接到电脑。

确认配置是否正确：

```bash
python3 -m esphome config esphome/oled_display_p1_demo.yaml
```

刷写：

```bash
python3 -m esphome run esphome/oled_display_p1_demo.yaml
```

ESPHome 会让你选择串口设备。常见名称类似：

```text
/dev/cu.usbserial-xxxx
/dev/cu.usbmodemxxxx
COM3
COM4
```

## 5. 连接 Home Assistant

第一次刷写成功后，ESP32 会连接 Wi-Fi，并出现在 Home Assistant 的 ESPHome 集成中。

在 Home Assistant 中添加这个 ESPHome 设备。添加成功后，OLED 固件会读取 `desktop_current_*` 实体并显示状态。

## 6. 后续 OTA 更新

第一次 USB 刷写成功后，后续通常可以通过网络更新：

```bash
python3 -m esphome run esphome/oled_display_p1_demo.yaml --device retro-monitor-display.local
```

如果 `.local` 名称不可用，也可以使用设备 IP：

```bash
python3 -m esphome run esphome/oled_display_p1_demo.yaml --device 192.168.x.x
```

## 7. 常见问题

### 屏幕不亮

检查：

- `GND` 是否共地
- `VCC` 是否符合屏幕模块要求
- `SCL` 和 `SDA` 有没有接反
- `CS`、`DC`、`RES` 是否和固件一致
- `RD` 和 `WR` 是否接到 `GND`

### ESP32 没有连上 Wi-Fi

检查：

- `esphome/secrets.yaml` 里的 Wi-Fi 名称和密码
- 当前 Wi-Fi 是否是 2.4GHz
- ESP32 是否离路由器太远

如果设备进入临时配网模式，会出现名为 `RetroMonitor Setup` 的热点。

### Home Assistant 有实体，但屏幕没有数据

检查 Home Assistant 中是否有：

- `sensor.desktop_current_display_payload`
- `binary_sensor.desktop_current_source_ok`

如果没有，请先回到 [Home Assistant 端配置教程](ha-setup-guide-zh.md)。
