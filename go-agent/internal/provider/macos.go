package provider

import (
	"os"
	"runtime"
	"strings"
	"time"

	"github.com/shirou/gopsutil/v4/cpu"
	"github.com/shirou/gopsutil/v4/disk"
	"github.com/shirou/gopsutil/v4/mem"
	"github.com/shirou/gopsutil/v4/net"

	"github.com/ian/retro-monitor/go-agent/internal/schema"
)

type MacOSProvider struct {
	hostname      string
	lastNet       net.IOCountersStat
	lastNetAt     time.Time
	lastDisk      disk.IOCountersStat
	lastDiskAt    time.Time
	netPrimed     bool
	diskPrimed    bool
}

func NewMacOSProvider() *MacOSProvider {
	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "localhost"
	}

	p := &MacOSProvider{
		hostname: hostname,
	}

	if counters, err := net.IOCounters(false); err == nil && len(counters) > 0 {
		p.lastNet = counters[0]
		p.lastNetAt = time.Now()
		p.netPrimed = true
	}

	if counters, err := disk.IOCounters(); err == nil {
		p.lastDisk = sumDiskCounters(counters)
		p.lastDiskAt = time.Now()
		p.diskPrimed = true
	}

	return p
}

func (p *MacOSProvider) Sample() (schema.Snapshot, error) {
	out := schema.Empty(p.hostname, p.hostname, "macos_"+runtime.GOARCH)
	out.Timestamp = time.Now().UTC().Format(time.RFC3339)

	if percents, err := cpu.Percent(0, false); err == nil && len(percents) > 0 {
		out.CPULoad = f64(round1(percents[0]))
	}

	if freqs, err := cpu.Info(); err == nil && len(freqs) > 0 {
		out.CPUClock = f64(round1(freqs[0].Mhz))
	}

	if vm, err := mem.VirtualMemory(); err == nil {
		out.MemoryUsedMB = f64(round1(float64(vm.Used) / 1024.0 / 1024.0))
		out.MemoryTotalMB = f64(round1(float64(vm.Total) / 1024.0 / 1024.0))
		out.MemoryPercent = f64(round1(vm.UsedPercent))
	}

	if counters, err := net.IOCounters(false); err == nil && len(counters) > 0 {
		now := time.Now()
		if p.netPrimed {
			elapsed := now.Sub(p.lastNetAt).Seconds()
			if elapsed > 0 {
				up := float64(counters[0].BytesSent-p.lastNet.BytesSent) * 8.0 / elapsed
				down := float64(counters[0].BytesRecv-p.lastNet.BytesRecv) * 8.0 / elapsed
				out.NetUpBPS = f64(round1(up))
				out.NetDownBPS = f64(round1(down))
			}
		}
		p.lastNet = counters[0]
		p.lastNetAt = now
		p.netPrimed = true
	}

	if counters, err := disk.IOCounters(); err == nil {
		now := time.Now()
		total := sumDiskCounters(counters)
		if p.diskPrimed {
			elapsedMS := now.Sub(p.lastDiskAt).Seconds() * 1000.0
			if elapsedMS > 0 {
				busyMS := float64((total.ReadTime + total.WriteTime) - (p.lastDisk.ReadTime + p.lastDisk.WriteTime))
				if busyMS < 0 {
					busyMS = 0
				}
				percent := busyMS / elapsedMS * 100.0
				if percent > 100 {
					percent = 100
				}
				out.DiskActivityPercent = f64(round1(percent))
			}
		}
		p.lastDisk = total
		p.lastDiskAt = now
		p.diskPrimed = true
	}

	out.SourceOK = hasAny(
		out.CPULoad,
		out.CPUClock,
		out.MemoryPercent,
		out.NetUpBPS,
		out.NetDownBPS,
	)

	return out, nil
}

func sumDiskCounters(counters map[string]disk.IOCountersStat) disk.IOCountersStat {
	var total disk.IOCountersStat
	for name, stat := range counters {
		if strings.HasPrefix(name, "disk") {
			total.ReadTime += stat.ReadTime
			total.WriteTime += stat.WriteTime
		}
	}
	return total
}

func round1(v float64) float64 {
	return float64(int(v*10+0.5)) / 10
}

func hasAny(values ...*float64) bool {
	for _, v := range values {
		if v != nil {
			return true
		}
	}
	return false
}

