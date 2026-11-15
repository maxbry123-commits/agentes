package attackchain

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"00d50b3c8c2597398763afb8abfa38854fe09e52f545544f361b57a2ed7cd634", Status:"CHECKPOINTED"} }
