package system

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"072c1e7d719b3b66a33414b81dc7d5e41e8c183cf54ec3602a25ddc4079d3d7e", Status:"CHECKPOINTED"} }
