package ui

import (
	"strings"
	"testing"
)

var testProviders = []string{"together", "claude", "openai", "gemini", "ollama", "lmstudio", "orcarouter"}

// A key-based provider with no key configured must expose a focusable API-key
// field, and navigation from the provider row must land on it.
func TestKeyFieldShownWhenProviderNeedsKey(t *testing.T) {
	m := newLaunchModel(testProviders, LaunchConfig{Provider: "together", KeyConfigured: false})
	if !m.keyFieldActive() {
		t.Fatal("together + no key: expected key field active")
	}
	view := stripANSI(m.View())
	if !strings.Contains(view, "API key") {
		t.Fatalf("together + no key: expected an 'API key' row, got:\n%s", view)
	}
	m.focus = fProvider
	m.move(1)
	if m.focus != fAPIKey {
		t.Fatalf("expected focus to land on fAPIKey, got %d", m.focus)
	}
}

// A local provider needs no key: the field is hidden and navigation skips it.
func TestKeyFieldHiddenForLocalProvider(t *testing.T) {
	m := newLaunchModel(testProviders, LaunchConfig{Provider: "ollama", KeyConfigured: false})
	if m.keyFieldActive() {
		t.Fatal("ollama: expected key field inactive")
	}
	m.focus = fProvider
	m.move(1)
	if m.focus != fSwarm {
		t.Fatalf("ollama: expected navigation to skip fAPIKey and land on fSwarm, got %d", m.focus)
	}
}

// When a key is already configured, a key-based provider must not prompt.
func TestKeyFieldHiddenWhenConfigured(t *testing.T) {
	m := newLaunchModel(testProviders, LaunchConfig{Provider: "claude", KeyConfigured: true})
	if m.keyFieldActive() {
		t.Fatal("claude + configured key: expected key field inactive")
	}
}

// RunLauncher only returns a pasted key for key-based providers.
func TestResultKeyOnlyForKeyProviders(t *testing.T) {
	if !providerNeedsKeyUI("together") {
		t.Fatal("together should need a key")
	}
	if providerNeedsKeyUI("ollama") {
		t.Fatal("ollama should not need a key")
	}
}

func stripANSI(s string) string {
	var b strings.Builder
	inEsc := false
	for _, r := range s {
		switch {
		case r == 0x1b:
			inEsc = true
		case inEsc && (r == 'm'):
			inEsc = false
		case inEsc:
			// swallow escape body
		default:
			b.WriteRune(r)
		}
	}
	return b.String()
}
