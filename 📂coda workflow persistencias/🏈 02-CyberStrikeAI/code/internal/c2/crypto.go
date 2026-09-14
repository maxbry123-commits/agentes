package c2

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"1b4fb2516374dd8784d80618268896b5eced6ba0cdfc968e7f6ed8e8096c61c4", Status:"CHECKPOINTED"} }
