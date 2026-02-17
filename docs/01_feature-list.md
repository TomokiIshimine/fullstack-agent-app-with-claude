# 機能一覧

## 一覧

| 機能ID | 機能名 | 説明 | 関連画面 | 関連API | ステータス |
|--------|--------|------|----------|---------|-----------|
| F001 | ログイン | メール/パスワードでJWT Cookie認証 | S001 | POST /api/auth/login | 実装済み |
| F002 | ログアウト | トークン無効化＋Cookie削除 | 全画面（Navbar） | POST /api/auth/logout | 実装済み |
| F003 | トークン自動更新 | アクセストークンの自動リフレッシュ | - | POST /api/auth/refresh | 実装済み |
| F004 | AIチャット | Claude APIによるリアルタイムストリーミング会話 | S002 | POST /api/conversations, POST /api/conversations/{uuid}/messages | 実装済み |
| F005 | 会話履歴管理 | 会話の一覧表示・詳細表示・削除 | S002 | GET /api/conversations, GET /api/conversations/{uuid}, DELETE /api/conversations/{uuid} | 実装済み |
| F006 | ツール呼び出し表示 | AIのツール呼び出し過程の表示 | S002 | - (SSEイベントで配信) | 実装済み |
| F007 | Markdownレンダリング | AIレスポンスのMarkdown＋コードハイライト表示 | S002 | - | 実装済み |
| F008 | プロフィール編集 | 名前の更新 | S003 | PATCH /api/users/me | 実装済み |
| F009 | パスワード変更 | 現在のパスワード確認＋新パスワード設定 | S003 | POST /api/password/change | 実装済み |
| F010 | ユーザー管理（Admin） | ユーザーの一覧・作成・削除・パスワードリセット | S004 | GET/POST /api/users, DELETE /api/users/{id}, POST /api/users/{id}/reset-password | 実装済み |
| F011 | ダッシュボード（Admin） | 統計サマリー・トレンドチャート・ランキング | S005 | GET /api/admin/dashboard/summary, trends, rankings | 実装済み |
| F012 | 会話履歴閲覧（Admin） | 全ユーザーの会話履歴を閲覧・フィルタリング | S006 | GET /api/admin/conversations, GET /api/admin/conversations/{uuid} | 実装済み |
| F013 | レート制限 | APIエンドポイントのリクエスト制限 | - | 全エンドポイント | 実装済み |
| F014 | ヘルスチェック | アプリケーション・DB状態確認 | - | GET /api/health | 実装済み |
| F015 | ロールベースアクセス制御 | Admin/Userロールによるアクセス制御 | 全画面 | 全エンドポイント | 実装済み |
| F016 | 送信ショートカットキー設定 | メッセージ送信キーをEnterまたはCtrl+Enter(Cmd+Enter)から選択 | S003, S002 | GET/PATCH /api/users/me/settings | 実装済み |
