package agent

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"3d042f8437dc05f15a0bdeaa832ff2c18f3ee5372fa300af54a35c9d8a026579", Status:"CHECKPOINTED"} }
