package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/ian/retro-monitor/go-agent/internal/provider"
	"github.com/ian/retro-monitor/go-agent/internal/server"
)

func main() {
	var (
		providerName = flag.String("provider", "mock", "provider to use: mock or macos")
		host         = flag.String("host", "127.0.0.1", "listen host")
		port         = flag.Int("port", 8126, "listen port")
		sampleInt    = flag.Duration("sample-interval", 500*time.Millisecond, "background sample interval")
	)
	flag.Parse()

	p, err := provider.Build(*providerName)
	if err != nil {
		log.Fatalf("build provider: %v", err)
	}
	if closer, ok := p.(provider.Closer); ok {
		defer func() {
			if err := closer.Close(); err != nil {
				log.Printf("provider close: %v", err)
			}
		}()
	}

	sampler := server.NewSampler(p, *sampleInt)
	if err := sampler.Start(); err != nil {
		log.Fatalf("start sampler: %v", err)
	}

	addr := fmt.Sprintf("%s:%d", *host, *port)
	log.Printf("retro-monitor-go listening on http://%s/telemetry", addr)
	httpServer := &http.Server{
		Addr:    addr,
		Handler: server.NewHandler(sampler),
	}

	go func() {
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("listen: %v", err)
		}
	}()

	signals := make(chan os.Signal, 1)
	signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
	<-signals

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := httpServer.Shutdown(shutdownCtx); err != nil {
		log.Printf("shutdown: %v", err)
	}
}
