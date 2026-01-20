package main

// The Eye - Agent
import (
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/nullvoider07/eye/pkg/capture"
	"github.com/nullvoider07/eye/pkg/transport"
)

// Agent represents the screen capture agent
type Agent struct {
	engine   *capture.Engine
	client   *transport.Client
	interval time.Duration
	frameID  int64
	running  bool
}

// NewAgent creates a new Agent instance
func NewAgent(serverURL, token string, interval time.Duration) *Agent {
	return &Agent{
		engine: capture.New(capture.Config{
			Interval: interval,
			Format:   "png",
		}),
		client:   transport.NewClient(serverURL, token),
		interval: interval,
		frameID:  0,
	}
}

// waitForServer waits until the server is reachable or timeout occurs
func (a *Agent) waitForServer(timeout time.Duration) error {
	log.Println("[INFO] Waiting for server...")
	start := time.Now()
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		if err := a.client.HealthCheck(); err == nil {
			log.Println("[INFO] Server ready!")
			return nil
		}
		if time.Since(start) > timeout {
			return fmt.Errorf("server timeout")
		}
	}
	return fmt.Errorf("server wait interrupted")
}

// captureAndUpload captures a frame and uploads it to the server
func (a *Agent) captureAndUpload() error {
	frame, err := a.engine.CaptureFrame(a.frameID)
	if err != nil {
		return err
	}

	if err := a.client.UploadFrame(frame.ID, frame.Data); err != nil {
		return err
	}

	log.Printf("[OK] Frame #%d uploaded (%.1f KB)", frame.ID, float64(frame.SizeBytes)/1024.0)
	a.frameID++
	return nil
}

// Start begins the agent's capture and upload loop
func (a *Agent) Start() error {
	if err := a.waitForServer(30 * time.Second); err != nil {
		return err
	}

	a.running = true
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, os.Interrupt, syscall.SIGTERM)

	ticker := time.NewTicker(a.interval)
	defer ticker.Stop()

	log.Println("[INFO] Starting capture loop...")

	for a.running {
		select {
		case <-ticker.C:
			if err := a.captureAndUpload(); err != nil {
				log.Printf("[ERROR] %v", err)
			}
		case <-sigChan:
			log.Println("[INFO] Stopping...")
			a.running = false
		}
	}

	return nil
}

// main is the entry point of the agent application
func main() {
	serverURL := os.Getenv("EYE_SERVER_URL")
	if serverURL == "" {
		log.Fatal("[ERROR] EYE_SERVER_URL required")
	}

	token := os.Getenv("EYE_AUTH_TOKEN")
	interval := 1500 * time.Millisecond

	log.Printf("[INFO] Server: %s", serverURL)
	log.Printf("[INFO] Interval: %.1fs", interval.Seconds())

	agent := NewAgent(serverURL, token, interval)
	if err := agent.Start(); err != nil {
		log.Fatalf("[ERROR] %v", err)
	}
}
