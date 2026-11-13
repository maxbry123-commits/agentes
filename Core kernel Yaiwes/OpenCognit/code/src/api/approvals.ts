import { request } from './core';
import type { Genehmigung } from './types';

export const apiApprovals = {
  liste: (unternehmenId: string) => request<Genehmigung[]>(`/companies/${unternehmenId}/approvals`),
  genehmigen: (id: string, notiz?: string) =>
    request<Genehmigung>(`/approvals/${id}/approve`, { method: 'POST', body: JSON.stringify({ notiz }) }),
  ablehnen: (id: string, notiz?: string) =>
    request<Genehmigung>(`/approvals/${id}/reject`, { method: 'POST', body: JSON.stringify({ notiz }) }),
};
