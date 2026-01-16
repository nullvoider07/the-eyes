package storage

// manager.go implements a Storage Manager that combines MemoryStore and DiskStore based on configuration.
type StorageMode string

// Storage modes
const (
	ModeMemory StorageMode = "memory"
	ModeDisk   StorageMode = "disk"
	ModeHybrid StorageMode = "hybrid"
)

// Manager manages storage of captured frames using MemoryStore and DiskStore.
type Manager struct {
	memory *MemoryStore
	disk   *DiskStore
	mode   StorageMode
}

// NewManager creates a new Manager with the specified storage mode, memory size, and disk path.
func NewManager(mode StorageMode, memorySize int, diskPath string) (*Manager, error) {
	m := &Manager{
		memory: NewMemoryStore(memorySize),
		mode:   mode,
	}

	if mode == ModeDisk || mode == ModeHybrid {
		disk, err := NewDiskStore(diskPath)
		if err != nil {
			return nil, err
		}
		m.disk = disk
	}

	return m, nil
}

// Store saves the given Frame using the configured storage mode(s).
func (m *Manager) Store(frame *Frame) error {
	if m.mode == ModeMemory || m.mode == ModeHybrid {
		if err := m.memory.Store(frame); err != nil {
			return err
		}
	}

	if m.mode == ModeDisk || m.mode == ModeHybrid {
		if err := m.disk.Store(frame); err != nil {
			return err
		}
	}

	return nil
}

// GetLatest retrieves the most recently stored Frame based on the storage mode.
func (m *Manager) GetLatest() (*Frame, error) {
	return m.memory.GetLatest()
}
