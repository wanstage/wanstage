## 同意と利用ポリシー

本ツールは **Google OAuth 2.0** を利用して YouTube Data API にアクセスします。
利用者は以下に同意した上で本ツールを実行してください：

- アクセス権限は `youtube.upload` のみに限定されます
- 取得した認可情報（アクセストークン／リフレッシュトークン）はローカルの `.env.youtube` に保存されます
- 当該ファイルは利用者の責任において安全に管理してください
- 本ツールは Google API 利用規約および [YouTube API サービス規約](https://developers.google.com/youtube/terms/api-services-terms-of-service?hl=ja) に従って利用されます
- 利用を停止する場合、下記の `logout` コマンドで認可情報を無効化し、ローカルファイルを削除してください
