package errors

import (
	"errors"
	"fmt"
)

// Sentinel errors
var (
	ErrScopeViolation    = errors.New("target is outside the defined scope")
	ErrAuthRequired      = errors.New("authorization token is required")
	ErrAgentFailed       = errors.New("agent execution failed")
	ErrToolNotFound      = errors.New("security tool not found or not available")
	ErrModelUnavailable  = errors.New("LLM model is not available")
	ErrCampaignAborted   = errors.New("campaign was aborted")
	ErrCampaignNotFound  = errors.New("campaign not found")
	ErrRateLimitExceeded = errors.New("rate limit exceeded")
	ErrInvalidTransition = errors.New("invalid campaign state transition")
	ErrParseFailure      = errors.New("failed to parse LLM response")
	ErrProviderError     = errors.New("LLM provider returned an error")
	ErrTimeout           = errors.New("operation timed out")
)

// ScopeViolationError provides details about what target was out of scope.
type ScopeViolationError struct {
	Target string
	Scope  string
	Detail string
}

func (e *ScopeViolationError) Error() string {
	return fmt.Sprintf("scope violation: target %q is not in scope %q — %s", e.Target, e.Scope, e.Detail)
}

func (e *ScopeViolationError) Unwrap() error {
	return ErrScopeViolation
}

// ToolError wraps an error with the tool that caused it.
type ToolError struct {
	Tool string
	Err  error
}

func (e *ToolError) Error() string {
	return fmt.Sprintf("tool %q failed: %s", e.Tool, e.Err)
}

func (e *ToolError) Unwrap() error {
	return e.Err
}

// WrapToolError creates a ToolError.
func WrapToolError(tool string, err error) error {
	return &ToolError{Tool: tool, Err: err}
}

// AgentError wraps an error with the agent that caused it.
type AgentError struct {
	Agent string
	Phase string
	Err   error
}

func (e *AgentError) Error() string {
	if e.Phase != "" {
		return fmt.Sprintf("agent %q failed during %s: %s", e.Agent, e.Phase, e.Err)
	}
	return fmt.Sprintf("agent %q failed: %s", e.Agent, e.Err)
}

func (e *AgentError) Unwrap() error {
	return e.Err
}

// WrapAgentError creates an AgentError.
func WrapAgentError(agent string, err error) error {
	return &AgentError{Agent: agent, Err: err}
}

// WrapAgentPhaseError creates an AgentError with phase context.
func WrapAgentPhaseError(agent, phase string, err error) error {
	return &AgentError{Agent: agent, Phase: phase, Err: err}
}

// Is checks if the error matches a target. Re-exported from stdlib for convenience.
func Is(err, target error) bool {
	return errors.Is(err, target)
}

// As finds the first error in err's chain that matches target. Re-exported for convenience.
func As(err error, target any) bool {
	return errors.As(err, target)
}
