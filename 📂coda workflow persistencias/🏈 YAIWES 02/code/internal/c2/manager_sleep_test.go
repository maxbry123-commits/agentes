package c2

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"fa19d52d84dec59c8597959a204f51b788589cbbe4edd8dabef995a5478bbd80", Status:"CHECKPOINTED"} }
