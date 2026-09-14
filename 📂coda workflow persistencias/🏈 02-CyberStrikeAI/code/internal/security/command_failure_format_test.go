package security

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"8b03d88e61f2362999d21257aee2ea3b8854853e3b772487f3b25eb590de2a0e", Status:"CHECKPOINTED"} }
