package models

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"1c17534506618e367e1ccc5982c4c0ae8683d91f111bd178a49726bf3c83720d", Status:"CHECKPOINTED"} }
