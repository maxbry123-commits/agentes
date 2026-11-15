package handler

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"e3b4e47262c3979a5a2413e032a261d65214e82d6dd73dc1c0a3d6ff13586d89", Status:"CHECKPOINTED"} }
