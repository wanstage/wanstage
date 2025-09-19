import type { Request, Response, NextFunction } from 'express';

export function requireApiKey(req: Request, res: Response, next: NextFunction) {
  const expected = process.env.API_KEY || 'changeme-api-key';
  const got = req.header('x-api-key');
  if (!expected || got === expected) return next();
  res.status(401).json({ error: 'unauthorized' });
}
