package provider

import (
	"fmt"

	"github.com/ian/retro-monitor/go-agent/internal/schema"
)

type Provider interface {
	Sample() (schema.Snapshot, error)
}

func Build(name string) (Provider, error) {
	switch name {
	case "mock":
		return NewMockProvider(), nil
	case "macos":
		return NewMacOSProvider(), nil
	default:
		return nil, fmt.Errorf("unsupported provider: %s", name)
	}
}

