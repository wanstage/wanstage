import { sqliteTable, integer, text } from 'drizzle-orm/sqlite-core';

export const links = sqliteTable('links', {
  code: text('code').primaryKey(),
  url: text('url').notNull(),
  tags: text('tags').default(''),
  createdAt: text('created_at').notNull(),
});

export const clicks = sqliteTable('clicks', {
  code: text('code').notNull(),
  ts: text('ts').notNull(),
});
