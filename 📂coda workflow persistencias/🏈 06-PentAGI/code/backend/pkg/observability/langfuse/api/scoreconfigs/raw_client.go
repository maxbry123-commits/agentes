package scoreconfigs

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"fbf716be2bba37bf2a48704328240dc1dd70e59ed9b854bcd63538d5857af1f5", Status:"CHECKPOINTED"} }
