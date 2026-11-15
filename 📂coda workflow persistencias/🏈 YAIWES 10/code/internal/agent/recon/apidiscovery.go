package recon

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"1dd54dfd2053ad73811e413b03b281bd24ef35b156d43fc467e08a3b0edc170a", Status:"CHECKPOINTED"} }
