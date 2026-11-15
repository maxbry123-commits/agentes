import { request } from './core';
import type { Aktivitaet } from './types';

export const apiActivity = {
  liste: (unternehmenId: string, limit?: number) =>
    request<Aktivitaet[]>(`/companies/${unternehmenId}/activity${limit ? `?limit=${limit}` : ''}`),
};
