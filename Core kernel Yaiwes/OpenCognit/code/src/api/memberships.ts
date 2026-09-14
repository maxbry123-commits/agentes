import { request } from './core';
import type { Mitgliedschaft, Mitglied } from './types';

export const apiMemberships = {
  meine: () => request<Mitgliedschaft[]>('/user/memberships'),
  mitglieder: (companyId: string) => request<Mitglied[]>(`/companies/${companyId}/members`),
  einladen: (companyId: string, email: string, role?: string) =>
    request<{ token: string; email: string; role: string; message: string }>(`/companies/${companyId}/invites`, { method: 'POST', body: JSON.stringify({ email, role: role || 'member' }) }),
  akzeptieren: (token: string) =>
    request<{ ok: boolean; companyId: string; role: string }>(`/invites/${token}/accept`, { method: 'POST' }),
  entfernen: (companyId: string, userId: string) =>
    request<{ ok: boolean }>(`/companies/${companyId}/members/${userId}`, { method: 'DELETE' }),
};
