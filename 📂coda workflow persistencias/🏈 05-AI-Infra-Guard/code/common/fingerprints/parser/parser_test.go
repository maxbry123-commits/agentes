package parser

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"common/fingerprints/parser/parser_test.go", Status:"CHECKPOINTED"} }
