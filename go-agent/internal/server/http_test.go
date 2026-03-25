package server

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/ian/retro-monitor/go-agent/internal/provider"
)

func TestTelemetryEndpoint(t *testing.T) {
	handler := NewHandler(provider.NewMockProvider())
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
