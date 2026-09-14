import { request } from './core';
import type { Unternehmen } from './types';

export const apiCompanies = {
  liste: () => request<Unternehmen[]>('/companies'),
  details: (id: string) => request<Unternehmen>(`/companies/${id}`),
  erstellen: (data: { name: string; beschreibung?: string; ziel?: string }) =>
    request<Unternehmen>('/companies', { method: 'POST', body: JSON.stringify(data) }),
  aktualisieren: (id: string, data: Partial<Unternehmen>) =>
    request<Unternehmen>(`/companies/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  loeschen: (id: string) =>
    request<{ success: boolean }>(`/companies/${id}`, { method: 'DELETE' }),
};
