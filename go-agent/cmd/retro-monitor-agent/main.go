package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"

	"github.com/ian/retro-monitor/go-agent/internal/provider"
	"github.com/ian/retro-monitor/go-agent/internal/server"
)

func main() {
	var (
		providerName = flag.String("provider", "mock", "provider to use: mock or macos")
		host         = flag.String("host", "127.0.0.1", "listen host")
		port         = flag.Int("port", 8126, "listen port")
	)
	flag.Parse()

	p, err := provider.Build(*providerName)
	if err != nil {
		log.Fatalf("build provider: %v", err)
	}

	addr := fmt.Sprintf("%s:%d", *host, *port)
	log.Printf("retro-monitor-go listening on http://%s/telemetry", addr)
	log.Fatal(http.ListenAndServe(addr, server.NewHandler(p)))
}

