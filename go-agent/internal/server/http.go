package server

import (
	"encoding/json"
	"net/http"

	"github.com/ian/retro-monitor/go-agent/internal/provider"
)

func NewHandler(p provider.Provider) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/telemetry", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		snapshot, err := p.Sample()
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_ = json.NewEncoder(w).Encode(snapshot)
	})
	return mux
}

