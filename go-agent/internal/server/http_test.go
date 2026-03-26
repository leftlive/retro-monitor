package server

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/ian/retro-monitor/go-agent/internal/provider"
)

func TestTelemetryEndpoint(t *testing.T) {
	sampler := NewSampler(provider.NewMockProvider(), 50*time.Millisecond)
	if err := sampler.Start(); err != nil {
		t.Fatalf("start sampler: %v", err)
	}
	handler := NewHandler(sampler)
	req := httptest.NewRequest(http.MethodGet, "/telemetry", nil)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("unexpected status: %d", rec.Code)
	}

	var payload map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &payload); err != nil {
		t.Fatalf("unmarshal response: %v", err)
	}

	if payload["platform"] != "mock" {
		t.Fatalf("unexpected platform: %v", payload["platform"])
	}
}

func TestTelemetryEndpointUnavailableWithoutSnapshot(t *testing.T) {
	sampler := NewSampler(provider.NewMockProvider(), time.Second)
	handler := NewHandler(sampler)
	req := httptest.NewRequest(http.MethodGet, "/telemetry", nil)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusServiceUnavailable {
		t.Fatalf("unexpected status: %d", rec.Code)
	}
}
