package resources

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"c93d102fd91101802e3e78c75ecee25b1f32dee07dd2bdb47c1459122c58fc40", Status:"CHECKPOINTED"} }
