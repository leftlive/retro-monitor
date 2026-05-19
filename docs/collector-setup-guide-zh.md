# 采集端配置教程

采集端负责把电脑或路由器的状态变成一个 HTTP 接口。Home Assistant 会定时访问这个接口。

你只需要根据自己的设备选择一种或多种采集端：

| 设备 | 推荐采集端 | 默认接口 |
| --- | --- | --- |
| macOS | `go-agent/` | `http://电脑IP:8125/telemetry` |
| Windows | `windows-agent/` | `http://电脑IP:8125/telemetry` |
| OpenWrt / iStoreOS | `openwrt/` | `http://路由器IP/cgi-bin/retro-monitor-router` |

## 1. macOS 采集端

进入仓库目录：

```bash
cd /path/to/retro-monitor/go-agent
```

临时运行：

```bash
go run ./cmd/retro-monitor-agent --provider macos --host 0.0.0.0 --port 8125 --sample-interval 500ms
```

在同一台电脑上测试：

```bash
curl http://127.0.0.1:8125/telemetry
```

能看到 JSON 就说明采集端已启动。

安装为后台服务：

```bash
cd /path/to/retro-monitor
./scripts/install_macos_agent.sh
```

查看日志：

```bash
tail -n 100 ~/Library/Logs/retro-monitor/agent.stderr.log
```

## 2. Windows 采集端

在 Windows PowerShell 中进入项目目录：

```powershell
cd C:\path\to\retro-monitor\windows-agent\RetroMonitor.WindowsAgent
```

编译并运行：

```powershell
dotnet restore
dotnet build
dotnet run
```

测试接口：

```powershell
curl http://127.0.0.1:8125/telemetry
```

查看当前电脑能读取到哪些传感器：

```powershell
dotnet run -- --dump-sensors
```

安装为 Windows Service：

```powershell
cd C:\path\to\retro-monitor
.\windows-agent\install-windows-agent.ps1
```

部分硬件传感器需要管理员权限。如果某些字段是 `null`，通常表示当前硬件或驱动没有暴露对应传感器。

## 3. OpenWrt / iStoreOS 采集端

复制脚本到路由器：

```bash
scp openwrt/router_telemetry.sh root@<router-ip>:/usr/local/bin/router_telemetry.sh
scp openwrt/router_telemetry.cgi root@<router-ip>:/www/cgi-bin/retro-monitor-router
ssh root@<router-ip> "chmod +x /usr/local/bin/router_telemetry.sh /www/cgi-bin/retro-monitor-router"
```

测试接口：

```bash
curl http://<router-ip>/cgi-bin/retro-monitor-router
```

能看到 JSON 就说明路由器采集端已可用。

## 4. 下一步

采集端测试通过后，继续配置 Home Assistant：

[Home Assistant 端配置教程](ha-setup-guide-zh.md)
