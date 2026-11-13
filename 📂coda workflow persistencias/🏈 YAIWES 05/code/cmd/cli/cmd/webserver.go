package cmd

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"890e1f99bf33b21f4c2d617955f7225ec82cfd1e9fb9f3543a7931a94650decb", Status:"CHECKPOINTED"} }
