// Package keychain stores secrets in the operating system's native secret
// store (macOS Keychain, linux-secret-service, Windows Credential Manager).
// Fall back to an encrypted file is intentionally NOT implemented — if the
// OS doesn't have a secret store, we prefer to fail loudly rather than pretend
// to store secrets securely.
package keychain

import (
	"errors"
	"fmt"

	"github.com/zalando/go-keyring"
)

// Service is the keychain service name everything under this package shares.
// Using one name means macOS Keychain Access groups all our entries together.
const Service = "pentestswarm"

// Common key names. Use these constants rather than magic strings so keys
// stay consistent between the 'init' writer and the scan-time reader.
const (
	KeyClaudeAPI      = "orchestrator.api_key"
	KeyHackerOneToken = "platform.hackerone.token"
	KeyBugcrowdToken  = "platform.bugcrowd.token"
	KeyIntigritiToken = "platform.intigriti.token"
)

// Set persists value under key. Overwrites any existing entry.
func Set(key, value string) error {
	return keyring.Set(Service, key, value)
}

// Get reads value for key. Returns ErrNotFound when no entry exists.
// Callers should treat ErrNotFound as "not configured" — never as a fatal error.
func Get(key string) (string, error) {
	v, err := keyring.Get(Service, key)
	if errors.Is(err, keyring.ErrNotFound) {
		return "", ErrNotFound
	}
	if err != nil {
		return "", fmt.Errorf("keychain read %q: %w", key, err)
	}
	return v, nil
}

// Delete removes a stored value. Idempotent — missing entries don't error.
func Delete(key string) error {
	err := keyring.Delete(Service, key)
	if errors.Is(err, keyring.ErrNotFound) {
		return nil
	}
	return err
}

// ErrNotFound is returned by Get when no entry exists.
var ErrNotFound = errors.New("keychain: entry not found")
