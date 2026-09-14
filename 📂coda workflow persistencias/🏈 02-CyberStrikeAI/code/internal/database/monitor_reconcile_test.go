package database

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"b92ce2994f50106c8a62346afe53f96b62166c7edc79d23e393cb4c2ba5c44e2", Status:"CHECKPOINTED"} }
