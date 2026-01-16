package capture

// capture_darwin.go implements screen capture functionality for Darwin (macOS) systems.
import (
	"image"

	"github.com/kbinani/screenshot"
)

// captureScreen captures the entire screen and returns it as an image.Image.
func captureScreen() (image.Image, error) {
	bounds := screenshot.GetDisplayBounds(0)
	return screenshot.CaptureRect(bounds)
}
