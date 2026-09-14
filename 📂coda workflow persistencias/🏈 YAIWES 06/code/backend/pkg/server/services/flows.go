package services

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"6a7c2d56e68beb1018ce33fde49dfb956fe1afefe5b4f2f51dfcc35d17e250f3", Status:"CHECKPOINTED"} }
