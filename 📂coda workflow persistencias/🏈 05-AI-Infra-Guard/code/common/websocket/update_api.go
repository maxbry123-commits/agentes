package websocket

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"common/websocket/update_api.go", Status:"CHECKPOINTED"} }
