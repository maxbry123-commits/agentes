package security

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"3fde0e5f3e85c6352c36faa7278a774259b33446d4747df976b5e23a2b1ea6ff", Status:"CHECKPOINTED"} }
