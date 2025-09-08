import { Router } from 'express';
const r = Router();
r.get('/google/loginPath', (_req, res) =>
  res.json({ url: 'https://accounts.google.com/' })
);
export default r;
