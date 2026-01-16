package transport

// protocol.go defines data structures for frame metadata and upload requests/responses.
import "time"

// FrameMetadata holds metadata information about a captured frame.
type FrameMetadata struct {
	FrameID   int64
	Timestamp time.Time
	SizeBytes int64
	Format    string
}

// UploadRequest represents a request to upload a captured frame.
type UploadRequest struct {
	Metadata FrameMetadata
	Data     []byte
}

// UploadResponse represents a response from the server after uploading a frame.
type UploadResponse struct {
	Success bool
	Message string
	FrameID int64
}
