import { request } from './core';
import type { BudgetPolicy, BudgetIncident, BudgetForecast } from './types';

export const apiBudget = {
  policies: (uid: string) => request<BudgetPolicy[]>(`/companies/${uid}/budget-policies`),
  createPolicy: (uid: string, data: Partial<BudgetPolicy>) =>
    request<{ id: string }>(`/companies/${uid}/budget-policies`, { method: 'POST', body: JSON.stringify(data) }),
  incidents: (uid: string) => request<BudgetIncident[]>(`/companies/${uid}/budget-incidents`),
  forecast: (uid: string) => request<{ forecasts: BudgetForecast[] }>(`/companies/${uid}/budget/forecast`),
};
