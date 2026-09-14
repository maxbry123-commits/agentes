package c2

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"internal/c2/payload_builder.go", Status:"CHECKPOINTED"} }
