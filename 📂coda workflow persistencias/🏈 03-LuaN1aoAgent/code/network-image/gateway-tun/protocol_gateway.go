package main

type YAIWESPersistenceEvent struct { Source string; Status string }
func YAIWESPersistenceStep() YAIWESPersistenceEvent { return YAIWESPersistenceEvent{Source:"network-image/gateway-tun/protocol_gateway.go", Status:"CHECKPOINTED"} }
