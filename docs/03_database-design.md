# データベース設計

## ER図

```
users 1──N refresh_tokens
  │
  1
  │
  N
conversations 1──N messages 1──N tool_calls
```

## テーブル定義

### users

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | ユーザーID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | メールアドレス |
| password_hash | VARCHAR(255) | NOT NULL | bcryptハッシュ |
| role | ENUM('admin','user') | DEFAULT 'user' | ロール |
| name | VARCHAR(100) | NULLABLE | 表示名 |
| created_at | DATETIME | DEFAULT NOW() | 作成日時 |
| updated_at | DATETIME | DEFAULT NOW() ON UPDATE | 更新日時 |

インデックス: `idx_users_role(role)`

### refresh_tokens

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | トークンID |
| token | VARCHAR(500) | UNIQUE, NOT NULL | リフレッシュトークン |
| user_id | BIGINT | FK → users.id (CASCADE) | ユーザーID |
| expires_at | DATETIME | NOT NULL | 有効期限 |
| is_revoked | BOOLEAN | DEFAULT FALSE | 無効化フラグ |
| created_at | DATETIME | DEFAULT NOW() | 作成日時 |
| updated_at | DATETIME | DEFAULT NOW() ON UPDATE | 更新日時 |

インデックス: `idx_refresh_tokens_token(token)`, `idx_refresh_tokens_user_id(user_id)`, `idx_refresh_tokens_expires_at(expires_at)`

### conversations

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 会話ID |
| uuid | VARCHAR(36) | UNIQUE, NOT NULL | 外部公開用UUID |
| user_id | BIGINT | FK → users.id (CASCADE) | 所有ユーザーID |
| title | VARCHAR(255) | NOT NULL | 会話タイトル |
| created_at | DATETIME | DEFAULT NOW() | 作成日時 |
| updated_at | DATETIME | DEFAULT NOW() ON UPDATE | 更新日時 |

インデックス: `idx_conversations_user_id(user_id)`, `idx_conversations_updated_at(updated_at)`

### messages

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | メッセージID |
| conversation_id | BIGINT | FK → conversations.id (CASCADE) | 会話ID |
| role | ENUM('user','assistant') | NOT NULL | 送信者ロール |
| content | TEXT | NOT NULL | メッセージ本文 |
| input_tokens | INT UNSIGNED | NULLABLE | 入力トークン数（assistant のみ） |
| output_tokens | INT UNSIGNED | NULLABLE | 出力トークン数（assistant のみ） |
| model | VARCHAR(255) | NULLABLE | 使用モデル名（assistant のみ） |
| response_time_ms | INT UNSIGNED | NULLABLE | 応答時間ms（assistant のみ） |
| cost_usd | DECIMAL(10,6) | NULLABLE | コストUSD（assistant のみ） |
| created_at | DATETIME | DEFAULT NOW() | 作成日時 |

インデックス: `idx_messages_conversation_id(conversation_id)`, `idx_messages_created_at(created_at)`

### tool_calls

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | ツール呼び出しID |
| message_id | BIGINT | FK → messages.id (CASCADE) | メッセージID |
| tool_call_id | VARCHAR(64) | NOT NULL | ツール呼び出し識別子 |
| tool_name | VARCHAR(100) | NOT NULL | ツール名 |
| input | JSON | NOT NULL | 入力パラメータ |
| output | TEXT | NULLABLE | 出力結果 |
| error | TEXT | NULLABLE | エラー内容 |
| status | ENUM('pending','success','error') | DEFAULT 'pending' | 実行ステータス |
| started_at | DATETIME | DEFAULT NOW() | 開始日時 |
| completed_at | DATETIME | NULLABLE | 完了日時 |

インデックス: `idx_tool_calls_message_id(message_id)`, `idx_tool_calls_tool_call_id(tool_call_id)`

### schema_migrations

| カラム名 | 型 | 制約 | 説明 |
|---------|-----|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | マイグレーションID |
| filename | VARCHAR(255) | UNIQUE, NOT NULL | ファイル名 |
| checksum | VARCHAR(64) | NOT NULL | SHA256ハッシュ |
| applied_at | DATETIME | DEFAULT NOW() | 適用日時 |

## スキーマ管理

- **初期スキーマ**: `infra/mysql/init/001_init.sql`（Docker初回起動時に自動適用）
- **マイグレーション**: `infra/mysql/migrations/` 配下のSQLファイル
- **モデル定義**: `backend/app/models/`（SQLAlchemy ORM）

スキーマ変更時は、モデル・init SQL・マイグレーションSQLの3箇所を同期する。
