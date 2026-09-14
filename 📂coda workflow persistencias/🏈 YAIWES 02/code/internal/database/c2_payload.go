package database

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"e1d8b3c4ad9ebca42f12e78b6de9314e4a41abfd9a6a8fb1f8609cc307972ba4", Status:"CHECKPOINTED"} }
