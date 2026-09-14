package checker

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"backend/cmd/installer/checker/helpers.go", Status:"CHECKPOINTED"} }
