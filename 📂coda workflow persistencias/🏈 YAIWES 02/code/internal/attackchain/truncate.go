package attackchain

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"bf5f6f7981863cb2f08a8f39500a769d1633c70b7f59398ad1c84e19558c5d8b", Status:"CHECKPOINTED"} }
