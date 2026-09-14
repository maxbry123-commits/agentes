import { request } from './core';

export const apiDependencies = {
  blocker: (aufgabeId: string) => request<Array<{ id: string; titel: string; status: string }>>(`/tasks/${aufgabeId}/blocker`),
  blockiert: (aufgabeId: string) => request<Array<{ id: string; titel: string; status: string }>>(`/tasks/${aufgabeId}/blocked`),
  hinzufuegen: (aufgabeId: string, blockerId: string) =>
    request<{ success: boolean }>(`/tasks/${aufgabeId}/blocker`, { method: 'POST', body: JSON.stringify({ blockerId }) }),
  entfernen: (aufgabeId: string, blockerId: string) =>
    request<{ ok: boolean }>(`/tasks/${aufgabeId}/blocker/${blockerId}`, { method: 'DELETE' }),
};
