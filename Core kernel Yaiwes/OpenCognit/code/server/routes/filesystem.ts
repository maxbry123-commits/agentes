import { Router } from 'express';
import fs from 'fs';
import path from 'path';
import { authMiddleware } from '../middleware/auth.js';

const router = Router();

router.get('/api/fs/dirs', authMiddleware, (req: any, res) => {
  const requested = (req.query.path as string) || '';
  const home = process.env.HOME || process.env.USERPROFILE || '/home';
  const current = requested ? path.resolve(requested) : home;

  const projectRoot = path.resolve(process.cwd());
  const blocked = ['node_modules', 'src', 'server', '.git'].map(d => path.join(projectRoot, d));
  if (blocked.some(b => current.startsWith(b))) {
    return res.status(403).json({ error: 'This path is not browsable' });
  }

  if (!fs.existsSync(current) || !fs.statSync(current).isDirectory()) {
    return res.status(400).json({ error: 'Path does not exist or is not a folder' });
  }

  let dirs: { name: string; path: string }[] = [];
  try {
    dirs = fs.readdirSync(current, { withFileTypes: true })
      .filter(d => d.isDirectory() && !d.name.startsWith('.'))
      .map(d => ({ name: d.name, path: path.join(current, d.name) }))
      .sort((a, b) => a.name.localeCompare(b.name));
  } catch { /* permission denied etc. */ }

  const parent = path.dirname(current) !== current ? path.dirname(current) : null;
  res.json({ current, parent, home, dirs });
});

router.post('/api/fs/mkdir', authMiddleware, (req: any, res) => {
  const { path: dirPath } = req.body as { path?: string };
  if (!dirPath || !path.isAbsolute(dirPath)) return res.status(400).json({ error: 'Absolute path required' });

  const projectRoot = path.resolve(process.cwd());
  const blocked = ['node_modules', 'src', 'server', '.git'].map(d => path.join(projectRoot, d));
  if (blocked.some(b => path.resolve(dirPath).startsWith(b))) {
    return res.status(403).json({ error: 'Cannot create folder here' });
  }
  try {
    fs.mkdirSync(dirPath, { recursive: true });
    res.json({ ok: true, path: dirPath });
  } catch (e: any) {
    res.status(500).json({ error: e.message });
  }
});

export default router;
