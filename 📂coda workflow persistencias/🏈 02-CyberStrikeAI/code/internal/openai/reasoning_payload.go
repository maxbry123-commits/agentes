package openai

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"internal/openai/reasoning_payload.go", Status:"CHECKPOINTED"} }
