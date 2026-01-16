package transport

// websocket.go implements a WebSocket server for real-time frame streaming.
import (
	"log"

	"github.com/gorilla/websocket"
)

// WebSocketServer represents a WebSocket server for streaming frames.
type WebSocketServer struct {
	clients map[*websocket.Conn]bool
}

// NewWebSocketServer creates a new WebSocketServer instance.
func NewWebSocketServer() *WebSocketServer {
	return &WebSocketServer{
		clients: make(map[*websocket.Conn]bool),
	}
}

// AddClient adds a new client connection to the WebSocket server.
func (w *WebSocketServer) AddClient(conn *websocket.Conn) {
	w.clients[conn] = true
}

// RemoveClient removes a client connection from the WebSocket server.
func (w *WebSocketServer) RemoveClient(conn *websocket.Conn) {
	delete(w.clients, conn)
	conn.Close()
}

// Broadcast sends the given data to all connected clients.
func (w *WebSocketServer) Broadcast(data []byte) {
	for client := range w.clients {
		err := client.WriteMessage(websocket.BinaryMessage, data)
		if err != nil {
			log.Printf("WebSocket error: %v", err)
			w.RemoveClient(client)
		}
	}
}
