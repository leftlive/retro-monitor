# Home Assistant 集成 — UX 设计文档

> 版本: v1 · 最后更新: 2026-04-20

## 1. 目标用户

运行 Home Assistant 且希望在一个面板上同时查看 PC 硬件遥测数据和其他智能家居传感器的 Home-lab 爱好者。

背景知识假设：

- 熟悉通过 HACS 或手动复制添加自定义集成。
- 熟悉 Lovelace 面板配置。
- **不**需要理解内部遥测协议或字段编码。

---

## 2. 主要使用场景

| # | 场景 | 用户看到的 |
|---|----------|--------------------|
| 1 | **状态一览** | Lovelace 卡片显示 CPU / GPU 负载、温度和风扇速度 |
| 2 | **异常告警** | 当 `cpu_temp > 85` 或 `source_ok` 变为 off 时触发 HA 自动化 |
| 3 | **历史趋势** | 将功率数据集成到能源面板；在 HA 历史记录中查看温度曲线 |
| 4 | **多设备管理** (未来 v2) | 为每台被监控的 PC 提供独立的设备卡片 |

---

## 3. Home Assistant 在系统中的角色

```
 ┌─────────────┐       GET /telemetry        ┌────────────────┐
 │  遥测代理    │ ◄──── (每 2 秒轮询一次) ─── │ Home Assistant  │
 │    Agent    │                              │      集成      │
 └──────┬──────┘                              └───────┬────────┘
        │                                             │
    本地传感器                                  Lovelace / 自动化
```

- HA 是**观测、聚合和设备接入中心**，而不是底层数据源。
- HA **不**进行单位转换 —— Agent 会完成所有数据的标准化处理。
- HA 在原始遥测数据之上提供**实体状态、历史记录、告警功能**。
- 显示屏控制不属于 `retro_monitor` 集成；OLED / VFD 控制实体由各自 ESPHome 设备提供。

---

## 4. 实体层级

### 4.1 核心传感器 (默认可见)

这些实体默认会出现在实体列表和自动补全中。

| 实体名称 | 协议字段 | 单位 | 设为核心的原因 |
|-------------|---------------|------|----------|
| CPU Temperature | `cpu_temp` | °C | 核心健康指标 |
| CPU Load | `cpu_load` | % | 核心利用率指标 |
| CPU Clock | `cpu_clock` | MHz | 性能上下文 |
| CPU Power | `cpu_power` | W | 电力/散热预算 |
| GPU Temperature | `gpu_temp` | °C | 核心 GPU 指标 |
| GPU Load | `gpu_load` | % | GPU 利用率 |
| GPU Clock | `gpu_clock` | MHz | 性能上下文 |
| GPU Power | `gpu_power` | W | 电力预算 |
| Memory Used | `memory_used_mb` | MiB | 实时消耗量 |
| Memory Usage | `memory_percent` | % | 快速查看利用率 |
| Fan Speed (Max) | `fan_rpm_max` | RPM | 散热健康指标 |
| Disk Activity | `disk_activity_percent` | % | I/O 瓶颈信号 |
| Network Upload | `net_up_bps` | bit/s | 流量监控 |
| Network Download | `net_down_bps` | bit/s | 流量监控 |

### 4.2 诊断传感器 (默认隐藏)

可通过 HA UI 中的“显示全部”进行查看。对排查问题有用，但不需要出现在日常面板上。

| 实体名称 | 协议字段 | 单位 | 设为诊断的原因 |
|-------------|---------------|------|----------------|
| Memory Total | `memory_total_mb` | MiB | 静态值，很少变化 |
| Fan Speed (Average) | `fan_rpm_avg` | RPM | 相比最大 RPM，其实际指导意义较小 |
| Disk Temperature (Max) | `disk_temp_max` | °C | 优先级低于磁盘活动度 |
| System Power (Estimated) | `system_power_estimated` | W | 当前为估算值，适合显示和趋势参考 |

### 4.3 二进制传感器 (诊断)

| 实体名称 | 协议字段 | 类别 |
|-------------|---------------|----------|
| Data Source OK | `source_ok` | DIAGNOSTIC |

- 附加属性: `sample_timestamp`, `agent_platform`.
- 当状态为 **off** 时: 表示数据降级 —— 传感器虽然仍显示数值，但应谨慎对待。

### 4.4 显示控制实体归属

`retro_monitor` 集成不再创建显示控制实体。

当前控制实体归属:

| 设备 | 控制实体 |
|-------------|------|
| OLED ESPHome | `Display Power`, `Brightness`, `Current Page`, `Auto Rotate`, `Auto Rotate Interval`, `API Diagnostics` |
| VFD ESPHome | `Display Power`, `Brightness`, `Animation`, `Sleep Timeout`, `Auto Rotate Interval`, `WiFi Signal`, `Restart` |

设计原因:

- 屏幕亮度、动画、页面状态是终端本地行为。
- HA 集成负责遥测数据，不承担显示设备控制。
- 同一套电脑数据可同时被 OLED 与 VFD 消费。

---

## 5. 降级与失败状态

### 5.1 三层错误模型

```
第一层: 传输失败 (Transport Failure)
  ├── DNS 失败 / 连接被拒绝 / 超时 / 非 2xx 响应 / 无效 JSON
  ├── coordinator 会抛出 UpdateFailed 异常
  └── 所有实体 → 变为 unavailable (不可用)

第二层: 数据解析错误 (Payload Validation Error)
  ├── 即使 HTTP 响应 200 且 JSON 有效，但违反了协议 Schema
  ├── coordinator 会抛出 UpdateFailed 并记录 WARNING 日志
  └── 所有实体 → 变为 unavailable (不可用)

第三层: 数据降级 (Degraded Payload, source_ok=false)
  ├── Schema 有效，但 Agent 信号表明数据过时或不可靠
  ├── coordinator 正常返回数据
  ├── source_ok 二进制传感器 → 变为 off
  ├── 标记为 null 的具体字段 → 变为 unknown (未知)
  └── 非 null 的字段 → 继续显示上一次获取的值
```

### 5.2 用户可见的效果

| 情况 | 实体状态 | 面板显示 |
|-----------|-------------|-----------|
| Agent 运行正常 | 正常数值 | ✅ 所有卡片正常显示 |
| Agent 正常, `source_ok=false` | 显示数值, 二进制传感器为 off | ⚠️ 可能显示警告角标 |
| Agent 正常, `cpu_temp=null` | CPU Temp 显示 "Unknown" | 对应卡片显示 "—" |
| Agent 无法连接 | 所有实体为 "Unavailable" | ❌ 卡片变灰 |
| Agent 返回了畸形的 JSON | 所有实体为 "Unavailable" | ❌ 卡片变灰 |

---

## 6. 设备模型

### 6.1 当前版本 (v1)

- **一个配置项 = HA 设备注册中的一台设备**。
- 设备标识符 (Identity) 来源于 Payload: `device_id` (优先级最高), 其次是 `hostname`, 最后是配置的 `host:port`。
- 设备名称 = Payload 中的 `hostname` (例如: `iandeiMac.local`)。
- 设备型号 = Payload 中的 `platform` (例如: `macos_hackintosh`)。
- `configuration_url` 链接到 Agent 的端点，方便快速检查状态。

### 6.2 未来多设备支持 (v2)

当监控多台 PC 时：

- 每个 Agent 端点都会创建一个独立的配置项和设备。
- `device_id` 确保即使 IP 发生变化，设备身份依然稳定。
- 实体通过 `unique_id = {entry_id}_{field}` 按设备进行划分。
- 用户在面板上能看到多张 PC 硬件监控卡片。

---

## 7. 配置流程 (Config Flow) UX

### 7.1 字段

| 字段 | 默认值 | 校验规则 |
|-------|---------|-----------|
| Host | `127.0.0.1` | 字符串 |
| Port | `8125` | 1–65535 |
| Scan interval | `2` 秒 | 1–60 秒 |

### 7.2 连接测试

在保存配置前，集成会向指定端点发送 `GET /telemetry` 请求，并根据完整的协议 Schema 校验响应数据。失败模式如下：

| 错误信息 | 显示内容 |
|-------|--------------|
| 网络无法连接 | "Cannot connect to the telemetry agent." |
| HTTP 正常但 Schema 无效 | "The endpoint responded but returned an invalid telemetry payload." |
| 重复配置 | "This agent endpoint is already configured." |

---

## 8. 仪表盘配置建议 (Dashboard)

### 推荐的 Lovelace 卡片

1. **Glance card (概览卡片)** — CPU 温度 / CPU 负载 / GPU 温度 / GPU 负载 / 内存利用率
2. **Sensor card (传感器卡片)** — 显示带历史曲线的风扇最大速度
3. **History graph (历史趋势图)** — 将 CPU 功率和 GPU 功率堆叠显示，查看能源监控趋势
4. **Conditional card (条件显示卡片)** — 当 `source_ok` 为 off 时显示警告信息

### 针对自动补全的实体命名

所有实体 ID 均遵循 `sensor.retro_monitor_{field}`。显示名称遵循自然语言习惯：

- ✅ "CPU Temperature" 而不是 ~~"cpu_temp"~~
- ✅ "Fan Speed (Max)" 而不是 ~~"Fan RPM Max"~~
- ✅ "Network Upload" 而不是 ~~"Net Upload"~~

---

## 9. 为什么这套设计比之前的原型 (Scaffold) 更好

| 维度 | 原型 (Scaffold) | v1 正式版 |
|--------|----------|-----|
| 实体层级 | 扁平结构 —— 18 个传感器没有任何区分 | 14 个核心实体 + 4 个诊断实体 |
| 错误处理 | 简单的 `try/except` | 三层细分错误模型 (传输 / 校验 / 降级) |
| 数据校验 | 无 | 每次更新都会进行完整的 Schema 校验 |
| 配置流程 | 无连接测试 | 包含实时连接测试和明确的错误消息 |
| `source_ok=false` | 静默处理 —— 被视为成功获取数据 | 通过二进制传感器和日志明确提示降级 |
| 设备身份 | 首次加载可能失败 | 缓存了 `last_device_info`，能在网络波动时保持稳定 |
| 显示控制 | 由 `retro_monitor` 创建本地偏好实体 | 由 OLED / VFD ESPHome 设备各自创建真实控制实体 |
| 实体命名 | 工程命名风格 (`Fan RPM Max`) | 用户友好风格 (`Fan Speed (Max)`) |

---

## 10. 需要主 Agent 配合的事宜

以下内容无法仅靠 HA 集成层解决：

1. **`system_power_estimated`** — 当前为保守估算值。若未来需要精确功耗，需要接入可靠的硬件级整机功耗来源。
2. **Windows 接入验证** — Windows agent 接入后，需要验证 `desktop_current_*` 聚合层在 macOS / Windows 同时在线时不会频繁跳源。
3. **协议版本字段** — 建议在 Payload 中增加 `schema_version` 键，以便于 HA 集成后续实现优雅的库版本兼容。
