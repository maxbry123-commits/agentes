import { request } from './core';
import type { DashboardData } from './types';

export const apiDashboard = {
  laden: (unternehmenId: string) => request<DashboardData>(`/companies/${unternehmenId}/dashboard`),
};
