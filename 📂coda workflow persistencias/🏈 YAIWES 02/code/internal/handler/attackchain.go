package handler

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"2e136debf7f138f0d97449532c3f26b175d65dcd3d7b03f8c843fe294e250538", Status:"CHECKPOINTED"} }
