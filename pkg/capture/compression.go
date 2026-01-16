package capture

// compression.go provides functions for compressing captured images.
import (
	"bytes"
	"image"
	"image/png"
)

// CompressPNG compresses the given image.Image into PNG format with best compression.
func CompressPNG(img image.Image) ([]byte, error) {
	var buf bytes.Buffer

	encoder := png.Encoder{
		CompressionLevel: png.BestCompression,
	}

	if err := encoder.Encode(&buf, img); err != nil {
		return nil, err
	}

	return buf.Bytes(), nil
}
