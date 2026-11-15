import { request } from './core';

export const apiSettings = {
  laden: () => request<Record<string, string>>('/settings'),
  setzen: (key: string, wert: string) =>
    request<{ schluessel: string; wert: string }>(`/settings/${key}`, { method: 'PUT', body: JSON.stringify({ wert }) }),
};
