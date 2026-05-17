# ESP32 屏幕接线与刷写小白教程

本文档面向第一次接 ESP32 屏幕、第一次刷 ESPHome 固件的用户。目标是从零开始完成：

1. 分清自己手上的屏幕类型。
2. 把屏幕线接到 ESP32。
3. 准备 Wi-Fi 配置。
4. 用 USB 首次刷写程序。
5. 让设备连上 Wi-Fi / Home Assistant。
6. 用 OTA 进行后续更新。

本项目当前有两条屏幕路线：

| 你手上的硬件 | 使用文件 | 说明 |
| --- | --- | --- |
| ESP32 DevKit + SSD1322 256x64 OLED | `esphome/oled_display_p1_demo.yaml` | 像素屏，适合三栏状态页和趋势页 |
| ESP32-C3 SuperMini + 016ST106INK VFD | `esphome/vfd_016st106ink_ha_monitor.yaml` | 字符屏，复古 VFD 风格 |

如果你不确定是哪一种：OLED 通常是一整块黑色像素屏，能画线和图形；016ST106INK VFD 是类似音响面板的荧光字符屏，显示区域像固定字符段。

## 0. 开始前先看这几条

- 不要带电插拔屏幕线。接线、改线前先拔掉 USB 和外部电源。
- ESP32 的信号脚是 `3.3V` 逻辑，不要把信号线接到 `5V`。
- 屏幕和 ESP32 必须共地，也就是屏幕 `GND` 要接 ESP32 `GND`。
- 先反复检查 `VCC` 和 `GND`，再插 USB。
- VFD 模块内部有升压/高压驱动，通电后不要用手碰裸露焊点。
- 第一次刷写一定用 USB，成功联网后再用 OTA。

## 1. 准备材料

通用材料：

- 一台电脑，macOS / Windows / Linux 都可以。
- 一根支持数据传输的 USB 线。只充电的线不能刷写。
- ESP32 或 ESP32-C3 开发板。
- 杜邦线。
- 已安装 ESPHome 的环境。
- Home Assistant 已经有 `Retro Monitor` 数据实体时，显示屏才能显示真实数据。

建议工具：

- 万用表，用来确认电源正负和线序。
- 镊子或小螺丝刀，用来按住 BOOT / RESET。
- 一张纸，先把线序写下来再接线。

## 2. 安装 ESPHome

如果你已经在 Home Assistant 里使用 ESPHome 插件，可以在插件里导入 YAML。下面是命令行方式。

在项目目录中安装或确认 ESPHome：

```bash
cd /Users/ian/retro-monitor
python3 -m venv .venv
source .venv/bin/activate
pip install esphome
```

检查 ESPHome 是否可用：

```bash
python3 -m esphome version
```

如果你的系统里已经有 `esphome` 命令，也可以直接用：

```bash
esphome version
```

后文命令会写成 `python3 -m esphome ...`。如果你使用全局命令，把前面的 `python3 -m` 去掉即可。

## 3. 配置 Wi-Fi 密码

ESPHome 会从 `esphome/secrets.yaml` 读取 Wi-Fi 名称和密码。

创建或编辑：

```text
esphome/secrets.yaml
```

最少需要：

```yaml
wifi_ssid: "你的WiFi名称"
wifi_password: "你的WiFi密码"
```

注意：

- Wi-Fi 名称和密码区分大小写。
- 如果名称里有空格，保留引号。
- ESP32 通常使用 `2.4GHz` Wi-Fi，不建议使用只有 `5GHz` 的网络。

### VFD 固件里的固定 BSSID

当前 `esphome/vfd_016st106ink_ha_monitor.yaml` 里为了稳定连接，写了固定 `bssid` 和 `channel`。

如果你不是在同一个路由器/AP 下使用，首次刷写前建议先把这两行改成你自己的 AP，或者先注释掉：

```yaml
bssid: 44:DF:65:DA:7C:6A
channel: 4
```

改成：

```yaml
# bssid: 44:DF:65:DA:7C:6A
# channel: 4
```

否则设备可能一直连不上你的 Wi-Fi。

## 4. 路线 A：SSD1322 OLED 接线

适用文件：

```text
esphome/oled_display_p1_demo.yaml
```

当前使用的是 SSD1322 16-pin 模块的 `4SPI` 模式。

### 4.1 OLED 接线表

| OLED 引脚 | 屏幕标识 | 作用 | 接到 ESP32 |
| --- | --- | --- | --- |
| 1 | `VSS` | 地 | `GND` |
| 2 | `VCC` | 电源 | `3V3` 或模块额定电源 |
| 3 | `NC` | 不接 | 悬空 |
| 4 | `SCL` | SPI 时钟 | `GPIO18` |
| 5 | `SDA` | SPI 数据 | `GPIO23` |
| 6 | `D2` | 并口数据 | 悬空 |
| 7 | `D3` | 并口数据 | 悬空 |
| 8 | `D4` | 并口数据 | 悬空 |
| 9 | `D5` | 并口数据 | 悬空 |
| 10 | `D6` | 并口数据 | 悬空 |
| 11 | `D7` | 并口数据 | 悬空 |
| 12 | `RD` | 读控制 | 接 `GND` |
| 13 | `WR` | 写控制 | 接 `GND` |
| 14 | `DC` | 数据/命令 | `GPIO16` |
| 15 | `RES` | 复位 | `GPIO17` |
| 16 | `CS` | 片选 | `GPIO5` |

### 4.2 OLED 接线顺序

1. 先不要插 USB。
2. 先接 `GND`：OLED `VSS` -> ESP32 `GND`。
3. 再接电源：OLED `VCC` -> ESP32 `3V3`，或接模块明确要求的电源。
4. 接 SPI 两根线：`SCL` -> `GPIO18`，`SDA` -> `GPIO23`。
5. 接控制线：`DC` -> `GPIO16`，`RES` -> `GPIO17`，`CS` -> `GPIO5`。
6. 把 `RD` 和 `WR` 接到 `GND`。
7. `NC`、`D2-D7` 不接。
8. 检查一遍有没有把 `VCC` 和 `GND` 接反。
9. 再插 USB。

### 4.3 OLED 刷写

先做配置检查：

```bash
cd /Users/ian/retro-monitor
source .venv/bin/activate
python3 -m esphome config esphome/oled_display_p1_demo.yaml
```

如果配置通过，插上 ESP32，查看串口：

```bash
ls /dev/cu.*
```

常见串口名类似：

```text
/dev/cu.usbserial-xxxx
/dev/cu.SLAB_USBtoUART
/dev/cu.wchusbserialxxxx
```

首次 USB 刷写：

```bash
python3 -m esphome run esphome/oled_display_p1_demo.yaml --device /dev/cu.usbserial-xxxx
```

把 `/dev/cu.usbserial-xxxx` 换成你实际看到的串口。

刷写完成后，如果屏幕不亮，先看第 9 节故障排查。

## 5. 路线 B：ESP32-C3 + 016ST106INK VFD 接线

适用文件：

```text
esphome/vfd_016st106ink_ha_monitor.yaml
```

当前项目已经验证过这套 ESP32-C3 SuperMini 引脚映射：

| VFD 信号 | 作用 | 接到 ESP32-C3 |
| --- | --- | --- |
| `GND` | 地 | `GND` |
| `VCC` | 模块电源 | 按模块要求接 `5V` 或指定电源 |
| `RST` | 复位 | `GPIO0` |
| `CS` | 片选 | `GPIO1` |
| `CP` | 时钟 | `GPIO4` |
| `DA` | 数据 | `GPIO5` |
| `EN` | 使能/电源控制 | `GPIO6` |

重要说明：

- 016ST106INK 模块已集成升压/驱动电路，但它不是普通低压像素屏。
- `VCC` 应按你手上模块的资料接，不要凭感觉接。
- `EN` 在当前驱动里按开漏输出处理，不要随便改接线。

### 5.1 VFD 接线顺序

1. 先不要插 USB。
2. 先接 `GND`：VFD `GND` -> ESP32-C3 `GND`。
3. 接电源：VFD `VCC` -> 模块要求的电源脚。
4. 接 `RST` -> `GPIO0`。
5. 接 `CS` -> `GPIO1`。
6. 接 `CP` -> `GPIO4`。
7. 接 `DA` -> `GPIO5`。
8. 接 `EN` -> `GPIO6`。
9. 检查线序，尤其是 `VCC`、`GND`、`CP`、`DA` 不要接反。
10. 再插 USB。

### 5.2 VFD 刷写

先做配置检查：

```bash
cd /Users/ian/retro-monitor
source .venv/bin/activate
python3 -m esphome config esphome/vfd_016st106ink_ha_monitor.yaml
```

插上 ESP32-C3，查看串口：

```bash
ls /dev/cu.*
```

首次 USB 刷写：

```bash
python3 -m esphome run esphome/vfd_016st106ink_ha_monitor.yaml --device /dev/cu.usbmodemXXXX
```

如果你的串口不是 `/dev/cu.usbmodemXXXX`，换成实际名称。

### 5.3 ESP32-C3 进入下载模式

如果刷写时提示连接失败，ESP32-C3 可能没有自动进入下载模式。按这个顺序试：

1. 按住 `BOOT`。
2. 点按一下 `RESET`。
3. 松开 `RESET`。
4. 继续按住 `BOOT`，重新执行刷写命令。
5. 看到开始写入后松开 `BOOT`。

刷写完成后如果程序没有自动运行，按一下 `RESET`。

## 6. 设备第一次启动后会发生什么

刷写完成后，ESP32 会：

1. 重启。
2. 尝试连接 `wifi_ssid`。
3. 连接成功后启动 ESPHome API。
4. Home Assistant 会发现新 ESPHome 设备，或你可以手动添加。
5. OLED / VFD 从 HA 读取 `desktop_current_*` 实体。

如果设备连不上 Wi-Fi，ESPHome 会开启一个临时热点：

- OLED：`RetroMonitor Setup`
- VFD：`Retro VFD Fallback`

可以用手机或电脑连接这个热点，进入 captive portal 修改 Wi-Fi。

## 7. 接入 Home Assistant

前提：

- Home Assistant 已安装 ESPHome 集成。
- Home Assistant 和 ESP32 在同一个网络，或彼此可访问。
- Retro Monitor 的电脑遥测已经接入，HA 中已有 `desktop_current_*` 实体。

在 Home Assistant 中：

1. 打开 `设置 -> 设备与服务`。
2. 如果看到 ESPHome 新设备发现提示，点添加。
3. 如果没有自动发现，点 `添加集成 -> ESPHome`。
4. 输入设备地址，例如：
   - OLED：`retro-monitor-display.local`
   - VFD：`retro-vfd-monitor.local`
5. 添加成功后，应该能看到设备实体。

如果 `.local` 地址不通，可以去路由器后台查看 ESP32 的 IP，直接输入 IP。

## 8. 后续 OTA 更新

第一次 USB 刷写成功、设备能连上 Wi-Fi 后，后续可以 OTA。

OLED：

```bash
python3 -m esphome run esphome/oled_display_p1_demo.yaml --device retro-monitor-display.local
```

VFD：

```bash
python3 -m esphome run esphome/vfd_016st106ink_ha_monitor.yaml --device retro-vfd-monitor.local
```

如果 `.local` 不稳定，改用 IP：

```bash
python3 -m esphome run esphome/vfd_016st106ink_ha_monitor.yaml --device 192.168.50.xxx
```

## 9. 常见故障排查

### 9.1 找不到串口

现象：

- `ls /dev/cu.*` 看不到新的 USB 设备。
- ESPHome 提示找不到串口。

检查：

- USB 线是不是数据线。
- ESP32 是否正常上电。
- 是否需要安装 CH340 / CP210x 驱动。
- 换一个 USB 口。

### 9.2 刷写时一直 Connecting

检查：

- 按 BOOT / RESET 进入下载模式。
- ESP32-C3 按第 5.3 节操作。
- 串口是否选错。
- 是否有其它程序占用串口。

macOS 上可以查看串口占用：

```bash
lsof /dev/cu.usb*
```

### 9.3 OLED 不亮

按顺序检查：

1. `VCC` 和 `GND` 是否接反。
2. OLED 模块电源要求是否正确。
3. `SCL` 是否接 `GPIO18`。
4. `SDA` 是否接 `GPIO23`。
5. `DC` / `RES` / `CS` 是否分别接 `GPIO16` / `GPIO17` / `GPIO5`。
6. `RD` 和 `WR` 是否接到 `GND`。
7. YAML 是否是 `esphome/oled_display_p1_demo.yaml`。

### 9.4 VFD 不亮

按顺序检查：

1. VFD 模块电源是否符合模块要求。
2. `GND` 是否和 ESP32-C3 共地。
3. `EN` 是否接 `GPIO6`。
4. `RST` / `CS` / `CP` / `DA` 是否分别接 `GPIO0` / `GPIO1` / `GPIO4` / `GPIO5`。
5. 刷写后是否按过 `RESET`。
6. 是否先用 `esphome/vfd_016st106ink_smoke_test.yaml` 做过冒烟测试。

### 9.5 能开机但 HA 里没数据

检查：

- Home Assistant 是否已经接入 ESPHome 设备。
- HA 中是否存在：
  - `sensor.desktop_current_cpu_temperature`
  - `sensor.desktop_current_gpu_temperature`
  - `sensor.desktop_current_memory_usage`
  - `binary_sensor.desktop_current_source_ok`
- 电脑端 Retro Monitor agent 是否运行。
- HA 的 `Retro Monitor` 集成是否在线。

### 9.6 设备显示离线或连不上 Wi-Fi

检查：

- `esphome/secrets.yaml` 里的 Wi-Fi 名称和密码。
- Wi-Fi 是否是 `2.4GHz`。
- VFD YAML 中的 `bssid` / `channel` 是否锁到了错误 AP。
- 设备距离路由器是否太远。

## 10. 建议的第一次上手顺序

如果你完全是第一次做，建议按这个节奏：

1. 先不要接屏幕，只插 ESP32，确认电脑能看到串口。
2. 写好 `esphome/secrets.yaml`。
3. 运行 `esphome config`，确认 YAML 没错误。
4. USB 首刷。
5. 看 ESP32 是否能连 Wi-Fi。
6. 再断电接屏幕线。
7. 再上电看屏幕是否点亮。
8. 接入 Home Assistant。
9. 确认 `desktop_current_*` 数据存在。
10. 最后再刷完整显示固件或做 OTA 更新。

这个顺序的好处是：如果出问题，你能分清是 USB、Wi-Fi、屏幕接线，还是 Home Assistant 数据源的问题。

