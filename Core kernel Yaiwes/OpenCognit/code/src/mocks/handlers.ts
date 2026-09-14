import { http, HttpResponse } from 'msw'

export const handlers = [
  // Auth
  http.get('/api/auth/ich', () => {
    return HttpResponse.json({ id: 'u1', name: 'Test User', email: 'test@example.com', rolle: 'admin' })
  }),

  // Companies
  http.get('/api/companies', () => {
    return HttpResponse.json([
      { id: 'c1', name: 'Test Company', beschreibung: null, ziel: null, status: 'active', erstelltAm: new Date().toISOString(), aktualisiertAm: new Date().toISOString() },
    ])
  }),

  // Dashboard
  http.get('/api/companies/:id/dashboard', () => {
    return HttpResponse.json({
      unternehmen: { id: 'c1', name: 'Test Company', beschreibung: null, ziel: null, status: 'active', erstelltAm: new Date().toISOString(), aktualisiertAm: new Date().toISOString() },
      experten: { gesamt: 0, aktiv: 0, running: 0, paused: 0, error: 0 },
      aufgaben: { gesamt: 0, offen: 0, inBearbeitung: 0, erledigt: 0, blockiert: 0, completedPerDay: [] },
      kosten: { gesamtVerbraucht: 0, gesamtBudget: 0, prozent: 0 },
      pendingApprovals: 0,
      topExperten: [],
      letzteAktivitaet: [],
    })
  }),

  // Tasks
  http.get('/api/companies/:id/tasks', () => {
    return HttpResponse.json([])
  }),

  // Agents
  http.get('/api/companies/:id/agents', () => {
    return HttpResponse.json([])
  }),

  // Settings
  http.get('/api/settings', () => {
    return HttpResponse.json({})
  }),

  // Settings
  http.put('/api/einstellungen/:key', async () => {
    return HttpResponse.json({ schluessel: 'ui_language', wert: 'en' })
  }),

  // Health
  http.get('/api/health', () => {
    return HttpResponse.json({ status: 'ok', version: '0.1.0', name: 'opencognit' })
  }),
]
