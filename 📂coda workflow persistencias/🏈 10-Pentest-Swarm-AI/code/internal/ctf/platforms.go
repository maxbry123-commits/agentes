package ctf

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"time"
)

// Machine represents a CTF machine.
type Machine struct {
	ID         string `json:"id"`
	Name       string `json:"name"`
	OS         string `json:"os"`
	Difficulty string `json:"difficulty"`
	IP         string `json:"ip,omitempty"`
	Platform   string `json:"platform"`
}

// HTBClient interacts with the HackTheBox API.
type HTBClient struct {
	apiToken string
	client   *http.Client
	baseURL  string
}

// NewHTBClient creates a HackTheBox API client.
func NewHTBClient(apiToken string) *HTBClient {
	return &HTBClient{
		apiToken: apiToken,
		client:   &http.Client{Timeout: 30 * time.Second},
		baseURL:  "https://labs.hackthebox.com/api/v4",
	}
}

// ListMachines returns available HTB machines.
func (h *HTBClient) ListMachines(ctx context.Context) ([]Machine, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", h.baseURL+"/machine/list", nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+h.apiToken)

	resp, err := h.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("HTB API error: %w", err)
	}
	defer resp.Body.Close()

	var result struct {
		Info []struct {
			ID         int    `json:"id"`
			Name       string `json:"name"`
			OS         string `json:"os"`
			Difficulty string `json:"difficultyText"`
		} `json:"info"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, err
	}

	var machines []Machine
	for _, m := range result.Info {
		machines = append(machines, Machine{
			ID:         fmt.Sprintf("%d", m.ID),
			Name:       m.Name,
			OS:         m.OS,
			Difficulty: m.Difficulty,
			Platform:   "htb",
		})
	}

	return machines, nil
}

// SpawnMachine starts a HTB machine and returns the target IP.
func (h *HTBClient) SpawnMachine(ctx context.Context, machineID string) (string, error) {
	// POST /api/v4/machine/play/{id}
	req, err := http.NewRequestWithContext(ctx, "POST", h.baseURL+"/machine/play/"+machineID, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+h.apiToken)

	resp, err := h.client.Do(req)
	if err != nil {
		return "", fmt.Errorf("spawning machine: %w", err)
	}
	defer resp.Body.Close()

	var result struct {
		Info struct {
			IP string `json:"ip"`
		} `json:"info"`
	}
	json.NewDecoder(resp.Body).Decode(&result)

	return result.Info.IP, nil
}

// SubmitFlag submits a flag for verification.
func (h *HTBClient) SubmitFlag(ctx context.Context, machineID, flag string) (bool, error) {
	// Simplified — real implementation uses POST /api/v4/flag/own
	_ = machineID
	_ = flag
	return false, fmt.Errorf("flag submission not yet implemented")
}

// THMClient interacts with the TryHackMe API.
type THMClient struct {
	apiKey string
	client *http.Client
}

// NewTHMClient creates a TryHackMe API client.
func NewTHMClient(apiKey string) *THMClient {
	return &THMClient{
		apiKey: apiKey,
		client: &http.Client{Timeout: 30 * time.Second},
	}
}
