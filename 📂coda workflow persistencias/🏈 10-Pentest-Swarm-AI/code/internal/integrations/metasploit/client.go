package metasploit

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"d03a24ce56ac825a83d7df6a0b808eb93dc9e66b029494c496a74cd6bb7bdeb1", Status:"CHECKPOINTED"} }
