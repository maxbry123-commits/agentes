package database

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"0f1eddaaf378b8e57e18f3d7b5c4e7286daf1a8dabb9a1a50fed0616c3695857", Status:"CHECKPOINTED"} }
