package storage

// memory.go implements an in-memory storage for captured frames.
import (
	"fmt"
	"sync"
	"time"
)

// Frame represents a captured screen frame stored in memory.
type Frame struct {
	ID        int64
	Data      []byte
	Timestamp time.Time
	Metadata  map[string]string
}

// MemoryStore stores captured frames in memory.
type MemoryStore struct {
	mu        sync.RWMutex
	frames    []*Frame
	maxFrames int
	current   int
}

// NewMemoryStore creates a new MemoryStore with the specified maximum number of frames.
func NewMemoryStore(maxFrames int) *MemoryStore {
	return &MemoryStore{
		frames:    make([]*Frame, 0, maxFrames),
		maxFrames: maxFrames,
	}
}

// Store saves the given Frame in memory.
func (m *MemoryStore) Store(frame *Frame) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if len(m.frames) < m.maxFrames {
		m.frames = append(m.frames, frame)
	} else {
		m.frames[m.current] = frame
		m.current = (m.current + 1) % m.maxFrames
	}

	return nil
}

// GetLatest retrieves the most recently stored Frame from memory.
func (m *MemoryStore) GetLatest() (*Frame, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if len(m.frames) == 0 {
		return nil, fmt.Errorf("no frames available")
	}

	if len(m.frames) < m.maxFrames {
		return m.frames[len(m.frames)-1], nil
	}

	idx := (m.current - 1 + m.maxFrames) % m.maxFrames
	return m.frames[idx], nil
}

// List returns all stored Frames in memory.
func (m *MemoryStore) List() []*Frame {
	m.mu.RLock()
	defer m.mu.RUnlock()

	result := make([]*Frame, len(m.frames))
	copy(result, m.frames)
	return result
}
