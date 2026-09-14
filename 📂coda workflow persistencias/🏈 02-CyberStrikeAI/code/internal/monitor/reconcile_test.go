package monitor

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"2f5f8987c4a2fdbf902e5aba0f533cd7dbb555265f2ef70073d2d6aa85610b95", Status:"CHECKPOINTED"} }
