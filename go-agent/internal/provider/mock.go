package provider

import (
	"os"
	"time"

	"github.com/ian/retro-monitor/go-agent/internal/schema"
)

type MockProvider struct {
	hostname string
}

func NewMockProvider() *MockProvider {
	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "mock-host"
	}
	return &MockProvider{hostname: hostname}
}

func (p *MockProvider) Sample() (schema.Snapshot, error) {
	return schema.Snapshot{
		DeviceID:             "mock-device",
		Hostname:             p.hostname,
		Platform:             "mock",
		Timestamp:            time.Now().UTC().Format(time.RFC3339),
		SourceOK:             true,
		CPUTemp:              f64(54.2),
		CPULoad:              f64(21.4),
		CPUClock:             f64(3875.0),
		CPUPower:             f64(48.6),
		GPUTemp:              f64(49.1),
		GPULoad:              f64(17.0),
		GPUClock:             f64(1425.0),
		GPUPower:             f64(62.3),
		MemoryUsedMB:         f64(12288.0),
		MemoryTotalMB:        f64(32768.0),
		MemoryPercent:        f64(37.5),
		FanRPMMax:            f64(1320.0),
		FanRPMAvg:            f64(1080.0),
		DiskTempMax:          f64(41.0),
		DiskActivityPercent:  f64(12.0),
		NetUpBPS:             f64(4800000.0),
		NetDownBPS:           f64(18500000.0),
		SystemPowerEstimated: f64(126.0),
	}, nil
}

