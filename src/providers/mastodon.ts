export type MastodonImage = { bytes: Uint8Array; mimeType: string };

/**
 * Direct Mastodon posting is currently routed via Zapier in this project.
 * This stub keeps the types happy and avoids Node/Blob/FormData mismatches.
 */
export async function postToMastodon(
  _text: string,
  _image?: MastodonImage
): Promise<void> {
  // no-op: use Zapier relay instead
  return;
}
