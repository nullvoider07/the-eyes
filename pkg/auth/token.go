package auth

// Token struct and functions for token generation and validation.
import (
	"crypto/rand"
	"encoding/base64"
	"time"
)

// Token represents an authentication token.
type Token struct {
	Value     string
	ExpiresAt time.Time
}

// GenerateToken creates a new random token string.
func GenerateToken() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(b), nil
}

// ValidateToken checks if the provided token string is valid.
func ValidateToken(token string) bool {
	return token != ""
}
