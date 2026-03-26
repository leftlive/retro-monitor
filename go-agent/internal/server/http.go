package server

import (
	"encoding/json"
	"log"
	"net/http"
	"sync"
	"time"

	"github.com/ian/retro-monitor/go-agent/internal/provider"
	"github.com/ian/retro-monitor/go-agent/internal/schema"
)

type Sampler struct {
	provider provider.Provider
	interval time.Duration

	mu       sync.RWMutex
	snapshot *schema.Snapshot
}

func NewSampler(p provider.Provider, interval time.Duration) *Sampler {
	return &Sampler{
		provider: p,
		interval: interval,
	}
}

func (s *Sampler) Start() error {
	if err := s.SampleOnce(); err != nil {
		return err
	}

	go func() {
		ticker := time.NewTicker(s.interval)
		defer ticker.Stop()
		for range ticker.C {
			if err := s.SampleOnce(); err != nil {
				log.Printf("retro-monitor-go sampler: %v", err)
				s.mu.Lock()
				if s.snapshot != nil {
					degraded := *s.snapshot
					degraded.SourceOK = false
					s.snapshot = &degraded
				}
				s.mu.Unlock()
			}
		}
	}()

	return nil
}

func (s *Sampler) SampleOnce() error {
	snapshot, err := s.provider.Sample()
	if err != nil {
		return err
	}
	s.mu.Lock()
	s.snapshot = &snapshot
	s.mu.Unlock()
	return nil
}

func (s *Sampler) Current() *schema.Snapshot {
	s.mu.RLock()
	defer s.mu.RUnlock()
	if s.snapshot == nil {
		return nil
	}
	copy := *s.snapshot
	return &copy
}

func NewHandler(sampler *Sampler) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/telemetry", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		snapshot := sampler.Current()
		if snapshot == nil {
			http.Error(w, "telemetry unavailable", http.StatusServiceUnavailable)
			return
		}

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_ = json.NewEncoder(w).Encode(snapshot)
	})
	return mux
}
