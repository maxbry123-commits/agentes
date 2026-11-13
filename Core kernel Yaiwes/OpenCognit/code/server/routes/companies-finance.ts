// =============================================================================
// Companies finance routes — costs, budget forecast, budget policies + incidents.
// Extracted from server/index.ts as part of the routes-split refactor.
// =============================================================================

import { Router } from 'express';
import { v4 as uuid } from 'uuid';
import { eq, sql } from 'drizzle-orm';

import { db } from '../db/client.js';
import { agents, costEntries, budgetPolicies, budgetIncidents } from '../db/schema.js';
import { erstellePolicy, berechneBudgetStatus } from '../services/budget-policies.js';
import { logAktivitaet } from '../services/activity-log.js';
import { requireCompanyAccess, authMiddleware } from '../middleware/auth.js';

const router = Router();
const now = () => new Date().toISOString();

// =============================================
// BUDGET FORECAST
// =============================================

router.get('/api/companies/:unternehmenId/budget/forecast', requireCompanyAccess(), async (req, res) => {
  try {
    const { getForecasts } = await import('../services/budget-forecast.js');
    res.json({ forecasts: getForecasts(req.params.unternehmenId) });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

// =============================================
// COSTS — summary, by-provider, timeline
// =============================================

router.get('/api/companies/:unternehmenId/costs/summary', requireCompanyAccess(), (req, res) => {
  const agenten = db.select().from(agents).where(eq(agents.companyId, req.params.unternehmenId)).all();

  const gesamtVerbraucht = agenten.reduce((s: number, a: any) => s + a.monthlySpendCent, 0);
  const gesamtBudget = agenten.reduce((s: number, a: any) => s + a.monthlyBudgetCent, 0);

  const proAgent = agenten.map((a: any) => ({
    id: a.id,
    name: a.name,
    titel: a.title,
    avatar: a.avatar,
    avatarFarbe: a.avatarColor,
    verbindungsTyp: a.connectionType,
    verbrauchtMonatCent: a.monthlySpendCent,
    budgetMonatCent: a.monthlyBudgetCent,
    prozent: a.monthlyBudgetCent > 0 ? Math.round((a.monthlySpendCent / a.monthlyBudgetCent) * 100) : 0,
  })).sort((a: any, b: any) => b.prozent - a.prozent);

  res.json({
    gesamtVerbraucht,
    gesamtBudget,
    gesamtProzent: gesamtBudget > 0 ? Math.round((gesamtVerbraucht / gesamtBudget) * 100) : 0,
    proExperte: proAgent,
  });
});

// Costs aggregated per provider
router.get('/api/companies/:unternehmenId/costs/by-provider', requireCompanyAccess(), (req, res) => {
  const buchungen = db.select().from(costEntries)
    .where(eq(costEntries.companyId, req.params.unternehmenId as string)).all();

  const providerMap = new Map<string, { kosten: number; tokens: number; buchungen: number }>();
  for (const b of buchungen) {
    const key = b.provider;
    const entry = providerMap.get(key) || { kosten: 0, tokens: 0, buchungen: 0 };
    entry.kosten += b.costCent;
    entry.tokens += b.inputTokens + b.outputTokens;
    entry.buchungen += 1;
    providerMap.set(key, entry);
  }

  const result = Array.from(providerMap.entries())
    .map(([anbieter, data]) => ({ anbieter, ...data }))
    .sort((a, b) => b.kosten - a.kosten);

  res.json(result);
});

// Cost timeline (last N days, daily aggregated)
router.get('/api/companies/:unternehmenId/costs/timeline', requireCompanyAccess(), (req, res) => {
  const tage = parseInt(req.query.tage as string) || 14;
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - tage);
  const startISO = startDate.toISOString();

  const buchungen = db.select().from(costEntries)
    .where(eq(costEntries.companyId, req.params.unternehmenId as string))
    .all()
    .filter(b => b.timestamp >= startISO);

  const tageMap = new Map<string, number>();
  for (let i = 0; i < tage; i++) {
    const d = new Date();
    d.setDate(d.getDate() - (tage - 1 - i));
    tageMap.set(d.toISOString().split('T')[0], 0);
  }

  for (const b of buchungen) {
    const tag = b.timestamp.split('T')[0];
    tageMap.set(tag, (tageMap.get(tag) || 0) + b.costCent);
  }

  const result = Array.from(tageMap.entries())
    .map(([datum, kostenCent]) => ({ datum, kostenCent }));

  res.json(result);
});

// Record a cost entry — also updates the agent's monthly spend and pauses
// the agent if the configured monthly budget is hit.
router.post('/api/companies/:unternehmenId/costEntries', requireCompanyAccess(), (req, res) => {
  const { expertId, aufgabeId, anbieter, modell, inputTokens, outputTokens, kostenCent } = req.body;
  if (!expertId || !anbieter || !modell || kostenCent === undefined) {
    return res.status(400).json({ error: 'Required: agentId, provider, model, costCent' });
  }

  const id = uuid();
  db.insert(costEntries).values({
    id,
    companyId: req.params.unternehmenId,
    agentId: expertId,
    taskId: aufgabeId || null,
    provider: anbieter,
    model: modell,
    inputTokens: inputTokens || 0,
    outputTokens: outputTokens || 0,
    costCent: kostenCent,
    timestamp: now(),
    createdAt: now(),
  }).run();

  db.update(agents).set({
    monthlySpendCent: sql`${agents.monthlySpendCent} + ${kostenCent}`,
    updatedAt: now(),
  }).where(eq(agents.id, expertId as string)).run();

  // Check budget threshold — pause agent at 100%
  const agent = db.select().from(agents).where(eq(agents.id, expertId as string)).get();
  if (agent && agent.monthlyBudgetCent > 0) {
    const prozent = Math.round((agent.monthlySpendCent / agent.monthlyBudgetCent) * 100);
    if (prozent >= 100 && agent.status !== 'paused') {
      db.update(agents).set({ status: 'paused', updatedAt: now() }).where(eq(agents.id, expertId as string)).run();
      logAktivitaet(req.params.unternehmenId, 'system', 'system', 'System', `${agent.name} wurde pausiert (Budget ${prozent}%)`, 'agents', expertId);
    }
  }

  res.status(201).json({ id });
});

// =============================================
// BUDGET POLICIES + INCIDENTS
// =============================================

router.get('/api/companies/:id/budget-policies', authMiddleware, requireCompanyAccess(), (req, res) => {
  const policies = db.select().from(budgetPolicies)
    .where(eq(budgetPolicies.companyId, req.params.id as string)).all();
  const mitStatus = policies.map(p => ({ ...p, status: berechneBudgetStatus(p.id) }));
  res.json(mitStatus);
});

router.post('/api/companies/:id/budget-policies', authMiddleware, requireCompanyAccess(), (req, res) => {
  const { scope, scopeId, limitCent, fenster, warnProzent, hardStop } = req.body;
  const id = erstellePolicy({
    unternehmenId: req.params.id as string,
    scope, scopeId, limitCent, fenster, warnProzent, hardStop,
  });
  res.json({ id });
});

router.get('/api/companies/:id/budget-incidents', authMiddleware, requireCompanyAccess(), (req, res) => {
  const incidents = db.select().from(budgetIncidents)
    .where(eq(budgetIncidents.companyId, req.params.id as string)).all();
  res.json(incidents);
});

export default router;
