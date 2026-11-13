package llm

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

// LMStudioProvider implements Provider using LM Studio's OpenAI-compatible API.
type LMStudioProvider struct {
	endpoint      string
	model         string
	contextWindow int
	httpClient    *http.Client
}

// LMStudioProviderConfig holds configuration for creating an LMStudioProvider.
type LMStudioProviderConfig struct {
	Endpoint      string
	Model         string
	ContextWindow int
}

// NewLMStudioProvider creates a new LM Studio provider.
func NewLMStudioProvider(cfg LMStudioProviderConfig) *LMStudioProvider {
	if cfg.Endpoint == "" {
		cfg.Endpoint = "http://localhost:1234"
	}
	if cfg.ContextWindow <= 0 {
		cfg.ContextWindow = 32000
	}

	return &LMStudioProvider{
		endpoint:      cfg.Endpoint,
		model:         cfg.Model,
		contextWindow: cfg.ContextWindow,
		httpClient: &http.Client{
			Timeout: 10 * time.Minute,
		},
	}
}

// OpenAI-compatible request/response types

type openAIChatRequest struct {
	Model       string              `json:"model"`
	Messages    []openAIChatMessage `json:"messages"`
	MaxTokens   int                 `json:"max_tokens,omitempty"`
	Temperature float64             `json:"temperature,omitempty"`
	Stream      bool                `json:"stream"`
}

type openAIChatMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type openAIChatResponse struct {
	Choices []openAIChatChoice `json:"choices"`
	Usage   openAIUsage        `json:"usage"`
}

type openAIChatChoice struct {
	Message      openAIChatMessage `json:"message"`
	FinishReason string            `json:"finish_reason"`
}

type openAIUsage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
}

func (l *LMStudioProvider) Complete(ctx context.Context, req CompletionRequest) (*CompletionResponse, error) {
	var messages []openAIChatMessage

	if req.SystemPrompt != "" {
		messages = append(messages, openAIChatMessage{Role: "system", Content: req.SystemPrompt})
	}
	for _, msg := range req.Messages {
		messages = append(messages, openAIChatMessage{Role: msg.Role, Content: msg.Content})
	}

	maxTokens := req.MaxTokens
	if maxTokens <= 0 {
		maxTokens = 8192
	}

	body := openAIChatRequest{
		Model:       l.model,
		Messages:    messages,
		MaxTokens:   maxTokens,
		Temperature: req.Temperature,
		Stream:      false,
	}

	jsonBody, err := json.Marshal(body)
	if err != nil {
		return nil, fmt.Errorf("marshaling lmstudio request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, "POST", l.endpoint+"/v1/chat/completions", bytes.NewReader(jsonBody))
	if err != nil {
		return nil, fmt.Errorf("creating lmstudio request: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := l.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("lmstudio request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("lmstudio returned status %d: %s", resp.StatusCode, string(respBody))
	}

	var oaiResp openAIChatResponse
	if err := json.NewDecoder(resp.Body).Decode(&oaiResp); err != nil {
		return nil, fmt.Errorf("decoding lmstudio response: %w", err)
	}

	result := &CompletionResponse{
		Usage: Usage{
			InputTokens:  oaiResp.Usage.PromptTokens,
			OutputTokens: oaiResp.Usage.CompletionTokens,
		},
	}

	if len(oaiResp.Choices) > 0 {
		result.Content = oaiResp.Choices[0].Message.Content
		result.StopReason = oaiResp.Choices[0].FinishReason
	}

	return result, nil
}

func (l *LMStudioProvider) Stream(ctx context.Context, req CompletionRequest) (<-chan StreamChunk, error) {
	// LM Studio supports SSE streaming via OpenAI-compatible endpoint
	// For simplicity, fall back to non-streaming and emit as a single chunk
	resp, err := l.Complete(ctx, req)
	if err != nil {
		return nil, err
	}

	ch := make(chan StreamChunk, 2)
	go func() {
		defer close(ch)
		ch <- StreamChunk{Delta: resp.Content}
		ch <- StreamChunk{Done: true}
	}()

	return ch, nil
}

func (l *LMStudioProvider) HealthCheck(ctx context.Context) error {
	httpReq, err := http.NewRequestWithContext(ctx, "GET", l.endpoint+"/v1/models", nil)
	if err != nil {
		return fmt.Errorf("creating health check request: %w", err)
	}

	resp, err := l.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("LM Studio is not reachable at %s: %w", l.endpoint, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("LM Studio returned status %d — is the server running?", resp.StatusCode)
	}

	return nil
}

func (l *LMStudioProvider) ModelName() string     { return l.model }
func (l *LMStudioProvider) ContextWindow() int    { return l.contextWindow }
func (l *LMStudioProvider) SupportsToolUse() bool { return false }
