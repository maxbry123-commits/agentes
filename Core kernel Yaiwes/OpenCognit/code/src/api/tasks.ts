import { request } from './core';
import type { Aufgabe, Kommentar } from './types';

export const apiTasks = {
  liste: (unternehmenId: string) => request<Aufgabe[]>(`/companies/${unternehmenId}/tasks`),
  details: (id: string) => request<Aufgabe>(`/tasks/${id}`),
  erstellen: (unternehmenId: string, data: Partial<Aufgabe>) =>
    request<Aufgabe>(`/companies/${unternehmenId}/tasks`, { method: 'POST', body: JSON.stringify(data) }),
  aktualisieren: (id: string, data: Partial<Aufgabe>) =>
    request<Aufgabe>(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  checkout: (id: string, expertId: string) =>
    request<Aufgabe>(`/tasks/${id}/checkout`, { method: 'POST', body: JSON.stringify({ expertId }) }),
  kommentare: (id: string) => request<Kommentar[]>(`/tasks/${id}/comments`),
  kommentieren: (id: string, inhalt: string, autorTyp?: string) =>
    request<Kommentar>(`/tasks/${id}/comments`, { method: 'POST', body: JSON.stringify({ inhalt, autorTyp }) }),
};
