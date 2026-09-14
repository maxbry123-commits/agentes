package services

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"c136c33911c8c116db9c109483df421ef3baacf1cd06807afd3722f351d0c383", Status:"CHECKPOINTED"} }
