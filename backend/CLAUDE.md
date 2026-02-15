# Backend Guide

Flask + SQLAlchemy バックエンドの実装ガイド。

## アーキテクチャ

### レイヤー構成

```
Routes (Blueprint)       リクエスト検証、レスポンス生成
  ↓
Services                 ビジネスロジック、ドメイン例外
  ↓
Repositories             SQLAlchemyクエリ、データアクセス
  ↓
Models (ORM)             テーブル定義
```

### セッション管理

- `get_session()` でリクエストスコープのセッションを取得
- `session_scope()` コンテキストマネージャでスクリプト/テスト用トランザクション管理
- Flask `g` オブジェクト経由、`teardown_appcontext` で自動コミット/ロールバック

### APIルート構成

- 全APIルートは `/api` プレフィックス（`app/routes/__init__.py`）
- 機能別Flask Blueprint（例: `auth_bp` → `/api/auth`）
- ルートはサービス層に委譲、直接的なビジネスロジックは書かない

## エラーハンドリング

### 例外階層 (`app/core/exceptions.py`)

- **ServiceError** → 基底例外
  - **AuthServiceError**: `InvalidCredentialsError`(401), `InvalidRefreshTokenError`(401)
  - **UserServiceError**: `UserAlreadyExistsError`(409), `UserNotFoundError`(404), `CannotDeleteAdminError`(403)
  - **ConversationServiceError**: `ConversationNotFoundError`(404), `ConversationAccessDeniedError`(403)
  - **PasswordServiceError**: `InvalidPasswordError`(401), `PasswordChangeFailedError`(500)

### サービスデコレーター (`app/routes/dependencies.py`)

`@with_auth_service`, `@with_user_service` 等がサービス注入＋ドメイン例外→HTTPレスポンス変換を担当。

### リクエストバリデーション

`@validate_request_body(PydanticSchema)` でJSONボディを検証し、`data` キーワード引数として注入。`ValidationError` は自動的に400応答に変換。

## コードスタイル

- **行長**: 150文字（Black, isort, flake8）
- **Python**: 3.12+
- **型ヒント**: 推奨（`disallow_untyped_defs=false`）
- **インポート順**: stdlib → third-party → first-party (`app`)
- **バリデーション**: Pydantic v2（`app/schemas/`）、`BaseModel` + `@field_validator`

## 開発コマンド

```bash
poetry -C backend run pytest                    # テスト実行
poetry -C backend run pytest tests/<path>       # 特定テスト
poetry -C backend run pytest --cov=app          # カバレッジ付き
poetry -C backend run flake8 app backend        # リント
poetry -C backend run mypy app                  # 型チェック
poetry -C backend run black app backend         # フォーマット
poetry -C backend run isort app backend         # インポートソート
poetry -C backend add <package>                 # 依存追加
poetry -C backend add --group dev <package>     # dev依存追加
```

## ロギング

`app/logger.py` に実装。詳細はソースコードを参照。

- **リクエストトレーシング**: UUID v4ベース、`g.request_id` に格納
- **機密データマスキング**: password, token, api_key, secret, authorization を自動マスク
- **環境別動作**: development=テキスト+DEBUG、testing=コンソールのみ、production=JSON+INFO
- **使い方**: `import logging; logger = logging.getLogger(__name__)`

## データベース設定

デフォルト接続: `mysql+pymysql://user:password@db:3306/app_db`

- **標準接続**: `DATABASE_URL` 環境変数
- **Cloud SQL Connector**: `USE_CLOUD_SQL_CONNECTOR=true` で有効化。詳細は `app/config.py` を参照

### スキーマ管理

| 方法 | 用途 | ファイル |
|------|------|---------|
| Docker初期化 | 新規環境 | `infra/mysql/init/001_init.sql` |
| SQLマイグレーション | 既存DB変更 | `infra/mysql/migrations/*.sql` |
| Pythonスクリプト | 開発/テスト | `scripts/create_tables.py` |

**スキーマ変更時**: モデル(`app/models/`)、init SQL、マイグレーションSQLの3箇所を同期。

### マイグレーション

```bash
poetry -C backend run python scripts/apply_sql_migrations.py  # ローカル適用
```

- `schema_migrations` テーブルで適用済み追跡（SHA256チェックサム）
- アルファベット順に実行、冪等性あり
- CI/CDでは `scripts/run_migrations.sh` が自動実行

## 新機能実装パターン

1. **Model** (`app/models/`) → SQLAlchemy ORM定義
2. **Schema** (`app/schemas/`) → Pydantic v2 リクエスト/レスポンス
3. **Repository** (`app/repositories/`) → データアクセス
4. **Service** (`app/services/`) → ビジネスロジック
5. **Route** (`app/routes/`) → Blueprint + デコレーター
6. **Test** (`tests/`) → pytest + SQLite in-memory

既存実装を参照: 認証(`auth`)、会話(`conversation`)、管理者(`admin_dashboard`)
