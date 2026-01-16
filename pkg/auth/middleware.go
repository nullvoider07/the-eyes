package auth

// TokenAuth provides a simple token-based authentication middleware for Gin framework.
import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
)

// TokenAuth struct holds the token for authentication.
type TokenAuth struct {
	token string
}

// NewTokenAuth creates a new TokenAuth middleware with the provided token.
func NewTokenAuth(token string) *TokenAuth {
	return &TokenAuth{token: token}
}

// Middleware returns a Gin middleware function that checks for the correct token in the Authorization header.
func (t *TokenAuth) Middleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Skip auth for health endpoint
		if c.Request.URL.Path == "/health" {
			c.Next()
			return
		}

		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "missing authorization"})
			c.Abort()
			return
		}

		token := strings.TrimPrefix(authHeader, "Bearer ")
		if token != t.token {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "invalid token"})
			c.Abort()
			return
		}

		c.Next()
	}
}
