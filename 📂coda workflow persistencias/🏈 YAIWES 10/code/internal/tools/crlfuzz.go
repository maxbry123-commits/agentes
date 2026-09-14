package tools

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"018fd1453079068ba0ed831469e448ed28e897388d1a4169ca9a6600db01849d", Status:"CHECKPOINTED"} }
