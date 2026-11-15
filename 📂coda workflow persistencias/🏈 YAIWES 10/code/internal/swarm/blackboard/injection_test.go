package blackboard

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"1da642a4eec501913cd017e06967ad0970bf9b819a736f3a1579f5a0ff39fc83", Status:"CHECKPOINTED"} }
