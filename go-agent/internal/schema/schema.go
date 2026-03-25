package schema

import "time"

type Snapshot struct {
	DeviceID             string   `json:"device_id"`
	Hostname             string   `json:"hostname"`
	Platform             string   `json:"platform"`
	Timestamp            string   `json:"timestamp"`
	SourceOK             bool     `json:"source_ok"`
	CPUTemp              *float64 `json:"cpu_temp"`
	CPULoad              *float64 `json:"cpu_load"`
	CPUClock             *float64 `json:"cpu_clock"`
	CPUPower             *float64 `json:"cpu_power"`
	GPUTemp              *float64 `json:"gpu_temp"`
	GPULoad              *float64 `json:"gpu_load"`
	GPUClock             *float64 `json:"gpu_clock"`
	GPUPower             *float64 `json:"gpu_power"`
	MemoryUsedMB         *float64 `json:"memory_used_mb"`
	MemoryTotalMB        *float64 `json:"memory_total_mb"`
	MemoryPercent        *float64 `json:"memory_percent"`
	FanRPMMax            *float64 `json:"fan_rpm_max"`
	FanRPMAvg            *float64 `json:"fan_rpm_avg"`
	DiskTempMax          *float64 `json:"disk_temp_max"`
	DiskActivityPercent  *float64 `json:"disk_activity_percent"`
	NetUpBPS             *float64 `json:"net_up_bps"`
	NetDownBPS           *float64 `json:"net_down_bps"`
	SystemPowerEstimated *float64 `json:"system_power_estimated"`
}

func Empty(deviceID, hostname, platform string) Snapshot {
	return Snapshot{
		DeviceID:  deviceID,
		Hostname:  hostname,
		Platform:  platform,
		Timestamp: time.Now().UTC().Format(time.RFC3339),
		SourceOK:  false,
	}
}

