import React, { useState } from 'react';

type LinkItem = {
  code: string;
  url: string;
  tags: string[];
  created_at: string;
  clicks?: number;
};

async function fetchPaged(from?: string, to?: string, q?: string) {
  const API_KEY =
    (import.meta.env.VITE_API_KEY as string) || 'changeme-api-key';
  const base = new URL('/api/links', window.location.origin);
  if (from) base.searchParams.set('from', from);
  if (to) base.searchParams.set('to', to);
  if (q) base.searchParams.set('q', q);
  base.searchParams.set('limit', '200');

  const all: LinkItem[] = [];
  let cursor: string | undefined = undefined;

  while (true) {
    const url = new URL(base.toString());
    if (cursor) url.searchParams.set('cursor', cursor);
    const resp = await fetch(url.toString(), {
      headers: { 'x-api-key': API_KEY },
    });
    if (!resp.ok) throw new Error(`GET /api/links ${resp.status}`);
    const json = await resp.json();
    all.push(...(json.data as LinkItem[]));
    if (!json.next) break;
    cursor = json.next as string;
  }
  return all;
}

function toCsv(rows: LinkItem[]) {
  const esc = (s: any) => `"${String(s ?? '').replace(/"/g, '""')}"`;
  const header = ['code', 'url', 'tags', 'created_at', 'clicks']
    .map(esc)
    .join(',');
  const lines = rows.map((r) =>
    [r.code, r.url, (r.tags || []).join('|'), r.created_at, r.clicks ?? 0]
      .map(esc)
      .join(',')
  );
  return [header, ...lines].join('\n');
}

export default function LinksCsvExport() {
  const [from, setFrom] = useState<string>('');
  const [to, setTo] = useState<string>('');
  const [q, setQ] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const onExport = async () => {
    try {
      setBusy(true);
      const rows = await fetchPaged(
        from || undefined,
        to || undefined,
        q || undefined
      );
      const csv = toCsv(rows);
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      const stamp = new Date().toISOString().slice(0, 10);
      a.download = `links_${stamp}.csv`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      alert(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ padding: 16, display: 'grid', gap: 12 }}>
      <h2>Export Links CSV</h2>
      <label>
        From{' '}
        <input
          type="date"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
        />
      </label>
      <label>
        To{' '}
        <input type="date" value={to} onChange={(e) => setTo(e.target.value)} />
      </label>
      <label>
        Search{' '}
        <input
          placeholder="code/url/tags"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </label>
      <button onClick={onExport} disabled={busy}>
        {busy ? 'Exporting...' : 'Export CSV'}
      </button>
      <small>環境変数 VITE_API_KEY を設定しておくと便利です。</small>
    </div>
  );
}
