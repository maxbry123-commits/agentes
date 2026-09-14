package database

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"30daeb178ce58f6d1cc566728a3d2ff4074816c621067dd0afd34a97cd106e93", Status:"CHECKPOINTED"} }
