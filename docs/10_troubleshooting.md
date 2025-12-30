# トラブルシューティングガイド

開発環境のセットアップや実行時によくある問題と解決策をまとめています。

## 目次

1. [環境セットアップの問題](#環境セットアップの問題)
2. [Docker関連の問題](#docker関連の問題)
3. [データベース関連の問題](#データベース関連の問題)
4. [フロントエンド関連の問題](#フロントエンド関連の問題)
5. [バックエンド関連の問題](#バックエンド関連の問題)
6. [認証関連の問題](#認証関連の問題)

---

## 環境セットアップの問題

### Node.js がインストールされていない / バージョンが古い

**症状**: `make doctor` で Node.js が ❌ または ⚠️ と表示される

**解決策**:
```bash
# nvm を使用する場合
nvm install 20
nvm use 20

# 直接インストールする場合
# https://nodejs.org/ から LTS 版をダウンロード
```

### Python がインストールされていない / バージョンが古い

**症状**: `make doctor` で Python が ❌ または ⚠️ と表示される

**解決策**:
```bash
# pyenv を使用する場合
pyenv install 3.12
pyenv local 3.12

# Mac (Homebrew)
brew install python@3.12

# Ubuntu/Debian
sudo apt update && sudo apt install python3.12
```

### pnpm がインストールされていない

**症状**: `make doctor` で pnpm が ❌ と表示される

**解決策**:
```bash
npm install -g pnpm
```

### Poetry がインストールされていない

**症状**: `make doctor` で Poetry が ❌ と表示される

**解決策**:
```bash
# 公式インストーラー (推奨)
curl -sSL https://install.python-poetry.org | python3 -

# pipx を使用する場合
pipx install poetry
```

### 環境変数ファイルがない

**症状**: `make doctor` で `infra/.env.development` が ❌ と表示される

**解決策**:
```bash
cp infra/.env.example infra/.env.development
# 必要に応じてパスワード等を編集
```

---

## Docker関連の問題

### Docker が起動していない

**症状**:
- `make doctor` で Docker が「Installed but not running」と表示される
- `make up` で接続エラー

**解決策**:
```bash
# Docker Desktop を起動
# または Linux の場合:
sudo systemctl start docker
```

### ポートが使用中

**症状**: `make up` でポート競合エラー
```
Error: bind: address already in use
```

**解決策**:

| サービス | ポート | 確認コマンド |
|---------|--------|-------------|
| Frontend | 5174 | `lsof -i :5174` |
| Backend | 5001 | `lsof -i :5001` |
| MySQL | 3306 | `lsof -i :3306` |
| Redis | 6379 | `lsof -i :6379` |

```bash
# プロセスを終了
kill -9 <PID>

# または、ローカルの MySQL/Redis を停止
brew services stop mysql
brew services stop redis
```

### コンテナがクラッシュする

**症状**: `make health` でサービスが ❌ と表示される

**解決策**:
```bash
# ログを確認
docker compose -f infra/docker-compose.yml logs backend
docker compose -f infra/docker-compose.yml logs frontend

# コンテナを再作成
make down
docker compose -f infra/docker-compose.yml build --no-cache
make up
```

### ボリュームのデータが壊れている

**症状**: データベースエラーやRedisエラーが発生

**解決策**:
```bash
# ⚠️ 注意: データが削除されます
make down
docker volume rm infra_mysql-data infra_redis-data
make up
make db-init
```

---

## データベース関連の問題

### データベースに接続できない

**症状**:
- バックエンドログに `Can't connect to MySQL server` と表示
- `make health` で DB が disconnected と表示

**解決策**:
```bash
# 1. MySQL コンテナの状態を確認
docker compose -f infra/docker-compose.yml ps db

# 2. MySQL が healthy になるまで待つ (最大60秒)
docker compose -f infra/docker-compose.yml logs -f db

# 3. 手動で接続テスト
docker compose -f infra/docker-compose.yml exec db \
  mysql -u app_user -p'example-password' -e "SELECT 1"
```

### テーブルが存在しない

**症状**: `relation "users" does not exist` などのエラー

**解決策**:
```bash
make db-init
```

### マイグレーションエラー

**症状**: テーブル構造の不整合

**解決策**:
```bash
# データベースを完全にリセット (⚠️ データ削除)
make db-reset
make db-init
```

---

## フロントエンド関連の問題

### 依存関係のインストールエラー

**症状**: `make install` で pnpm エラー

**解決策**:
```bash
# node_modules を削除して再インストール
rm -rf frontend/node_modules frontend/pnpm-lock.yaml
pnpm --dir frontend install
```

### Vite 開発サーバーが起動しない

**症状**: `http://localhost:5174` にアクセスできない

**解決策**:
```bash
# コンテナログを確認
docker compose -f infra/docker-compose.yml logs frontend

# よくある原因:
# - node_modules がマウントされていない → make down && make up
# - ポート 5174 が使用中 → lsof -i :5174 で確認
```

### Hot Reload が動作しない

**症状**: ファイルを変更しても画面が更新されない

**解決策**:
1. ブラウザのキャッシュをクリア
2. 開発者ツールで「キャッシュを無効化」をオン
3. コンテナを再起動: `make down && make up`

### API リクエストが失敗する

**症状**: ネットワークエラー、CORS エラー

**解決策**:
```bash
# バックエンドが起動しているか確認
make health

# プロキシ設定を確認
# frontend/vite.config.ts の proxy 設定が正しいか確認
```

---

## バックエンド関連の問題

### Poetry の依存関係エラー

**症状**: `make install` で Poetry エラー

**解決策**:
```bash
# lock ファイルを更新
cd backend
poetry lock --no-update
poetry install
```

### Flask が起動しない

**症状**: `http://localhost:5001/health` にアクセスできない

**解決策**:
```bash
# ログを確認
docker compose -f infra/docker-compose.yml logs backend

# よくある原因:
# - DATABASE_URL が間違っている
# - MySQL が起動していない
# - 依存関係のインポートエラー
```

### インポートエラー

**症状**: `ModuleNotFoundError` または `ImportError`

**解決策**:
```bash
# コンテナ内で依存関係を再インストール
docker compose -f infra/docker-compose.yml exec backend poetry install
```

---

## 認証関連の問題

### ログインできない

**症状**: 正しい認証情報でもログインに失敗する

**解決策**:
```bash
# 1. ユーザーが存在するか確認
docker compose -f infra/docker-compose.yml exec db \
  mysql -u app_user -p'example-password' app_db \
  -e "SELECT email FROM users"

# 2. テストユーザーを作成
make db-create-user EMAIL=test@example.com PASSWORD=Test123!
```

### Cookie が保存されない

**症状**: ログイン後すぐにログアウトされる

**解決策**:
1. ブラウザの Cookie 設定を確認
2. `http://localhost:5174` でアクセスしているか確認（IP アドレスではなく）
3. シークレットモードで試す

### JWT トークンエラー

**症状**: `Token has expired` や `Invalid token` エラー

**解決策**:
1. ブラウザの Cookie を削除
2. 再ログイン
3. バックエンドの `JWT_SECRET_KEY` 環境変数が設定されているか確認

---

## その他のヒント

### ログの確認方法

```bash
# 全サービスのログ
docker compose -f infra/docker-compose.yml logs -f

# 特定のサービスのログ
docker compose -f infra/docker-compose.yml logs -f backend

# 直近100行のみ
docker compose -f infra/docker-compose.yml logs --tail=100 backend
```

### 完全なリセット

すべてを最初からやり直す場合:

```bash
# 1. すべてのコンテナとボリュームを削除
make down
docker volume rm infra_mysql-data infra_redis-data

# 2. 依存関係を再インストール
rm -rf frontend/node_modules backend/.venv
make install

# 3. サービスを起動
make up

# 4. データベースを初期化
make db-init

# 5. テストユーザーを作成
make db-create-user EMAIL=test@example.com PASSWORD=Test123!
```

### サポートを求める前に

問題を報告する際は、以下の情報を含めてください:

1. `make doctor` の出力
2. `make health` の出力
3. 関連するエラーログ (`docker compose logs <service>`)
4. OS とバージョン
5. 実行したコマンドとその結果
