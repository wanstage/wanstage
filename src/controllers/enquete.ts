import { Router } from 'express';
const r = Router();
r.get('/', (_req, res) => res.json([]));
export default r;
