# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクトの目的

Claude APIを活用したAIチャットアプリケーション。リアルタイムストリーミング会話、会話履歴管理、ユーザー認証、管理者ダッシュボードを提供する。

## 設計原則

- **Clean Architecture**: 依存は内側に向かう（Routes → Services → Repositories → Models）。インフラコードは外縁に配置
- **JWT認証**: httpOnly Cookieによる自動送信（XSS対策）
- **全APIルートは `/api` プレフィックス**: JSON request/response
- **テスト**: バックエンドはpytest + SQLite in-memory、フロントエンドはVitest + Testing Library

## 技術スタック

Full-stack monorepo. Docker Compose for local development.

| Layer | Frontend | Backend |
|-------|----------|---------|
| Framework | React 18 + Vite | Flask 2.x |
| Language | TypeScript | Python 3.12 |
| ORM/Validation | - | SQLAlchemy 2.x + Pydantic v2 |
| Database | - | MySQL 8.0 |

## ディレクトリ構成

```
.
├── backend/             # Flask + SQLAlchemy backend
│   ├── app/            #   routes/, services/, repositories/, models/, schemas/
│   ├── scripts/        #   DB管理スクリプト
│   └── tests/          #   pytest テスト
├── frontend/            # React + TypeScript frontend
│   └── src/            #   pages/, components/, hooks/, contexts/, lib/api/
├── infra/               # インフラ構成
│   ├── docker-compose.yml
│   ├── mysql/          #   init SQL, migrations
│   └── terraform/      #   GCP Terraform
├── specs/               # 機能仕様書（archive/）
└── .claude/             # Claude Code設定
    ├── agents/         #   サブエージェント定義
    ├── commands/       #   スラッシュコマンド
    └── skills/         #   スキル定義
```

## 開発クイックスタート

```bash
make install              # 全依存関係のインストール
make up                   # 全サービス起動 (frontend :5174, backend :5001, MySQL, Redis)
make down                 # 全サービス停止
make test                 # 全テスト実行（カバレッジ付き）
make lint                 # 全リンター実行
make format               # 全コードフォーマット
```

全コマンド一覧: `make help`

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/): `<type>(<scope>): <subject>`

例: `feat(chat): add streaming support`, `fix(auth): handle expired tokens`

## ブラウザテスト (Playwright MCP)

`make up` → `mcp__playwright__browser_navigate` (`http://localhost:5174`) → `mcp__playwright__browser_snapshot` → 操作・検証。テスト時のパスワード: `Test123!`

## ドキュメント

### 実装ガイド

| ドキュメント | 内容 |
|------------|------|
| [backend/CLAUDE.md](backend/CLAUDE.md) | バックエンド実装ガイド（アーキテクチャ、パターン、ロギング、DB設定） |
| [frontend/CLAUDE.md](frontend/CLAUDE.md) | フロントエンド実装ガイド（コンポーネント、UI、テスト、ロギング） |

### プロジェクトドキュメント

| ドキュメント | 内容 |
|------------|------|
| [docs/00_development.md](docs/00_development.md) | 環境構築手順書 |
| [docs/01_feature-list.md](docs/01_feature-list.md) | 機能一覧 |
| [docs/02_screen-list.md](docs/02_screen-list.md) | 画面一覧 |
| [docs/03_database-design.md](docs/03_database-design.md) | データベース設計 |
| [docs/04_system-architecture.md](docs/04_system-architecture.md) | システムアーキテクチャ |
| [docs/05_e2e-test-cases.md](docs/05_e2e-test-cases.md) | E2Eテストケース一覧 |
