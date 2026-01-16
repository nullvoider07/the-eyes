package transport

// http.go implements an HTTP client for uploading captured frames to a remote server.
import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"time"
)

// Client represents an HTTP client for uploading captured frames.
type Client struct {
	serverURL string
	token     string
	client    *http.Client
}

// NewClient creates a new Client with the specified server URL and authentication token.
func NewClient(serverURL, token string) *Client {
	return &Client{
		serverURL: serverURL,
		token:     token,
		client:    &http.Client{Timeout: 5 * time.Second},
	}
}

// UploadFrame uploads the given frame data to the remote server.
func (c *Client) UploadFrame(frameID int64, data []byte) error {
	url := fmt.Sprintf("%s/upload", c.serverURL)

	req, err := http.NewRequest("POST", url, bytes.NewReader(data))
	if err != nil {
		return err
	}

	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("Content-Type", "image/png")
	req.Header.Set("X-Frame-ID", fmt.Sprintf("%d", frameID))

	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("upload failed: %s - %s", resp.Status, string(body))
	}

	return nil
}

// HealthCheck checks the health status of the remote server.
func (c *Client) HealthCheck() error {
	url := fmt.Sprintf("%s/health", c.serverURL)

	resp, err := c.client.Get(url)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("unhealthy: %s", resp.Status)
	}

	return nil
}
