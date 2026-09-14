import { request } from './core';
import type { Experte, Aktivitaet, AgentPermissions } from './types';

export const apiAgents = {
  liste: (unternehmenId: string) => request<Experte[]>(`/companies/${unternehmenId}/agents`),
  details: (id: string) => request<Experte>(`/agents/${id}`),
  erstellen: (unternehmenId: string, data: Partial<Experte>) =>
    request<Experte>(`/companies/${unternehmenId}/agents`, { method: 'POST', body: JSON.stringify(data) }),
  aktualisieren: (id: string, data: Partial<Experte>) =>
    request<Experte>(`/agents/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  pausieren: (id: string) =>
    request<{ success: boolean }>(`/agents/${id}/pause`, { method: 'POST' }),
  fortsetzen: (id: string) =>
    request<{ success: boolean }>(`/agents/${id}/resume`, { method: 'POST' }),
  loeschen: (id: string) =>
    request<{ success: boolean }>(`/agents/${id}`, { method: 'DELETE' }),
  aktivitaet: (id: string, limit?: number) =>
    request<Aktivitaet[]>(`/agents/${id}/activity${limit ? `?limit=${limit}` : ''}`),
};

export const apiPermissions = {
  laden: (expertId: string) => request<AgentPermissions>(`/agents/${expertId}/permissions`),
  speichern: (expertId: string, data: Partial<AgentPermissions>) =>
    request<AgentPermissions>(`/agents/${expertId}/permissions`, { method: 'PUT', body: JSON.stringify(data) }),
};
