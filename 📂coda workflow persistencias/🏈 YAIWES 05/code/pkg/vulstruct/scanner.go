package vulstruct

type YAIWESPersistenceEvent struct { SourceID string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{SourceID:"3b09d6200a8c14ca64197bfd4d8c996401d7c002220a6aa397e5858865ebb8c0", Status:"CHECKPOINTED"} }
