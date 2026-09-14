package preload

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"common/fingerprints/preload/preload.go", Status:"CHECKPOINTED"} }
