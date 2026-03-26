package provider

import (
	"os"
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
	smc           *appleSMC
	intelPower    *intelPowerGadget
}

func NewMacOSProvider() *MacOSProvider {
	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "localhost"
	}

	p := &MacOSProvider{
		hostname: hostname,
	}

	if smc, err := newAppleSMC(); err == nil {
		p.smc = smc
	}
	if gadget, err := newIntelPowerGadget(); err == nil {
		p.intelPower = gadget
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

func (p *MacOSProvider) Close() error {
	if p == nil {
		return nil
	}
	if p.smc != nil {
		p.smc.Close()
		p.smc = nil
	}
	if p.intelPower != nil {
		p.intelPower.Close()
		p.intelPower = nil
	}
	return nil
}

func (p *MacOSProvider) Sample() (schema.Snapshot, error) {
	out := schema.Empty(p.hostname, p.hostname, "macos_hackintosh")
	out.Timestamp = time.Now().UTC().Format(time.RFC3339)

	if p.smc != nil {
		out.CPUTemp = p.smc.cpuTemperature()
		out.CPUPower = p.smc.cpuPower()

		fanCount := p.smc.fanCount()
		var fanValues []float64
		for i := 0; i < fanCount; i++ {
			if speed := p.smc.fanSpeed(i); speed != nil {
				fanValues = append(fanValues, *speed)
			}
		}
		if len(fanValues) > 0 {
			maxFan := fanValues[0]
			total := 0.0
			for _, speed := range fanValues {
				total += speed
				if speed > maxFan {
					maxFan = speed
				}
			}
			out.FanRPMMax = f64(round1(maxFan))
			out.FanRPMAvg = f64(round1(total / float64(len(fanValues))))
		}
	}

	out.GPUTemp = readGPUStat("Temperature(C)")
	out.GPULoad = readGPUStat("GPU Activity(%)")
	out.GPUClock = readGPUStat("Core Clock(MHz)")
	out.GPUPower = readGPUStat("Total Power(W)")

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

	if partitions, err := disk.Partitions(false); err == nil {
		out.DiskTempMax = readNVMeTemperatureMax(mountedBSDNames(partitions))
	}

	if direct := func() *float64 {
		if p.intelPower == nil {
			return nil
		}
		return p.intelPower.platformPower()
	}(); direct != nil {
		out.SystemPowerEstimated = direct
	} else if out.CPUPower != nil || out.GPUPower != nil {
		estimate := 20.0
		if out.CPUPower != nil {
			estimate += *out.CPUPower
		}
		if out.GPUPower != nil {
			estimate += *out.GPUPower
		}
		out.SystemPowerEstimated = f64(round1(estimate))
	}

	out.SourceOK = hasAny(
		out.CPUTemp,
		out.CPULoad,
		out.CPUPower,
		out.CPUClock,
		out.GPUTemp,
		out.GPULoad,
		out.MemoryPercent,
		out.NetUpBPS,
		out.NetDownBPS,
	)

	return out, nil
}

func mountedBSDNames(partitions []disk.PartitionStat) []string {
	seen := map[string]struct{}{}
	var out []string
	for _, partition := range partitions {
		if !strings.HasPrefix(partition.Device, "/dev/") {
			continue
		}
		name := strings.TrimPrefix(partition.Device, "/dev/")
		if _, ok := seen[name]; ok {
			continue
		}
		seen[name] = struct{}{}
		out = append(out, name)
	}
	return out
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

func hasAny(values ...*float64) bool {
	for _, v := range values {
		if v != nil {
			return true
		}
	}
	return false
}
