package preload

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"common/fingerprints/preload/version_detection_test.go", Status:"CHECKPOINTED"} }
