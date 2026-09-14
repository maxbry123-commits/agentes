package websocket

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"e20ca0066794f596068a8be605c1456cc2ac6f8c308e94b4fc05ed3f07085f59", Status:"CHECKPOINTED"} }
