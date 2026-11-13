package tools

import (
	"context"
	"time"
)

// Tool is the interface every security tool wrapper must implement.
type Tool interface {
	// Name returns the tool's identifier.
	Name() string

	// Run executes the tool against a target with the given options.
	Run(ctx context.Context, target string, opts Options) (*ToolResult, error)

	// IsAvailable checks whether the tool's dependencies are satisfied.
	IsAvailable() bool
}

// ToolResult is the standardized output from any security tool.
type ToolResult struct {
	ToolName       string           `json:"tool_name"`
	Target         string           `json:"target"`
	RawOutput      string           `json:"raw_output"`
	ParsedFindings []map[string]any `json:"parsed_findings,omitempty"`
	Duration       time.Duration    `json:"duration"`
	Error          error            `json:"error,omitempty"`
}

// Options holds tool configuration as a string-keyed map with typed accessors.
type Options map[string]any

// GetString returns the string value for key, or defaultVal if not found.
func (o Options) GetString(key, defaultVal string) string {
	if v, ok := o[key]; ok {
		if s, ok := v.(string); ok {
			return s
		}
	}
	return defaultVal
}

// GetInt returns the int value for key, or defaultVal if not found.
func (o Options) GetInt(key string, defaultVal int) int {
	if v, ok := o[key]; ok {
		switch n := v.(type) {
		case int:
			return n
		case float64:
			return int(n)
		case int64:
			return int(n)
		}
	}
	return defaultVal
}

// GetBool returns the bool value for key, or defaultVal if not found.
func (o Options) GetBool(key string, defaultVal bool) bool {
	if v, ok := o[key]; ok {
		if b, ok := v.(bool); ok {
			return b
		}
	}
	return defaultVal
}

// GetStringSlice returns a string slice for key, or nil if not found.
func (o Options) GetStringSlice(key string) []string {
	if v, ok := o[key]; ok {
		if ss, ok := v.([]string); ok {
			return ss
		}
		// Handle []any from JSON unmarshaling
		if ai, ok := v.([]any); ok {
			result := make([]string, 0, len(ai))
			for _, item := range ai {
				if s, ok := item.(string); ok {
					result = append(result, s)
				}
			}
			return result
		}
	}
	return nil
}
