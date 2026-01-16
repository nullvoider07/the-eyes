package auth

// OAuthProvider implements OAuth2 authentication.
import (
	"context"
	"crypto/rand"
	"encoding/base64"
	"fmt"
	"time"

	"golang.org/x/oauth2"
)

// OAuthConfig holds the configuration for OAuth2 providers.
type OAuthConfig struct {
	ClientID     string
	ClientSecret string
	RedirectURL  string
	AuthURL      string
	TokenURL     string
	Scopes       []string
}

// OAuthProvider struct manages OAuth2 authentication flow.
type OAuthProvider struct {
	config *oauth2.Config
	states map[string]time.Time
}

// NewOAuthProvider creates a new OAuthProvider with the given configuration.
func NewOAuthProvider(cfg OAuthConfig) *OAuthProvider {
	return &OAuthProvider{
		config: &oauth2.Config{
			ClientID:     cfg.ClientID,
			ClientSecret: cfg.ClientSecret,
			RedirectURL:  cfg.RedirectURL,
			Scopes:       cfg.Scopes,
			Endpoint: oauth2.Endpoint{
				AuthURL:  cfg.AuthURL,
				TokenURL: cfg.TokenURL,
			},
		},
		states: make(map[string]time.Time),
	}
}

// GetAuthURL generates the OAuth2 authorization URL and a state parameter.
func (o *OAuthProvider) GetAuthURL() (string, string, error) {
	state, err := generateState()
	if err != nil {
		return "", "", err
	}

	o.states[state] = time.Now()
	url := o.config.AuthCodeURL(state)

	return url, state, nil
}

// Exchange exchanges the authorization code for an access token.
func (o *OAuthProvider) Exchange(ctx context.Context, code string, state string) (*oauth2.Token, error) {
	if _, exists := o.states[state]; !exists {
		return nil, fmt.Errorf("invalid state")
	}
	delete(o.states, state)

	token, err := o.config.Exchange(ctx, code)
	if err != nil {
		return nil, err
	}

	return token, nil
}

// generateState creates a random state string for OAuth2 flow.
func generateState() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return base64.URLEncoding.EncodeToString(b), nil
}
