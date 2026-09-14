package c2

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"internal/c2/listener_websocket.go", Status:"CHECKPOINTED"} }
