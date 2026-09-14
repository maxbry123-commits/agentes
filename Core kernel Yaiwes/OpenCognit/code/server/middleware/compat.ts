import type express from 'express';

// ===== DE → EN URL compatibility layer =====
// The frontend still calls German-named endpoints while the backend
// routes were refactored to English. This middleware rewrites URLs
// so old frontend code continues to work.
export function urlRewrite(req: express.Request, _res: express.Response, next: express.NextFunction) {
  req.url = req.url
    .replace(/^\/api\/unternehmen/, '/api/companies')
    .replace(/^\/api\/einstellungen/, '/api/settings')
    .replace(/\/experten\b/g, '/agents')
    .replace(/\/mitarbeiter\b/g, '/agents')
    .replace(/\/aufgaben\b/g, '/tasks')
    .replace(/\/ziele\b/g, '/goals')
    .replace(/\/routinen\b/g, '/routines')
    .replace(/\/genehmigungen\b/g, '/approvals')
    .replace(/\/projekte\b/g, '/projects')
    .replace(/\/aktivitaet\b/g, '/activity')
    .replace(/\/agent-qualitaet\b/g, '/agent-quality')
    .replace(/\/kosten\b/g, '/costs')
    .replace(/\/zusammenfassung\b/g, '/summary')
    .replace(/\/nach-provider\b/g, '/by-provider')
    .replace(/\/pausieren\b/g, '/pause')
    .replace(/\/fortsetzen\b/g, '/resume')
    .replace(/\/genehmigen\b/g, '/approve')
    .replace(/\/ablehnen\b/g, '/reject');
  next();
}

// ===== EN → DE response field aliasing =====
// Frontend code still reads German field names on many pages.
// This middleware wraps res.json to add German aliases on responses
// so old frontend code keeps working until the migration is complete.
const FIELD_ALIASES: Record<string, string> = {
  title: 'titel',
  description: 'beschreibung',
  createdAt: 'erstelltAm',
  updatedAt: 'aktualisiertAm',
  completedAt: 'abgeschlossenAm',
  assignedTo: 'zugewiesenAn',
  priority: 'prioritaet',
  connectionType: 'verbindungsTyp',
  connectionConfig: 'verbindungsConfig',
  costCent: 'kostenCent',
  message: 'nachricht',
  senderType: 'absenderTyp',
  agentId: 'expertId',
  companyId: 'unternehmenId',
  taskId: 'aufgabeId',
  key: 'schluessel',
  value: 'wert',
  type: 'typ',
  role: 'rolle',
  skills: 'faehigkeiten',
  avatarColor: 'avatarFarbe',
  autoCycleActive: 'zyklusAktiv',
  autoCycleIntervalSec: 'zyklusIntervallSek',
  monthlyBudgetCent: 'budgetMonatCent',
  monthlySpendCent: 'verbrauchtMonatCent',
  goal: 'ziel',
  level: 'ebene',
  progress: 'fortschritt',
  ownerAgentId: 'eigentuemerExpertId',
  organizerAgentId: 'veranstalterExpertId',
  participantIds: 'teilnehmerIds',
  result: 'ergebnis',
  decidedAt: 'entschiedenAm',
  decisionNote: 'entscheidungsnotiz',
  requestedBy: 'angefordertVon',
  actorType: 'akteurTyp',
  actorId: 'akteurId',
  actorName: 'akteurName',
  action: 'aktion',
  entityType: 'entitaetTyp',
  entityId: 'entitaetId',
  read: 'gelesen',
  active: 'aktiv',
  content: 'inhalt',
  lastCycle: 'letzterZyklus',
  uses: 'nutzungen',
  successes: 'erfolge',
  confidence: 'konfidenz',
  source: 'quelle',
  createdBy: 'erstelltVon',
};

function aliasObject(obj: any): any {
  if (obj === null || typeof obj !== 'object') return obj;
  if (Array.isArray(obj)) return obj.map(aliasObject);
  const out: any = { ...obj };
  for (const [eng, de] of Object.entries(FIELD_ALIASES)) {
    if (eng in out && !(de in out)) out[de] = out[eng];
  }
  // Recurse into nested objects (e.g. approval.payload.params)
  for (const k of Object.keys(out)) {
    if (out[k] && typeof out[k] === 'object') out[k] = aliasObject(out[k]);
  }
  return out;
}

export function responseAlias(_req: express.Request, res: express.Response, next: express.NextFunction) {
  const orig = res.json.bind(res);
  res.json = (body: any) => orig(aliasObject(body));
  next();
}
