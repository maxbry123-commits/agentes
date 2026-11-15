import { Router } from 'express';
import fs from 'fs';
import path from 'path';
import { db } from '../db/client.js';
import { agents, companies, settings } from '../db/schema.js';
import { eq } from 'drizzle-orm';
import { decryptSetting } from '../utils/crypto.js';
import { getUiLanguage } from '../services/messaging.js';
import { v4 as uuid } from 'uuid';
import { authMiddleware, requireResourceAccess } from '../middleware/auth.js';

const router = Router();

// ── Export SOUL.md ───────────────────────────────────────────────────────────
router.post('/api/agents/:id/export-soul', authMiddleware, requireResourceAccess("agent"), async (req, res) => {
  try {
    const agent = db.select().from(agents).where(eq(agents.id, req.params.id as string)).get();
    if (!agent) return res.status(404).json({ error: 'Agent not found' });

    const soulsDir = path.resolve('data', 'souls');
    if (!fs.existsSync(soulsDir)) fs.mkdirSync(soulsDir, { recursive: true });

    const safeName = agent.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    const soulPath = path.join(soulsDir, `${safeName}.soul.md`);

    const company = db.select().from(companies).where(eq(companies.id, agent.companyId)).get();
    const soulContent = [
      `# SOUL — ${agent.name} [${agent.role}]`,
      `version: ${new Date().toISOString().slice(0, 10)}`,
      '',
      `## Identität`,
      `Ich bin ${agent.name}, ${agent.role}${company ? ` bei {{company.name}}` : ''}.`,
      agent.title ? `Titel: ${agent.title}` : '',
      '',
      `## Fähigkeiten`,
      agent.skills
        ? agent.skills.split(',').map((s: string) => `- ${s.trim()}`).join('\n')
        : `- Allgemeiner Agent`,
      '',
      `## Kernverhalten`,
      agent.systemPrompt
        ? agent.systemPrompt
        : `- Ich erledige mir zugewiesene Aufgaben präzise und vollständig.`,
      '',
      `## Gedächtnis-Präferenzen`,
      `- Ich speichere Entscheidungen in [entscheidungen]`,
      `- Ich tracke Projektstatus in [projekt]`,
      `- Ich archiviere abgeschlossene Erkenntnisse in [erkenntnisse]`,
      '',
      `## Grenzen`,
      `- Ich handle nur im Rahmen meiner zugewiesenen Aufgaben`,
      `- Ich eskaliere blockierte Tasks an meinen Vorgesetzten`,
    ].filter(l => l !== undefined && l !== null).join('\n');

    fs.writeFileSync(soulPath, soulContent, 'utf-8');

    db.update(agents)
      .set({ soulPath, soulVersion: null })
      .where(eq(agents.id, agent.id))
      .run();

    res.json({ soulPath, content: soulContent });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

// ── SOUL.md: read file content ────────────────────────────────────────────────
router.get('/api/agents/:id/soul', authMiddleware, requireResourceAccess("agent"), (req, res) => {
  try {
    const agent = db.select({ soulPath: agents.soulPath, soulVersion: agents.soulVersion, name: agents.name })
      .from(agents).where(eq(agents.id, req.params.id as string)).get();
    if (!agent) return res.status(404).json({ error: 'Agent not found' });
    if (!agent.soulPath || !fs.existsSync(agent.soulPath)) {
      return res.json({ soulPath: null, content: null });
    }
    const content = fs.readFileSync(agent.soulPath, 'utf-8');
    res.json({ soulPath: agent.soulPath, soulVersion: agent.soulVersion, content });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

// ── SOUL.md: save edited content ──────────────────────────────────────────────
router.put('/api/agents/:id/soul', authMiddleware, requireResourceAccess("agent"), (req, res) => {
  try {
    const { content } = req.body;
    if (typeof content !== 'string') return res.status(400).json({ error: 'content required' });

    const agent = db.select({ soulPath: agents.soulPath, name: agents.name, unternehmenId: agents.companyId })
      .from(agents).where(eq(agents.id, req.params.id as string)).get();
    if (!agent) return res.status(404).json({ error: 'Agent not found' });

    let soulPath = agent.soulPath;
    if (!soulPath) {
      const soulsDir = path.resolve('data', 'souls');
      if (!fs.existsSync(soulsDir)) fs.mkdirSync(soulsDir, { recursive: true });
      const safeName = agent.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
      soulPath = path.join(soulsDir, `${safeName}.soul.md`);
    }

    fs.writeFileSync(soulPath, content, 'utf-8');
    db.update(agents).set({ soulPath, soulVersion: null }).where(eq(agents.id, req.params.id as string)).run();

    res.json({ success: true, soulPath });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

// ─── SOUL Generator ──────────────────────────────────────────────────────────
router.post('/api/agents/:id/soul/generate', authMiddleware, requireResourceAccess("agent"), async (req, res) => {
  try {
    const expert = db.select().from(agents).where(eq(agents.id, req.params.id as string)).get() as any;
    if (!expert) return res.status(404).json({ error: 'Expert not found' });

    const company = db.select().from(companies).where(eq(companies.id, expert.companyId)).get() as any;
    const lang = getUiLanguage(expert.companyId);
    const isEn = lang === 'en';

    const prompt = isEn ? `You are an AI architect. Generate a structured SOUL document for this AI agent.

Agent:
- Name: ${expert.name}
- Role: ${expert.role}
- Skills: ${expert.skills || 'none specified'}
- Is Orchestrator/CEO: ${expert.isOrchestrator ? 'yes' : 'no'}
- Company: ${company?.name || 'unknown'}
- Company goal: ${company?.goal || 'not defined'}

Generate a SOUL with exactly these 4 sections. Respond ONLY with this JSON, no text before/after:
{
  "identity": "2-3 sentences: Who am I? What is my core task?",
  "principles": "4-5 decision principles as a numbered list",
  "checklist": "5-6 bullet points of what the agent does on every wakeup",
  "personality": "2-3 sentences about communication style and personality"
}` : `Du bist ein KI-Architekt. Generiere ein strukturiertes SOUL-Dokument für diesen KI-Agenten.

Agent:
- Name: ${expert.name}
- Rolle: ${expert.role}
- Skills: ${expert.skills || 'keine angegeben'}
- Ist Orchestrator/CEO: ${expert.isOrchestrator ? 'ja' : 'nein'}
- Unternehmen: ${company?.name || 'unbekannt'}
- Unternehmensziel: ${company?.goal || 'nicht definiert'}

Generiere ein SOUL mit genau diesen 4 Abschnitten. Antworte NUR mit diesem JSON, kein Text davor/danach:
{
  "identity": "2-3 Sätze: Wer bin ich? Was ist meine Kernaufgabe?",
  "principles": "4-5 Entscheidungsprinzipien als nummerierte Liste",
  "checklist": "5-6 Punkte als Bullet-Liste was der Agent bei jedem Wakeup tut",
  "personality": "2-3 Sätze über Kommunikationsstil und Persönlichkeit"
}`;

    const anthropicKeyRaw = db.select().from(settings).where(eq(settings.key, 'anthropic_api_key')).get()?.value;
    const anthropicKey = anthropicKeyRaw ? decryptSetting('anthropic_api_key', anthropicKeyRaw) : null;

    let generated: any = null;

    if (anthropicKey) {
      const r = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-api-key': anthropicKey, 'anthropic-version': '2023-06-01' },
        body: JSON.stringify({ model: 'claude-haiku-4-5-20251001', max_tokens: 1000, messages: [{ role: 'user', content: prompt }] }),
      });
      if (r.ok) {
        const d = await r.json() as any;
        const text = d.content?.[0]?.text || '';
        const m = text.match(/\{[\s\S]*\}/);
        if (m) { try { generated = JSON.parse(m[0]); } catch { /* ignore */ } }
      }
    }

    if (!generated) {
      const orKeyRaw = db.select().from(settings).where(eq(settings.key, 'openrouter_api_key')).get()?.value;
      const orKey = orKeyRaw ? decryptSetting('openrouter_api_key', orKeyRaw) : null;
      if (orKey) {
        const r = await fetch('https://openrouter.ai/api/v1/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${orKey}`, 'HTTP-Referer': 'http://localhost:3200', 'X-Title': 'OpenCognit SOUL' },
          body: JSON.stringify({ model: 'openrouter/auto', messages: [{ role: 'user', content: prompt }], max_tokens: 1000 }),
        });
        if (r.ok) {
          const d = await r.json() as any;
          const text = d.choices?.[0]?.message?.content || '';
          const m = text.match(/\{[\s\S]*\}/);
          if (m) { try { generated = JSON.parse(m[0]); } catch { /* ignore */ } }
        }
      }
    }

    if (!generated) {
      generated = isEn ? {
        identity: `I am ${expert.name}, ${expert.role} at ${company?.name || 'our company'}. My main task is to ${expert.skills ? `bring expertise in ${expert.skills.split(',')[0].trim()}` : 'professionally handle my assigned tasks'} and contribute to the company goal.`,
        principles: `1. Quality over speed — thorough beats fast\n2. Escalate blockers immediately, don't wait\n3. Document every decision\n4. When in doubt, ask the CEO\n5. Always formulate results clearly and measurably`,
        checklist: `- Check inbox and read all new messages\n- Review active tasks and assess status\n- Identify blockers and report immediately\n- Document progress\n- Define next steps`,
        personality: `Direct, solution-oriented and professional. Communicate clearly without filler. Take responsibility for results.`,
      } : {
        identity: `Ich bin ${expert.name}, ${expert.role} bei ${company?.name || 'unserem Unternehmen'}. Meine Hauptaufgabe ist es, ${expert.skills ? `Expertise in ${expert.skills.split(',')[0].trim()} einzubringen` : 'meine zugewiesenen Aufgaben professionell zu erledigen'} und zum Unternehmensziel beizutragen.`,
        principles: `1. Qualität vor Geschwindigkeit — lieber gründlich als schnell\n2. Bei Blockern sofort eskalieren, nicht warten\n3. Jede Entscheidung dokumentieren\n4. Im Zweifel den CEO fragen\n5. Ergebnisse immer klar und messbar formulieren`,
        checklist: `- Inbox prüfen und alle neuen Nachrichten lesen\n- Aktive Tasks reviewen und Status bewerten\n- Blocker identifizieren und sofort melden\n- Fortschritt dokumentieren\n- Nächste Schritte definieren`,
        personality: `Direkt, lösungsorientiert und professionell. Kommuniziere klar und ohne Umschweife. Übernehme Verantwortung für Ergebnisse.`,
      };
    }

    res.json(generated);
  } catch (err: any) {
    console.error('SOUL generation failed:', err);
    res.status(500).json({ error: 'SOUL generation failed' });
  }
});

export default router;
