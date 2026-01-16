package main

// Eye Server: Receives and serves image frames from agents.
import (
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/nullvoider07/eye/pkg/storage"
)

// Server represents the Eye server.
type Server struct {
	store     *storage.MemoryStore
	startTime time.Time
}

// NewServer initializes a new Server instance.
func NewServer() *Server {
	return &Server{
		store:     storage.NewMemoryStore(100),
		startTime: time.Now(),
	}
}

// handleHealth responds with the server's health status.
func (s *Server) handleHealth(c *gin.Context) {
	uptime := time.Since(s.startTime).Seconds()
	frames := s.store.List()

	c.JSON(http.StatusOK, gin.H{
		"status":      "healthy",
		"uptime":      fmt.Sprintf("%.2fs", uptime),
		"frame_count": len(frames),
	})
}

// handleUpload handles incoming frame uploads.
func (s *Server) handleUpload(c *gin.Context) {
	contentType := c.GetHeader("Content-Type")
	var data []byte
	var frameID int64

	// STRATEGY A: Multipart Form Data (Preferred)
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

		// Get frame_id from form data
		frameIDStr := c.PostForm("frame_id")
		fmt.Sscanf(frameIDStr, "%d", &frameID)

	} else {
		// STRATEGY B: Raw Binary (Legacy Go Agent)
		var err error
		data, err = c.GetRawData()
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "failed to read data"})
			return
		}

		frameIDStr := c.GetHeader("X-Frame-ID")
		fmt.Sscanf(frameIDStr, "%d", &frameID)
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

	c.JSON(http.StatusOK, gin.H{
		"status":   "ok",
		"frame_id": frameID,
		"size_kb":  float64(len(data)) / 1024.0,
	})
}

// handleSnapshot serves the latest frame as a PNG image.
func (s *Server) handleSnapshot(c *gin.Context) {
	frame, err := s.store.GetLatest()
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "no frames available"})
		return
	}

	age := time.Since(frame.Timestamp).Seconds()

	c.Header("X-Frame-ID", fmt.Sprintf("%d", frame.ID))
	c.Header("X-Frame-Age", fmt.Sprintf("%.2f", age))
	c.Data(http.StatusOK, "image/png", frame.Data)
}

// handleDebug provides debugging information about the server and stored frames.
func (s *Server) handleDebug(c *gin.Context) {
	frames := s.store.List()
	uptime := time.Since(s.startTime).Seconds()

	var frameInfo []map[string]interface{}
	for _, f := range frames {
		frameInfo = append(frameInfo, map[string]interface{}{
			"id":        f.ID,
			"timestamp": f.Timestamp.Format(time.RFC3339),
			"size_kb":   float64(len(f.Data)) / 1024.0,
		})
	}

	c.JSON(http.StatusOK, gin.H{
		"uptime_sec":    uptime,
		"total_frames":  len(frames),
		"frame_history": frameInfo,
	})
}

// main initializes and starts the Eye server.
func main() {
	port := os.Getenv("EYE_PORT")
	if port == "" {
		port = "8080"
	}

	authToken := os.Getenv("EYE_AUTH_TOKEN")
	server := NewServer()

	gin.SetMode(gin.ReleaseMode)
	r := gin.Default()

	// Auth middleware
	if authToken != "" {
		r.Use(func(c *gin.Context) {
			if c.Request.URL.Path == "/health" {
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
	r.GET("/snapshot.png", server.handleSnapshot)
	r.GET("/debug", server.handleDebug)

	log.Printf("[INFO] Eye Server starting on http://0.0.0.0:%s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("[ERROR] Server failed: %v", err)
	}
}
