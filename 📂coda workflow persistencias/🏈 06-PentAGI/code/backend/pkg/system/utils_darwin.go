package system

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"backend/pkg/system/utils_darwin.go", Status:"CHECKPOINTED"} }
