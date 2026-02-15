# Frontend Guide

React + TypeScript フロントエンドの実装ガイド。

## アーキテクチャ

### ビルドシステム

Vite + TypeScript。`@` エイリアスが `src/` を指す（`vite.config.ts`）。

### APIプロキシ

Vite dev serverが `/api/*` をバックエンドにプロキシ。`VITE_API_PROXY` 環境変数で設定（デフォルト: `http://localhost:5000`）。

### コンポーネント構成

```
src/
├── pages/           # ページコンポーネント（LoginPage.tsx 等）
│   └── admin/       # 管理者ページ
├── components/
│   ├── ui/          # 共有UIライブラリ（Button, Input, Alert, Modal）
│   ├── admin/       # 管理者コンポーネント
│   ├── chat/        # チャットコンポーネント
│   └── settings/    # 設定コンポーネント
├── contexts/        # React Context（AuthContext.tsx）
├── hooks/           # カスタムフック（useChat, useConversations 等）
├── lib/api/         # APIクライアント
├── types/           # TypeScript型定義
├── styles/          # CSSファイル
├── App.tsx          # ルートコンポーネント（ルーティング）
└── main.tsx         # エントリーポイント
```

### 命名規則

- **ページ**: `<Feature>Page.tsx`（例: `LoginPage.tsx`）
- **コンポーネント**: PascalCase `<Name>.tsx`
- **ユーティリティ**: camelCase `name.ts`
- **テスト**: `<Name>.test.tsx`
- 1ファイル1コンポーネント

## UIライブラリ (`components/ui/`)

Tailwind CSSベースの共有UIコンポーネント。詳細なProps定義はソースコードを参照。

- **Button**: variant(primary/secondary/danger/success), size(sm/md/lg), loading状態
- **Input**: label, error表示, パスワード表示切替, CAPS LOCK検出
- **Alert**: variant(success/error/warning/info), autoClose, retry
- **Modal**: size(sm/md/lg), ESCで閉じる, 外側クリックで閉じる

## スタイリング

- **Tailwind CSS優先**: カスタムCSSクラスよりユーティリティクラスを使用
- **カラー**: Primary=blue, Danger=red, Success=emerald, Warning=amber, Neutral=slate
- **アクセシビリティ**: 最小タップターゲット44px, ARIA属性, フォーカスリング, セマンティックHTML

## テスト

Vitest + Testing Library。テスト設定は `vitest.config.ts`。

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
```

## コードスタイル

- **Prettier**: 幅100文字, セミコロンなし, シングルクォート, trailing comma=es5
- **ESLint**: `@typescript-eslint` + `eslint-plugin-react`, max-warnings=0
- **TypeScript**: Props型は `interface`、Union型は `type`、`React.FC<Props>` 推奨

## 開発コマンド

```bash
pnpm --dir frontend run dev --host 0.0.0.0 --port 5174  # 開発サーバー
pnpm --dir frontend run test                              # テスト実行
pnpm --dir frontend run test:coverage                     # カバレッジ付き
pnpm --dir frontend run lint                              # リント
pnpm --dir frontend run format                            # フォーマット
pnpm --dir frontend run build                             # ビルド
pnpm --dir frontend add <package>                         # 依存追加
pnpm --dir frontend add -D <package>                      # dev依存追加
```

## ロギング

`lib/logger.ts` に実装。詳細はソースコードを参照。

- **環境別動作**: development=DEBUG, production=WARN, testing=抑制
- **APIロギング**: `fetchWithLogging` ラッパーで自動記録（リクエスト/レスポンス/タイミング）
- **機密データマスキング**: password, token, api_key 等を自動マスク
- **グローバルエラー**: `window.onerror`, `unhandledrejection`, React ErrorBoundary
- **使い方**: `import { logger } from '@/lib/logger'`

## 環境変数

`frontend/.env` で設定（`VITE_` プレフィックス必須）:

```env
VITE_API_PROXY=http://localhost:5000
VITE_LOG_LEVEL=DEBUG
VITE_ENABLE_API_LOGGING=true
```

## 新機能実装パターン

1. **Types** (`types/`) → TypeScript型定義
2. **API Client** (`lib/api/`) → fetch関数
3. **Hook** (`hooks/`) → 状態管理・API呼び出し
4. **Component** (`components/`) → UIコンポーネント
5. **Page** (`pages/`) → ページ組み立て
6. **Test** (`*.test.tsx`) → Vitest + Testing Library

既存実装を参照: 認証(`auth`), チャット(`chat`), 管理者(`admin`)
