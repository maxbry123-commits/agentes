package audit

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"cb6244ec7c876f7fbcdf522eed235c833255856a71fc0250b5efd7ad62b336fb", Status:"CHECKPOINTED"} }
