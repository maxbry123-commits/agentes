package scoreconfigs

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"fd15056bc1879871fa538f30d105df2c2fd8144a1cb63f69eb752a8a0ea8f97d", Status:"CHECKPOINTED"} }
