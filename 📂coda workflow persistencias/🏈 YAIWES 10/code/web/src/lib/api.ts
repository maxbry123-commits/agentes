const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080/api/v1";

export interface Campaign {
  id: string;
  name: string;
  target: string;
  objective: string;
  status: string;
  mode: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface Finding {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low" | "informational";
  cvss_score: number;
  description: string;
  target: string;
  attack_category: string;
}

export interface CampaignEvent {
  id: string;
  campaign_id: string;
  timestamp: string;
  event_type: string;
  agent_name: string;
  detail: string;
}

async function fetchAPI<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  campaigns: {
    list: () => fetchAPI<{ data: Campaign[] }>("/campaigns"),
    get: (id: string) => fetchAPI<Campaign>(`/campaigns/${id}`),
    create: (data: Partial<Campaign>) =>
      fetch(`${API_BASE}/campaigns`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      }).then((r) => r.json()),
    start: (id: string) =>
      fetch(`${API_BASE}/campaigns/${id}/start`, { method: "POST" }),
    stop: (id: string) =>
      fetch(`${API_BASE}/campaigns/${id}/stop`, { method: "POST" }),
  },
  findings: {
    list: (campaignId: string) =>
      fetchAPI<{ data: Finding[] }>(`/campaigns/${campaignId}/findings`),
  },
  models: {
    list: () => fetchAPI<{ models: string[] }>("/models"),
  },
  stats: () => fetchAPI<Record<string, number>>("/stats"),
};

export function connectWebSocket(campaignId: string, onEvent: (event: CampaignEvent) => void): WebSocket {
  const wsUrl = API_BASE.replace("http", "ws") + `/campaigns/${campaignId}/ws`;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (msg) => {
    try {
      const event = JSON.parse(msg.data) as CampaignEvent;
      onEvent(event);
    } catch {
      // ignore parse errors
    }
  };

  return ws;
}
