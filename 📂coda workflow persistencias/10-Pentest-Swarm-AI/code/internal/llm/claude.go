package llm

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"math/rand"
	"strings"
	"time"

	"github.com/anthropics/anthropic-sdk-go"
	"github.com/anthropics/anthropic-sdk-go/option"
)

// ClaudeProvider implements Provider using the Anthropic SDK.
type ClaudeProvider struct {
	client        anthropic.Client
	model         string
	contextWindow int
	maxRetries    int
}

// ClaudeProviderConfig holds configuration for creating a ClaudeProvider.
type ClaudeProviderConfig struct {
	APIKey        string
	Model         string
	ContextWindow int
	MaxRetries    int
}

// NewClaudeProvider creates a new Claude provider.
func NewClaudeProvider(cfg ClaudeProviderConfig) *ClaudeProvider {
	if cfg.MaxRetries <= 0 {
		cfg.MaxRetries = 3
	}
	if cfg.ContextWindow <= 0 {
		cfg.ContextWindow = 200000
	}
	if cfg.Model == "" {
		cfg.Model = "claude-sonnet-4-6"
	}

	client := anthropic.NewClient(option.WithAPIKey(cfg.APIKey))

	return &ClaudeProvider{
		client:        client,
		model:         cfg.Model,
		contextWindow: cfg.ContextWindow,
		maxRetries:    cfg.MaxRetries,
	}
}

func (c *ClaudeProvider) Complete(ctx context.Context, req CompletionRequest) (*CompletionResponse, error) {
	params := c.buildParams(req)

	var resp *anthropic.Message
	var err error

	for attempt := 0; attempt <= c.maxRetries; attempt++ {
		resp, err = c.client.Messages.New(ctx, params)
		if err == nil {
			break
		}

		// Retry on rate limit (429) and overloaded (529)
		if !isRetryableError(err) || attempt == c.maxRetries {
			return nil, fmt.Errorf("claude completion failed: %w", err)
		}

		backoff := time.Duration(math.Pow(2, float64(attempt))) * time.Second
		jitter := time.Duration(rand.Int63n(int64(time.Second)))
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		case <-time.After(backoff + jitter):
		}
	}

	return c.parseResponse(resp), nil
}

func (c *ClaudeProvider) Stream(ctx context.Context, req CompletionRequest) (<-chan StreamChunk, error) {
	params := c.buildParams(req)
	ch := make(chan StreamChunk, 100)

	stream := c.client.Messages.NewStreaming(ctx, params)

	go func() {
		defer close(ch)

		for stream.Next() {
			event := stream.Current()

			switch evt := event.AsAny().(type) {
			case anthropic.ContentBlockDeltaEvent:
				switch delta := evt.Delta.AsAny().(type) {
				case anthropic.TextDelta:
					ch <- StreamChunk{Delta: delta.Text}
				case anthropic.InputJSONDelta:
					ch <- StreamChunk{
						ToolCallDelta: &ToolCallDelta{
							ArgumentsDelta: delta.PartialJSON,
						},
					}
				}
			case anthropic.ContentBlockStartEvent:
				if block, ok := evt.ContentBlock.AsAny().(anthropic.ToolUseBlock); ok {
					ch <- StreamChunk{
						ToolCallDelta: &ToolCallDelta{
							ID:   block.ID,
							Name: block.Name,
						},
					}
				}
			case anthropic.MessageStopEvent:
				ch <- StreamChunk{Done: true}
			}
		}

		if err := stream.Err(); err != nil {
			ch <- StreamChunk{Done: true}
		}
	}()

	return ch, nil
}

func (c *ClaudeProvider) HealthCheck(ctx context.Context) error {
	_, err := c.client.Messages.New(ctx, anthropic.MessageNewParams{
		Model:     anthropic.Model(c.model),
		MaxTokens: 10,
		Messages: []anthropic.MessageParam{
			anthropic.NewUserMessage(anthropic.NewTextBlock("ping")),
		},
	})
	if err != nil {
		return fmt.Errorf("claude health check failed: %w", err)
	}
	return nil
}

func (c *ClaudeProvider) ModelName() string {
	return c.model
}

func (c *ClaudeProvider) ContextWindow() int {
	return c.contextWindow
}

func (c *ClaudeProvider) SupportsToolUse() bool {
	return true
}

func (c *ClaudeProvider) buildParams(req CompletionRequest) anthropic.MessageNewParams {
	maxTokens := req.MaxTokens
	if maxTokens <= 0 {
		maxTokens = 8192
	}

	// Convert messages
	var messages []anthropic.MessageParam
	for _, msg := range req.Messages {
		switch msg.Role {
		case "user":
			messages = append(messages, anthropic.NewUserMessage(anthropic.NewTextBlock(msg.Content)))
		case "assistant":
			messages = append(messages, anthropic.NewAssistantMessage(anthropic.NewTextBlock(msg.Content)))
		case "tool":
			messages = append(messages, anthropic.NewUserMessage(
				anthropic.NewToolResultBlock(msg.ToolCallID, msg.Content, false),
			))
		}
	}

	params := anthropic.MessageNewParams{
		Model:     anthropic.Model(c.model),
		MaxTokens: int64(maxTokens),
		Messages:  messages,
	}

	if req.SystemPrompt != "" {
		block := anthropic.TextBlockParam{Text: req.SystemPrompt}
		if req.CacheSystemPrompt {
			ttl := req.CacheTTL
			if ttl == "" {
				ttl = "5m"
			}
			block.CacheControl = anthropic.CacheControlEphemeralParam{TTL: anthropic.CacheControlEphemeralTTL(ttl)}
		}
		params.System = []anthropic.TextBlockParam{block}
	}

	if req.Temperature > 0 {
		params.Temperature = anthropic.Float(req.Temperature)
	}

	// Convert tools
	if len(req.Tools) > 0 {
		var tools []anthropic.ToolUnionParam
		for _, t := range req.Tools {
			var props map[string]any
			_ = json.Unmarshal(t.Parameters, &props)

			tools = append(tools, anthropic.ToolUnionParam{
				OfTool: &anthropic.ToolParam{
					Name:        t.Name,
					Description: anthropic.String(t.Description),
					InputSchema: anthropic.ToolInputSchemaParam{
						Properties: props,
					},
				},
			})
		}
		params.Tools = tools
	}

	return params
}

func (c *ClaudeProvider) parseResponse(resp *anthropic.Message) *CompletionResponse {
	result := &CompletionResponse{
		Usage: Usage{
			InputTokens:              int(resp.Usage.InputTokens),
			OutputTokens:             int(resp.Usage.OutputTokens),
			CacheCreationInputTokens: int(resp.Usage.CacheCreationInputTokens),
			CacheReadInputTokens:     int(resp.Usage.CacheReadInputTokens),
		},
		StopReason: string(resp.StopReason),
	}

	for _, block := range resp.Content {
		switch v := block.AsAny().(type) {
		case anthropic.TextBlock:
			result.Content += v.Text
		case anthropic.ToolUseBlock:
			argsJSON, _ := json.Marshal(v.Input)
			result.ToolCalls = append(result.ToolCalls, ToolCall{
				ID:        v.ID,
				Name:      v.Name,
				Arguments: string(argsJSON),
			})
		}
	}

	return result
}

// isRetryableError checks if an API error is retryable (429 or 529).
func isRetryableError(err error) bool {
	errStr := err.Error()
	return strings.Contains(errStr, "429") || strings.Contains(errStr, "529") || strings.Contains(errStr, "overloaded")
}
