package llm

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"internal/llm/deepseek_anthropic_compat.go", Status:"CHECKPOINTED"} }
