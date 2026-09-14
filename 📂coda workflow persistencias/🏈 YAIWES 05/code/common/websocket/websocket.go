package websocket

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"1a7656f34b1ed6787cf06eeded672aee34cc243552fd502972ef0cf6720cdee1", Status:"CHECKPOINTED"} }
