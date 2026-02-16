# システムアーキテクチャ

## 全体構成

```
[ブラウザ]
    │
    │ HTTPS
    ▼
[React + Vite]  ──Proxy /api/*──▶  [Flask API]
  :5174                               :5001
                                        │
                            ┌───────────┼───────────┐
                            │           │           │
                            ▼           ▼           ▼
                       [MySQL 8.0] [Redis 7]  [Claude API]
                        :3306       :6379      (Anthropic)
```

## ローカル開発環境（Docker Compose）

| Service | Image | Port | 用途 |
|---------|-------|------|------|
| frontend | Node 20 | 5174 | Vite開発サーバー + APIプロキシ |
| backend | Python 3.12 | 5001→5000 | Flask APIサーバー |
| db | MySQL 8.0 | 3306 | データベース |
| redis | Redis 7 Alpine | 6379 | レート制限 |

## 本番環境（GCP）

```
[ブラウザ]
    │
    │ HTTPS
    ▼
[Cloud Run]  ──VPC Connector──▶  [Cloud SQL (MySQL 8.0)]
  (Frontend + Backend)              Private IP Only
  0〜5 instances                    db-f1-micro
  1 vCPU / 512Mi                    IAM認証
    │
    │ HTTPS
    ▼
[Claude API]
  (Anthropic)
```

### GCPリソース

| リソース | サービス | 説明 |
|---------|---------|------|
| アプリケーション | Cloud Run | フロントエンド＋バックエンド統合コンテナ |
| データベース | Cloud SQL | MySQL 8.0, Private IP, IAM認証 |
| マイグレーション | Cloud Run Job | デプロイ前に自動実行 |
| コンテナレジストリ | Artifact Registry | asia-northeast1 |
| シークレット | Secret Manager | JWT/Flask秘密鍵 |
| ネットワーク | VPC + Connector | Private接続用 |

## CI/CD

```
[GitHub PR]  ──trigger──▶  [CI Workflow]
                              ├─ lint-frontend
                              ├─ test-frontend
                              ├─ lint-backend
                              ├─ test-backend
                              ├─ format-check
                              └─ security

[Git Tag v*]  ──trigger──▶  [Deploy Workflow]
                              ├─ CI (全チェック)
                              ├─ Terraform outputs取得
                              ├─ Docker build + push
                              ├─ Migration Job実行
                              ├─ Cloud Run deploy
                              ├─ Health check
                              └─ GitHub Release作成

[infra/terraform/** 変更]  ──trigger──▶  [Terraform Workflow]
                                          ├─ Plan (PR時)
                                          └─ Apply (main push時)
```

## バックエンドレイヤー構成

```
Routes (Blueprint)
  │  リクエスト検証、レスポンス生成
  ▼
Services
  │  ビジネスロジック、ドメイン例外
  ▼
Repositories
  │  SQLAlchemyクエリ、データアクセス
  ▼
Models (ORM)
```

## 認証フロー

```
[ログイン]
  POST /api/auth/login
    → JWT access_token (httpOnly Cookie, 24時間)
    → JWT refresh_token (httpOnly Cookie, 7日)

[API呼び出し]
  Cookie自動送信 → @require_auth デコレーター → g.user_id 設定

[トークン更新]
  POST /api/auth/refresh → 新しい access_token 発行
```
