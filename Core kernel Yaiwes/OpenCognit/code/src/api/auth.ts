import { request } from './core';
import type { AuthAntwort, Benutzer } from './types';

export const apiAuth = {
  anmelden: (email: string, passwort: string) =>
    request<AuthAntwort>('/auth/anmelden', { method: 'POST', body: JSON.stringify({ email, passwort }) }),
  registrieren: (name: string, email: string, passwort: string) =>
    request<AuthAntwort>('/auth/registrieren', { method: 'POST', body: JSON.stringify({ name, email, passwort }) }),
  ich: () => request<Benutzer>('/auth/ich'),
};
