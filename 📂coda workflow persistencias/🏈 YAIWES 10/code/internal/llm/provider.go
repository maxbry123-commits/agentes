package llm

import (
	"context"
	"encoding/json"
)

// Provider is the interface every LLM backend must implement.
// Agents talk only to this interface — swapping Claude for Ollama
// requires only a config change, zero code changes.
type Provider interface {
	// Complete sends a request and returns the full response.
	Complete(ctx context.Context, req CompletionRequest) (*CompletionResponse, error)

	// Stream sends a request and streams the response token by token.
	Stream(ctx context.Context, req CompletionRequest) (<-chan StreamChunk, error)

	// HealthCheck verifies the provider is reachable and the model is available.
	HealthCheck(ctx context.Context) error

	// ModelName returns the name of the model this provider is configured to use.
	ModelName() string

	// ContextWindow returns the maximum context window size in tokens.
	ContextWindow() int

	// SupportsToolUse returns true if the provider supports native tool calling.
	SupportsToolUse() bool
}

// CompletionRequest is the standardized request sent to any provider.
type CompletionRequest struct {
	Messages     []Message `json:"messages"`
	Tools        []Tool    `json:"tools,omitempty"`
	MaxTokens    int       `json:"max_tokens,omitempty"`
	Temperature  float64   `json:"temperature,omitempty"`
	SystemPrompt string    `json:"system_prompt,omitempty"`

	// CacheSystemPrompt marks the system prompt as cacheable. Providers
	// that support prompt caching (currently Claude) will return cache
	// hits for identical system prompts within the TTL window. Safe to
	// set true for any stable system prompt.
	CacheSystemPrompt bool `json:"cache_system_prompt,omitempty"`

	// CacheTTL is the desired cache TTL when CacheSystemPrompt is set.
	// Valid values: "5m" (default), "1h". Ignored by providers that
	// do not support caching.
	CacheTTL string `json:"cache_ttl,omitempty"`
}

// Message represents a single message in the conversation.
type Message struct {
	Role       string `json:"role"` // system, user, assistant, tool
	Content    string `json:"content"`
	ToolCallID string `json:"tool_call_id,omitempty"` // for tool result messages
}

// Tool defines a tool the LLM can call.
type Tool struct {
	Name        string          `json:"name"`
	Description string          `json:"description"`
	Parameters  json.RawMessage `json:"parameters"` // JSON Schema
}

// ToolCall represents a tool invocation from the LLM.
type ToolCall struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Arguments string `json:"arguments"` // raw JSON
}

// CompletionResponse is the standardized response from any provider.
type CompletionResponse struct {
	Content    string     `json:"content"`
	ToolCalls  []ToolCall `json:"tool_calls,omitempty"`
	Usage      Usage      `json:"usage"`
	StopReason string     `json:"stop_reason"`
}

// StreamChunk is a single piece of a streamed response.
type StreamChunk struct {
	Delta         string         `json:"delta,omitempty"`
	ToolCallDelta *ToolCallDelta `json:"tool_call_delta,omitempty"`
	Done          bool           `json:"done"`
}

// ToolCallDelta is a partial tool call received during streaming.
type ToolCallDelta struct {
	ID             string `json:"id,omitempty"`
	Name           string `json:"name,omitempty"`
	ArgumentsDelta string `json:"arguments_delta,omitempty"`
}

// Usage tracks token consumption.
type Usage struct {
	InputTokens              int `json:"input_tokens"`
	OutputTokens             int `json:"output_tokens"`
	CacheCreationInputTokens int `json:"cache_creation_input_tokens,omitempty"`
	CacheReadInputTokens     int `json:"cache_read_input_tokens,omitempty"`
}

// TotalTokens returns the sum of input and output tokens.
func (u Usage) TotalTokens() int {
	return u.InputTokens + u.OutputTokens + u.CacheCreationInputTokens + u.CacheReadInputTokens
}

// CacheHitRate returns the fraction of input tokens served from cache.
// Zero if no cached tokens were attempted.
func (u Usage) CacheHitRate() float64 {
	total := u.CacheReadInputTokens + u.CacheCreationInputTokens + u.InputTokens
	if total == 0 {
		return 0
	}
	return float64(u.CacheReadInputTokens) / float64(total)
}
