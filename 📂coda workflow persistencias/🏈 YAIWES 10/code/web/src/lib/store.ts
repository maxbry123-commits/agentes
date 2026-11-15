import { create } from "zustand";
import type { Campaign, CampaignEvent, Finding } from "./api";

interface DashboardStore {
  // Campaigns
  campaigns: Campaign[];
  setCampaigns: (campaigns: Campaign[]) => void;
  activeCampaignId: string | null;
  setActiveCampaignId: (id: string | null) => void;

  // Events (from WebSocket)
  events: CampaignEvent[];
  addEvent: (event: CampaignEvent) => void;
  clearEvents: () => void;

  // Findings
  findings: Finding[];
  setFindings: (findings: Finding[]) => void;
  addFinding: (finding: Finding) => void;

  // Agent status
  agentStatuses: Record<string, "idle" | "active" | "complete" | "error">;
  setAgentStatus: (agent: string, status: "idle" | "active" | "complete" | "error") => void;

  // UI state
  selectedPanel: "surface" | "paths" | "mitre";
  setSelectedPanel: (panel: "surface" | "paths" | "mitre") => void;
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  campaigns: [],
  setCampaigns: (campaigns) => set({ campaigns }),
  activeCampaignId: null,
  setActiveCampaignId: (id) => set({ activeCampaignId: id }),

  events: [],
  addEvent: (event) =>
    set((state) => ({ events: [...state.events.slice(-500), event] })),
  clearEvents: () => set({ events: [] }),

  findings: [],
  setFindings: (findings) => set({ findings }),
  addFinding: (finding) =>
    set((state) => ({ findings: [...state.findings, finding] })),

  agentStatuses: {
    orchestrator: "idle",
    recon: "idle",
    classifier: "idle",
    exploit: "idle",
    report: "idle",
  },
  setAgentStatus: (agent, status) =>
    set((state) => ({
      agentStatuses: { ...state.agentStatuses, [agent]: status },
    })),

  selectedPanel: "surface",
  setSelectedPanel: (panel) => set({ selectedPanel: panel }),
}));
