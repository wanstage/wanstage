export type FormatOpts = {
  datePrefix?: boolean;
  hashtags?: string;
  tz?: string;
};

export function formatMessage(base: string, opts: FormatOpts = {}): string {
  const tz = opts.tz || process.env.TZ || 'Asia/Tokyo';
  let msg = base;

  if (opts.datePrefix) {
    const stamp = new Date().toLocaleString('ja-JP', { timeZone: tz });
    msg = `[${stamp}] ${msg}`;
  }

  const tags = (opts.hashtags || process.env.HASHTAGS || '')
    .split(/[,\s]+/)
    .map((t) => t.trim())
    .filter(Boolean);

  if (tags.length) {
    const hashLine = tags
      .map((t) => (t.startsWith('#') ? t : `#${t}`))
      .join(' ');
    msg = `${msg} ${hashLine}`.trim();
  }
  return msg;
}
