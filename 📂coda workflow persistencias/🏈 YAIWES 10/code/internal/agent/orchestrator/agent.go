package orchestrator

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/llm"
	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
)

// OrchestratorAgent coordinates all specialist agents using a ReAct loop.
type OrchestratorAgent struct {
	provider      llm.Provider
	budgetManager *llm.BudgetManager
	tools         map[string]OrchestratorTool
	maxIterations int
	eventSink     func(pipeline.CampaignEvent)
}

// OrchestratorTool is a function the orchestrator can call.
type OrchestratorTool struct {
	Name        string
	Description string
	Parameters  json.RawMessage
	Execute     func(ctx context.Context, args string) (string, error)
}

// OrchestratorConfig configures the orchestrator.
type OrchestratorConfig struct {
	Provider      llm.Provider
	MaxIterations int
	EventSink     func(pipeline.CampaignEvent) // callback for real-time event streaming
}

// NewOrchestratorAgent creates a new orchestrator.
func NewOrchestratorAgent(cfg OrchestratorConfig) *OrchestratorAgent {
	maxIter := cfg.MaxIterations
	if maxIter <= 0 {
		maxIter = 50
	}

	return &OrchestratorAgent{
		provider:      cfg.Provider,
		budgetManager: llm.NewBudgetManager(cfg.Provider.ContextWindow()),
		tools:         make(map[string]OrchestratorTool),
		maxIterations: maxIter,
		eventSink:     cfg.EventSink,
	}
}

// RegisterTool adds a tool the orchestrator can call.
func (o *OrchestratorAgent) RegisterTool(tool OrchestratorTool) {
	o.tools[tool.Name] = tool
}

// Run starts the ReAct loop for a campaign.
func (o *OrchestratorAgent) Run(ctx context.Context, campaign pipeline.Campaign) error {
	messages := []llm.Message{
		{
			Role: "user",
			Content: fmt.Sprintf(
				"Campaign started.\nTarget: %s\nObjective: %s\nMode: %s\n\nBegin the penetration test. Start with reconnaissance.",
				campaign.Target, campaign.Objective, campaign.Mode,
			),
		},
	}

	// Build tool definitions for the LLM
	var llmTools []llm.Tool
	for _, t := range o.tools {
		llmTools = append(llmTools, llm.Tool{
			Name:        t.Name,
			Description: t.Description,
			Parameters:  t.Parameters,
		})
	}

	for iteration := 0; iteration < o.maxIterations; iteration++ {
		// Check context cancellation (emergency stop)
		select {
		case <-ctx.Done():
			o.emitEvent(campaign, pipeline.EventStateChange, "orchestrator", "Campaign aborted", nil)
			return ctx.Err()
		default:
		}

		// Manage token budget
		if o.budgetManager.NeedsSummarization(messages) {
			summarized, err := o.budgetManager.Summarize(ctx, messages, o.provider)
			if err == nil {
				messages = summarized
			}
		}

		// Send to LLM
		req := llm.CompletionRequest{
			SystemPrompt: orchestratorSystemPrompt,
			Messages:     messages,
			Tools:        llmTools,
			MaxTokens:    4096,
			Temperature:  0.1,
		}

		resp, err := o.provider.Complete(ctx, req)
		if err != nil {
			o.emitEvent(campaign, pipeline.EventError, "orchestrator", "LLM call failed: "+err.Error(), nil)
			return fmt.Errorf("orchestrator LLM call failed: %w", err)
		}

		// Process reasoning text
		if resp.Content != "" {
			o.emitEvent(campaign, pipeline.EventThought, "orchestrator", resp.Content, nil)
			messages = append(messages, llm.Message{Role: "assistant", Content: resp.Content})
		}

		// Check for campaign completion
		if resp.StopReason == "end_turn" && len(resp.ToolCalls) == 0 {
			// LLM chose to stop — check if it signaled completion
			if isCompletionSignal(resp.Content) {
				o.emitEvent(campaign, pipeline.EventMilestone, "orchestrator", "Campaign complete", nil)
				return nil
			}
		}

		// Process tool calls
		if len(resp.ToolCalls) == 0 {
			// No tool call and no completion — ask LLM to take action
			messages = append(messages, llm.Message{
				Role:    "user",
				Content: "What's the next step? Use one of the available tools to continue the campaign.",
			})
			continue
		}

		for _, tc := range resp.ToolCalls {
			o.emitEvent(campaign, pipeline.EventToolCall, "orchestrator",
				fmt.Sprintf("Calling %s", tc.Name), json.RawMessage(tc.Arguments))

			tool, ok := o.tools[tc.Name]
			if !ok {
				toolResult := fmt.Sprintf("Tool %q not found. Available tools: %v", tc.Name, o.toolNames())
				messages = append(messages, llm.Message{
					Role:       "tool",
					Content:    toolResult,
					ToolCallID: tc.ID,
				})
				continue
			}

			// Execute the tool
			result, err := tool.Execute(ctx, tc.Arguments)
			if err != nil {
				result = fmt.Sprintf("Tool %s failed: %s", tc.Name, err)
				o.emitEvent(campaign, pipeline.EventError, tc.Name, result, nil)
			} else {
				o.emitEvent(campaign, pipeline.EventToolResult, tc.Name, truncate(result, 500), nil)
			}

			messages = append(messages, llm.Message{
				Role:       "tool",
				Content:    result,
				ToolCallID: tc.ID,
			})
		}
	}

	o.emitEvent(campaign, pipeline.EventMilestone, "orchestrator", "Max iterations reached", nil)
	return fmt.Errorf("orchestrator reached max iterations (%d)", o.maxIterations)
}

func (o *OrchestratorAgent) emitEvent(campaign pipeline.Campaign, eventType pipeline.EventType, agent, detail string, data json.RawMessage) {
	if o.eventSink == nil {
		return
	}

	o.eventSink(pipeline.CampaignEvent{
		CampaignID: campaign.ID,
		Timestamp:  time.Now(),
		EventType:  eventType,
		AgentName:  agent,
		Detail:     detail,
		Data:       data,
	})
}

func (o *OrchestratorAgent) toolNames() []string {
	var names []string
	for name := range o.tools {
		names = append(names, name)
	}
	return names
}

func isCompletionSignal(content string) bool {
	for _, signal := range []string{"campaign complete", "objective reached", "all paths exhausted", "report generated"} {
		if containsIgnoreCase(content, signal) {
			return true
		}
	}
	return false
}

func containsIgnoreCase(s, substr string) bool {
	s = toLower(s)
	substr = toLower(substr)
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

func toLower(s string) string {
	b := make([]byte, len(s))
	for i := 0; i < len(s); i++ {
		if s[i] >= 'A' && s[i] <= 'Z' {
			b[i] = s[i] + 32
		} else {
			b[i] = s[i]
		}
	}
	return string(b)
}

func truncate(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return s[:max] + "..."
}

const orchestratorSystemPrompt = `You are the orchestrator of an autonomous penetration testing platform. You coordinate four specialist agents:

1. **Recon Agent**: Discovers subdomains, ports, services, endpoints, and technologies
2. **Classifier Agent**: Maps findings to CVEs, scores CVSS, filters false positives
3. **Exploit Agent**: Constructs and executes multi-step attack chains
4. **Report Agent**: Generates professional pentest reports

Your job is to:
- Plan the campaign strategy based on the target and objective
- Decide which agent to invoke and when
- Adapt the strategy based on results
- Know when to stop (objective reached, all paths exhausted, or diminishing returns)

Use the available tools to coordinate the agents. Think step by step about what to do next.

When the campaign objective is achieved or all attack paths are exhausted, declare "Campaign complete" and invoke the report generator.

IMPORTANT: Never target anything outside the defined scope. If you're unsure, ask.`
