package openai

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"d31ed88b911648e51a025251cfdbbf61354088a4a9430c766b45d79810e948f8", Status:"CHECKPOINTED"} }
