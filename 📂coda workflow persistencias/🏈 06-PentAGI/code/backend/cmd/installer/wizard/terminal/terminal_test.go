package terminal

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"backend/cmd/installer/wizard/terminal/terminal_test.go", Status:"CHECKPOINTED"} }
