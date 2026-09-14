package services

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"backend/pkg/server/services/graphql.go", Status:"CHECKPOINTED"} }
