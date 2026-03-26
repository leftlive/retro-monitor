package provider

import (
	"testing"

	"github.com/shirou/gopsutil/v4/disk"
)

func TestMountedBSDNames(t *testing.T) {
	partitions := []disk.PartitionStat{
		{Device: "/dev/disk3s4s1"},
		{Device: "/dev/disk3s4s1"},
		{Device: "/dev/disk0s1"},
		{Device: "map auto_home"},
	}

	got := mountedBSDNames(partitions)
	want := []string{"disk3s4s1", "disk0s1"}
	if len(got) != len(want) {
		t.Fatalf("len=%d want=%d (%v)", len(got), len(want), got)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("got[%d]=%q want=%q", i, got[i], want[i])
		}
	}
}

func TestDecodeSMCNumeric(t *testing.T) {
	tests := []struct {
		name    string
		typ     string
		payload []byte
		want    float64
		ok      bool
	}{
		{name: "sp78", typ: "sp78", payload: []byte{0x47, 0x00}, want: 71, ok: true},
		{name: "sp96", typ: "sp96", payload: []byte{0x01, 0x80}, want: 6, ok: true},
		{name: "float", typ: "flt ", payload: []byte{0x00, 0x00, 0x48, 0x42}, want: 50, ok: true},
		{name: "unknown", typ: "ui8 ", payload: []byte{0x07}, want: 0, ok: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, ok := decodeSMCNumeric(tt.typ, tt.payload)
			if ok != tt.ok {
				t.Fatalf("ok=%v want=%v", ok, tt.ok)
			}
			if ok && got != tt.want {
				t.Fatalf("got=%v want=%v", got, tt.want)
			}
		})
	}
}
