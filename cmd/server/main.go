package main

// Eye Server: Receives frames and commands agents.
import (
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/nullvoider07/eye/pkg/storage"
)

// --- CONFIGURATION MANAGEMENT ---

// AgentConfig defines the settings sent to agents.
type AgentConfig struct {
	Interval float64 `json:"interval"`
	Format   string  `json:"format"`
	Quality  int     `json:"quality"`
}

// Global thread-safe config store
var (
	currentConfig = AgentConfig{
		Interval: 1.5,
		Format:   "png",
		Quality:  95,
	}
	configMutex sync.RWMutex
)

// --- SERVER STRUCTS ---
type Server struct {
	store     *storage.MemoryStore
	startTime time.Time
}

func NewServer() *Server {
	return &Server{
		store:     storage.NewMemoryStore(100),
		startTime: time.Now(),
	}
}

// --- HANDLERS ---
func (s *Server) handleHealth(c *gin.Context) {
	uptime := time.Since(s.startTime).Seconds()
	frames := s.store.List()
	c.JSON(http.StatusOK, gin.H{
		"status":      "healthy",
		"uptime":      fmt.Sprintf("%.2fs", uptime),
		"frame_count": len(frames),
	})
}

// handleAdminConfig updates the global settings for ALL agents.
func handleAdminConfig(c *gin.Context) {
	var newConfig AgentConfig
	if err := c.ShouldBindJSON(&newConfig); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid config JSON"})
		return
	}

	// Validate inputs
	if newConfig.Interval < 0.1 {
		newConfig.Interval = 0.1
	}
	if newConfig.Quality < 1 || newConfig.Quality > 100 {
		newConfig.Quality = 75
	}
	newConfig.Format = strings.ToLower(newConfig.Format)
	if newConfig.Format != "png" && newConfig.Format != "jpeg" {
		newConfig.Format = "png"
	}

	// Update Global Config safely
	configMutex.Lock()
	currentConfig = newConfig
	configMutex.Unlock()

	log.Printf("[ADMIN] Config updated: %+v", currentConfig)
	c.JSON(http.StatusOK, gin.H{"message": "Configuration updated", "config": currentConfig})
}

func (s *Server) handleUpload(c *gin.Context) {
	contentType := c.GetHeader("Content-Type")
	var data []byte
	var frameID int64

	// Read File (Multipart) or Raw
	if strings.HasPrefix(contentType, "multipart/form-data") {
		file, _, err := c.Request.FormFile("image")
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "no image file"})
			return
		}
		defer file.Close()
		data, err = io.ReadAll(file)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "failed to read file"})
			return
		}
		fmt.Sscanf(c.PostForm("frame_id"), "%d", &frameID)
	} else {
		var err error
		data, err = c.GetRawData()
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "failed to read data"})
			return
		}
		fmt.Sscanf(c.GetHeader("X-Frame-ID"), "%d", &frameID)
	}

	// Store frame
	frame := &storage.Frame{
		ID:        frameID,
		Data:      data,
		Timestamp: time.Now(),
		Metadata:  map[string]string{"content-type": contentType},
	}

	if err := s.store.Store(frame); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	log.Printf("[INFO] Frame #%d stored (%d bytes)", frameID, len(data))

	// --- C2 PIGGYBACK ---
	// Attach the current config to the response
	configMutex.RLock()
	responseConfig := currentConfig
	configMutex.RUnlock()

	c.JSON(http.StatusOK, gin.H{
		"status":   "ok",
		"frame_id": frameID,
		"size_kb":  float64(len(data)) / 1024.0,
		"config":   responseConfig,
	})
}

func (s *Server) handleSnapshot(c *gin.Context) {
	frame, err := s.store.GetLatest()
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "no frames available"})
		return
	}
	c.Header("X-Frame-ID", fmt.Sprintf("%d", frame.ID))
	c.Data(http.StatusOK, "image/png", frame.Data)
}

func (s *Server) handleDebug(c *gin.Context) {
	configMutex.RLock()
	cfg := currentConfig
	configMutex.RUnlock()

	c.JSON(http.StatusOK, gin.H{
		"uptime_sec":     time.Since(s.startTime).Seconds(),
		"total_frames":   len(s.store.List()),
		"current_config": cfg,
	})
}

func main() {
	// 1. CLI Flags (For Version Check)
	versionFlag := flag.Bool("version", false, "Print version and exit")
	flag.Parse()

	if *versionFlag {
		fmt.Println("Eye Server v0.1.0")
		os.Exit(0)
	}

	// 2. Server Setup
	port := os.Getenv("EYE_PORT")
	if port == "" {
		port = "8080"
	}
	authToken := os.Getenv("EYE_AUTH_TOKEN")
	server := NewServer()

	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	// Auth Middleware
	if authToken != "" {
		r.Use(func(c *gin.Context) {
			if c.Request.URL.Path == "/health" || c.Request.URL.Path == "/snapshot.png" {
				c.Next()
				return
			}
			token := c.GetHeader("Authorization")
			if token != "Bearer "+authToken {
				c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
				c.Abort()
				return
			}
			c.Next()
		})
	}

	// Routes
	r.GET("/health", server.handleHealth)
	r.POST("/upload", server.handleUpload)
	r.POST("/admin/config", handleAdminConfig)
	r.GET("/snapshot.png", server.handleSnapshot)
	r.GET("/debug", server.handleDebug)

	log.Printf("[INFO] Eye Server starting on 0.0.0.0:%s", port)
	r.Run(":" + port)
}
