package models

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"backend/cmd/installer/wizard/models/docker_form.go", Status:"CHECKPOINTED"} }
