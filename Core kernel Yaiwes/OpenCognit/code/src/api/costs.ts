import { request } from './core';
import type { KostenZusammenfassung, ProviderKosten, TimelineTag } from './types';

export const apiCosts = {
  zusammenfassung: (unternehmenId: string) => request<KostenZusammenfassung>(`/companies/${unternehmenId}/costs/summary`),
  nachProvider: (unternehmenId: string) => request<ProviderKosten[]>(`/companies/${unternehmenId}/costs/by-provider`),
  timeline: (unternehmenId: string, tage?: number) => request<TimelineTag[]>(`/companies/${unternehmenId}/costs/timeline${tage ? `?days=${tage}` : ''}`),
};
