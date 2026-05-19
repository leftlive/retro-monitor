# Home Assistant 端配置教程

Home Assistant 负责把采集端数据变成实体，并提供给 OLED 屏幕读取。

配置前请先确认至少有一个采集端已经能访问：

```bash
curl http://<agent-ip>:8125/telemetry
```

## 1. 安装自定义集成

把集成目录复制到 Home Assistant 配置目录：

```bash
cp -R homeassistant/custom_components/retro_monitor \
  /path/to/homeassistant/config/custom_components/
```

重启 Home Assistant。

## 2. 添加电脑采集端

在 Home Assistant 中打开：

```text
设置 -> 设备与服务 -> 添加集成
```

搜索并添加：

```text
Retro Monitor
```

填写：

| 字段 | 示例 |
| --- | --- |
| Host | `<agent-ip>` |
| Port | `8125` |
| Path | `/telemetry` |
| Scan interval | `1` |

保存前，集成会先测试接口。如果提示无法连接，请确认 Home Assistant 所在设备能访问采集端 IP 和端口。

## 3. 启用统一聚合实体

OLED 固件默认读取 `desktop_current_*` 这一组稳定实体。复制 package 文件：

```bash
mkdir -p /path/to/homeassistant/config/packages
cp homeassistant/packages/retro_monitor_desktop_current.yaml \
  /path/to/homeassistant/config/packages/
```

确认 `configuration.yaml` 中启用了 packages：

```yaml
homeassistant:
  packages: !include_dir_named packages
```

重启 Home Assistant。

## 4. 检查实体

在开发者工具里搜索：

```text
desktop_current
```

常用实体包括：

- `sensor.desktop_current_display_payload`
- `sensor.desktop_current_cpu_temperature`
- `sensor.desktop_current_cpu_load`
- `sensor.desktop_current_gpu_temperature`
- `sensor.desktop_current_gpu_load`
- `sensor.desktop_current_memory_usage`
- `binary_sensor.desktop_current_source_ok`

如果这些实体存在，OLED 就可以从 Home Assistant 读取电脑状态。

## 5. 可选：添加 OpenWrt 路由器状态

复制路由器 package：

```bash
cp homeassistant/packages/retro_monitor_router.yaml \
  /path/to/homeassistant/config/packages/
```

按你的网络环境修改其中的路由器接口地址，然后重启 Home Assistant。

## 6. 下一步

Home Assistant 配好后，继续接线和刷写 OLED：

[硬件连接及烧录教程](hardware-flashing-guide-zh.md)
