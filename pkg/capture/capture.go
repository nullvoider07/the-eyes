package capture

// capture.go defines the core structures and functions for screen capturing.
import (
	"bytes"
	"image/png"
	"time"
)

// Frame represents a captured screen frame.
type Frame struct {
	ID        int64
	Timestamp time.Time
	Data      []byte
	Width     int
	Height    int
	Format    string
	SizeBytes int64
}

// Config holds configuration settings for the capture engine.
type Config struct {
	Interval time.Duration
	Format   string
}

// Engine manages the screen capture process.
type Engine struct {
	config Config
}

// New creates a new capture Engine with the given configuration.
func New(config Config) *Engine {
	return &Engine{config: config}
}

// CaptureFrame captures a single frame of the screen and returns it as a Frame struct.
func (e *Engine) CaptureFrame(frameID int64) (*Frame, error) {
	img, err := captureScreen()
	if err != nil {
		return nil, err
	}

	var buf bytes.Buffer
	if err := png.Encode(&buf, img); err != nil {
		return nil, err
	}

	bounds := img.Bounds()

	return &Frame{
		ID:        frameID,
		Timestamp: time.Now(),
		Data:      buf.Bytes(),
		Width:     bounds.Dx(),
		Height:    bounds.Dy(),
		Format:    "png",
		SizeBytes: int64(buf.Len()),
	}, nil
}
