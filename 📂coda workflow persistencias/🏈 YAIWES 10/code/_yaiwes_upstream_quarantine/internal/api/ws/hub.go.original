package ws

import (
	"encoding/json"
	"sync"

	"github.com/Armur-Ai/Pentest-Swarm-AI/internal/pipeline"
	"github.com/fasthttp/websocket"
)

// EventHub manages WebSocket connections per campaign for real-time event streaming.
type EventHub struct {
	mu    sync.RWMutex
	conns map[string][]*websocket.Conn // campaignID -> connections
}

// NewEventHub creates a new event hub.
func NewEventHub() *EventHub {
	return &EventHub{
		conns: make(map[string][]*websocket.Conn),
	}
}

// Subscribe registers a WebSocket connection for a campaign.
func (h *EventHub) Subscribe(campaignID string, conn *websocket.Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.conns[campaignID] = append(h.conns[campaignID], conn)
}

// Unsubscribe removes a WebSocket connection.
func (h *EventHub) Unsubscribe(campaignID string, conn *websocket.Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()

	conns := h.conns[campaignID]
	for i, c := range conns {
		if c == conn {
			h.conns[campaignID] = append(conns[:i], conns[i+1:]...)
			break
		}
	}

	if len(h.conns[campaignID]) == 0 {
		delete(h.conns, campaignID)
	}
}

// Publish sends an event to all WebSocket subscribers for a campaign.
func (h *EventHub) Publish(campaignID string, event pipeline.CampaignEvent) {
	h.mu.RLock()
	conns := h.conns[campaignID]
	h.mu.RUnlock()

	if len(conns) == 0 {
		return
	}

	data, err := json.Marshal(event)
	if err != nil {
		return
	}

	for _, conn := range conns {
		if err := conn.WriteMessage(websocket.TextMessage, data); err != nil {
			// Connection dead — will be cleaned up on next Unsubscribe
			conn.Close()
		}
	}
}

// SubscriberCount returns the number of active subscribers for a campaign.
func (h *EventHub) SubscriberCount(campaignID string) int {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return len(h.conns[campaignID])
}
