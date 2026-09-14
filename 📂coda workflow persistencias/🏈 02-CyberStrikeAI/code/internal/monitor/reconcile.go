package monitor

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"042e96c470fe17e5376fb74369c82f169227d0ad9033038c57648f96e805434e", Status:"CHECKPOINTED"} }
