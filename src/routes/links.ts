import { Router } from 'express';
import {
  getLinksPaginated,
  updateLinkUrl,
  updateTags,
  deleteLink,
  getLink,
} from '../db';

const router = Router();

/**
 * GET /api/links?from=YYYY-MM-DD&to=YYYY-MM-DD&limit=50&cursor=<created_at>&q=keyword
 * 返り値: { data:[{code,url,tags,created_at,clicks}], next:"<created_at>|null" }
 */
router.get('/', (req, res) => {
  const { from, to, limit, cursor, q } = req.query as Record<
    string,
    string | undefined
  >;
  const parsed = {
    from,
    to,
    cursor,
    q,
    limit: limit ? parseInt(limit) : undefined,
  };
  const result = getLinksPaginated(parsed);
  res.json(result);
});

/** PUT /api/links/:code  body: { url } */
router.put('/:code', (req, res) => {
  const code = req.params.code;
  const url = (req.body?.url ?? '').toString().trim();
  if (!url) return res.status(400).json({ error: 'url required' });
  const ok = updateLinkUrl(code, url);
  if (!ok) return res.status(404).json({ error: 'not found' });
  res.json({ ok: true, link: getLink(code) });
});

/** PATCH /api/links/:code/tags  body: { op: "add"|"remove"|"replace", tags: string[] } */
router.patch('/:code/tags', (req, res) => {
  const code = req.params.code;
  const op = (req.body?.op ?? '').toString() as 'add' | 'remove' | 'replace';
  const tags = Array.isArray(req.body?.tags)
    ? req.body.tags.map((s: any) => String(s))
    : [];
  if (!['add', 'remove', 'replace'].includes(op) || !Array.isArray(tags))
    return res
      .status(400)
      .json({ error: 'op(add|remove|replace) and tags[] required' });
  const ok = updateTags(code, op, tags);
  if (!ok) return res.status(404).json({ error: 'not found' });
  res.json({ ok: true, link: getLink(code) });
});

/** DELETE /api/links/:code */
router.delete('/:code', (req, res) => {
  const ok = deleteLink(req.params.code);
  if (!ok) return res.status(404).json({ error: 'not found' });
  res.json({ ok: true });
});

export default router;
