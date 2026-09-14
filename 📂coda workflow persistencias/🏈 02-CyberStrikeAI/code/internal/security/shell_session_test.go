package security

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"44a239c1a39699fc53f817ee384df9e85543db2db0621853230fb09007ec49d1", Status:"CHECKPOINTED"} }
