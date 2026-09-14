package app

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"04cab2d948d1bb03f3a29da03942b06ebeb99b766ba06e29ef4994b7462bc974", Status:"CHECKPOINTED"} }
