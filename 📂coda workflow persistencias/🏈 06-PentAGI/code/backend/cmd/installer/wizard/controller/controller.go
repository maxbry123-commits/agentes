package controller

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"backend/cmd/installer/wizard/controller/controller.go", Status:"CHECKPOINTED"} }
