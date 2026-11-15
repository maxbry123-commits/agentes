import { request } from './core';
import type { Projekt } from './types';

export const apiProjects = {
  liste: (unternehmenId: string) => request<Projekt[]>(`/companies/${unternehmenId}/projects`),
  details: (id: string) => request<Projekt>(`/projects/${id}`),
  erstellen: (unternehmenId: string, data: Partial<Projekt>) =>
    request<Projekt>(`/companies/${unternehmenId}/projects`, { method: 'POST', body: JSON.stringify(data) }),
  aktualisieren: (id: string, data: Partial<Projekt>) =>
    request<Projekt>(`/projects/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  loeschen: (id: string) =>
    request<{ success: boolean }>(`/projects/${id}`, { method: 'DELETE' }),
  fortschrittAktualisieren: (id: string) =>
    request<Projekt>(`/projects/${id}/fortschritt-aktualisieren`, { method: 'POST' }),
};
