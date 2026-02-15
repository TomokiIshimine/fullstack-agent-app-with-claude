# Full Stack App Monorepo

React + TypeScript フロントエンドと Flask + SQLAlchemy バックエンドを含むフルスタックモノレポです。ユーザー認証機能を持つWebアプリケーションを実装しており、Docker Compose を使用した MySQL によるローカル開発環境を提供しています。

## ディレクトリ構造

```
.
├── frontend/          # React + TypeScript クライアントアプリケーション
├── backend/           # Flask API サーバーとバックエンドコード
│   └── scripts/       # データベース管理などの運用スクリプト
├── infra/             # Infrastructure as Code、デプロイスクリプト、運用ツール
├── docs/              # プロジェクトドキュメント
└── specs/             # 仕様書
```

## ドキュメント

包括的なドキュメントは `docs/` ディレクトリに用意されています。

| ドキュメント | 内容 |
|------------|------|
| [docs/00_development.md](docs/00_development.md) | 環境構築手順書 |
| [docs/01_feature-list.md](docs/01_feature-list.md) | 機能一覧 |
| [docs/02_screen-list.md](docs/02_screen-list.md) | 画面一覧 |
| [docs/03_database-design.md](docs/03_database-design.md) | データベース設計 |
| [docs/04_system-architecture.md](docs/04_system-architecture.md) | システムアーキテクチャ |
| [docs/05_e2e-test-cases.md](docs/05_e2e-test-cases.md) | E2Eテストケース一覧 |

### 実装ガイド

詳細な実装ガイドは各ディレクトリの `CLAUDE.md` を参照してください：
- **[backend/CLAUDE.md](backend/CLAUDE.md)** - バックエンド実装規約
- **[frontend/CLAUDE.md](frontend/CLAUDE.md)** - フロントエンド実装規約
- **[CLAUDE.md](CLAUDE.md)** - プロジェクト共通ガイド

## クイックスタート

### セットアップとインストール

```bash
make install              # すべての依存関係をインストール（frontend: pnpm, backend: poetry）
make setup                # 完全な環境セットアップ
```

### スタックの起動

```bash
make up                   # Docker コンテナを起動（MySQL、frontend、backend）
make down                 # Docker コンテナを停止
```

全コマンド一覧: `make help`

## テスト

```bash
make test                 # すべてのテスト（frontend と backend）をカバレッジ付きで実行
make test-frontend        # frontend のテストのみ実行
make test-backend         # backend のテストのみ実行
make test-fast            # カバレッジなしでテスト実行（高速）
```

### 個別テストの実行

```bash
# Frontend - 特定のテストファイルを実行
pnpm --dir frontend run test src/lib/api/auth.test.ts

# Backend - 特定のテストファイルを実行
poetry -C backend run pytest backend/tests/routes/test_auth_routes.py

# Backend - 特定のテスト関数を実行
poetry -C backend run pytest backend/tests/routes/test_auth_routes.py::test_login_success
```

## データベース管理

```bash
make db-init              # すべてのテーブルを初期化/再作成
make db-create-user EMAIL=user@example.com PASSWORD=password123  # テストユーザーを作成
make db-reset             # データベースをリセット（破壊的 - すべてのデータを削除）
```

詳細なデータベーススキーマについては [docs/03_database-design.md](docs/03_database-design.md) を参照してください。

## Pre-commit フック

Pre-commit フックは各コミット前に軽量なチェック（フォーマット、リント）を実行します。重いチェック（mypy、pytest、vitest）は高速なコミットのため除外されています。

```bash
make pre-commit-install   # フックをインストール（clone 後に一度実行）
make pre-commit-run       # すべてのファイルに対してフックを手動実行
```

**注意:** 型チェックとテストはコミット時に実行されません。`make lint` と `make test` で手動実行してください。

## 環境変数設定

### Admin ユーザー設定（必須）

アプリケーションの初回起動時に、Admin ユーザーを作成するための環境変数を設定する必要があります。

`backend/.env` ファイルに以下を追加：

```env
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD_HASH=$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5UpCCaa70.MYW
```

**パスワードハッシュの生成方法:**

```bash
poetry -C backend run python backend/scripts/generate_admin_hash.py
```

**開発環境での簡易設定:**

平文パスワードを直接設定することもできます（自動的にハッシュ化されます）：

```env
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=YourSecurePassword123
```

詳細は `backend/.env.example` を参照してください。

### 本番環境デプロイ時の設定（GitHub Secrets）

GitHub Actions でのデプロイ時に、管理者アカウント情報を安全に設定できます。

| シークレット名 | 説明 | 例 |
|-------------|------|-----|
| `ADMIN_EMAIL` | 管理者のメールアドレス | `admin@example.com` |
| `ADMIN_PASSWORD_HASH` | 管理者のパスワード（bcryptハッシュ） | `$2b$12$LQv3...` |

## Docker Compose セットアップ

4つのサービスが Docker で実行されます：`frontend` (Node 20)、`backend` (Python 3.12)、`db` (MySQL 8.0)、`redis` (Redis 7)。サービスは `app-network` ブリッジネットワークで通信します。

詳細なアーキテクチャについては [docs/04_system-architecture.md](docs/04_system-architecture.md) を参照してください。

## プロジェクト規約

### コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) に従い、`<type>(<scope>): <subject>` の形式を使用します。

**例:**
- `feat(frontend): ユーザーダッシュボードを追加`
- `fix(backend): 空のペイロードを処理`

### コード構成

- **Backend**: Flask + SQLAlchemy のレイヤードアーキテクチャ（routes → services → models）
- **Frontend**: React + TypeScript with Vite、ページとコンポーネントで整理
- すべての API ルートは `/api` プレフィックスを使用
- Frontend は開発時に API リクエストを Backend にプロキシ

## 本番環境デプロイ

### Google Cloud SQL 対応

このアプリケーションは Google Cloud SQL への安全な接続をサポートしています。

**設定例:**
```env
USE_CLOUD_SQL_CONNECTOR=true
CLOUDSQL_INSTANCE=my-project:asia-northeast1:my-instance
DB_USER=my-service-account@my-project.iam
DB_NAME=app_db
ENABLE_IAM_AUTH=true
```

詳細な設定方法については `backend/app/config.py` を参照してください。
