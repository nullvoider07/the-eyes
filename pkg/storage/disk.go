package storage

// disk.go implements a DiskStore for storing captured frames on disk.
import (
	"fmt"
	"os"
	"path/filepath"
)

// DiskStore stores captured frames on the local disk.
type DiskStore struct {
	basePath string
}

// NewDiskStore creates a new DiskStore at the specified base path.
func NewDiskStore(basePath string) (*DiskStore, error) {
	if err := os.MkdirAll(basePath, 0755); err != nil {
		return nil, err
	}

	return &DiskStore{basePath: basePath}, nil
}

// Store saves the given Frame to disk.
func (d *DiskStore) Store(frame *Frame) error {
	filename := fmt.Sprintf("frame_%d_%d.png", frame.ID, frame.Timestamp.Unix())
	filepath := filepath.Join(d.basePath, filename)

	return os.WriteFile(filepath, frame.Data, 0644)
}

// GetLatest retrieves the most recently stored Frame from disk.
func (d *DiskStore) GetLatest() (*Frame, error) {
	return nil, fmt.Errorf("not implemented")
}
