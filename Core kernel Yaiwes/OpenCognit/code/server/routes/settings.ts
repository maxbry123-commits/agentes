import { Router } from 'express';
import { db } from '../db/client.js';
import { settings } from '../db/schema.js';
import { eq, and, inArray } from 'drizzle-orm';
import { decryptSetting, encryptSetting } from '../utils/crypto.js';
import { messagingService } from '../services/messaging.js';

const router = Router();
const now = () => new Date().toISOString();

router.get('/api/settings', (req, res) => {
  const uId = (req.query.unternehmenId as string) || '';
  try {
    const result = db.select().from(settings).where(inArray(settings.companyId, ['', uId])).all();
    const obj: Record<string, string> = {};
    const sorted = [...result].sort((a, b) => a.companyId.length - b.companyId.length);
    for (const e of sorted) {
      try {
        obj[e.key] = decryptSetting(e.key, e.value);
      } catch (decryptErr) {
        console.warn(`[Settings] Failed to decrypt ${e.key}:`, decryptErr);
        obj[e.key] = e.value;
      }
    }
    res.json(obj);
  } catch (err) {
    console.error('[Settings] Error loading settings:', err);
    res.status(500).json({ error: 'Failed to load settings' });
  }
});

router.put('/api/settings/:key', async (req, res) => {
  const key = req.params.key;
  const uId = req.body.unternehmenId || '';
  const wert = (req.body.value ?? req.body.wert ?? '') as string;

  if (key === 'telegram_bot_token' && wert) {
    try {
      const tgCheck = await fetch(`https://api.telegram.org/bot${wert}/getMe`);
      const tgData = await tgCheck.json() as any;
      if (!tgData.ok) {
        return res.status(400).json({ error: 'invalid_token', message: `Telegram bot token ungültig: ${tgData.description || 'Unauthorized'}` });
      }
      console.log(`[Telegram] Token validiert: @${tgData.result?.username}`);
    } catch (e: any) {
      return res.status(400).json({ error: 'validation_failed', message: `Telegram Validierung fehlgeschlagen: ${e.message}` });
    }
  }

  const wertToStore = encryptSetting(key as string, String(wert));

  const existing = db.select().from(settings)
    .where(and(eq(settings.key, key), eq(settings.companyId, uId)))
    .get();

  if (existing) {
    db.update(settings)
      .set({ value: wertToStore, updatedAt: now() })
      .where(and(eq(settings.key, key), eq(settings.companyId, uId)))
      .run();
  } else {
    db.insert(settings)
      .values({ key, companyId: uId, value: wertToStore, updatedAt: now() })
      .run();
  }

  if (key === 'telegram_bot_token') {
    messagingService.clearInvalidTokens();
  }

  res.json({ schluessel: key, unternehmenId: uId, wert });
});

export default router;
