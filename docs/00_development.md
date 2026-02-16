# 環境構築手順書

## 前提条件

| ツール | バージョン | 確認コマンド |
|--------|-----------|-------------|
| Node.js | 20+ | `node --version` |
| Python | 3.12+ | `python3 --version` |
| Docker | 最新 | `docker --version` |
| pnpm | 最新 | `pnpm --version` |
| Poetry | 最新 | `poetry --version` |

環境チェック: `make doctor`

## セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd fullstack-agent-app-with-claude
```

### 2. 環境変数ファイルの作成

```bash
cp infra/.env.example infra/.env.development
```

`infra/.env.development` を編集し、以下を設定:

| 変数名 | 説明 | 必須 |
|--------|------|------|
| `ANTHROPIC_API_KEY` | Anthropic APIキー（`sk-ant-...`） | 必須 |
| `MYSQL_ROOT_PASSWORD` | MySQL rootパスワード（デフォルト: `rootpassword123`） | 任意 |
| `MYSQL_PASSWORD` | MySQL アプリユーザーパスワード（デフォルト: `apppassword123`） | 任意 |
| `REDIS_PASSWORD` | Redisパスワード（デフォルト: `redispassword123`） | 任意 |

> **Note**: `ANTHROPIC_API_KEY` 以外の変数はデフォルト値が設定済みのため、ローカル開発ではそのままで動作します。

### 3. 依存関係のインストール

```bash
make install
```

### 4. サービスの起動

```bash
make up
```

起動するサービス:

| Service | URL | 説明 |
|---------|-----|------|
| frontend | http://localhost:5174 | Vite開発サーバー |
| backend | http://localhost:5001 | Flask API |
| db | localhost:3306 | MySQL 8.0 |
| redis | localhost:6379 | レート制限用 |

### 5. テストユーザーの作成

```bash
make db-create-user EMAIL=admin@example.com PASSWORD=Test123!
```

### 6. 動作確認

```bash
make health
```

ブラウザで http://localhost:5174 にアクセスし、ログイン画面が表示されればOK。

## よく使うコマンド

| コマンド | 説明 |
|---------|------|
| `make up` | 全サービス起動 |
| `make down` | 全サービス停止 |
| `make test` | 全テスト実行（カバレッジ付き） |
| `make lint` | 全リンター実行 |
| `make format` | 全コードフォーマット |
| `make db-reset` | データベース完全リセット |
| `make health` | サービスヘルスチェック |

全コマンド一覧: `make help`
