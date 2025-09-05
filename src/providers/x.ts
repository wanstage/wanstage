import { TwitterApi } from 'twitter-api-v2';

export async function postToX(text: string) {
  const { X_APP_KEY, X_APP_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET } =
    process.env;

  if (!X_APP_KEY || !X_APP_SECRET || !X_ACCESS_TOKEN || !X_ACCESS_SECRET) {
    throw new Error('X_* secrets are missing');
  }

  const client = new TwitterApi({
    appKey: X_APP_KEY,
    appSecret: X_APP_SECRET,
    accessToken: X_ACCESS_TOKEN,
    accessSecret: X_ACCESS_SECRET,
  });

  const { data } = await client.v2.tweet(text);
  return data;
}
