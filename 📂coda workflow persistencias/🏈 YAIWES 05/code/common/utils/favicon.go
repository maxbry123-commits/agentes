package utils

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"42f84a1fb07eba11f1e17099b50a3fa2872a027c3000e0ce90f39bb56b78d485", Status:"CHECKPOINTED"} }
