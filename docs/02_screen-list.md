# 画面一覧

## 一覧

| 画面ID | 画面名 | URLパス | 説明 | 権限 | 遷移元 | 遷移先 |
|--------|--------|--------|------|------|--------|--------|
| S001 | ログインページ | /login | メール/パスワード入力フォーム | Public | - | S002 (user), S005 (admin) |
| S002 | チャットページ | /chat, /chat/:uuid | AIチャット画面（サイドバー＋メッセージエリア） | User/Admin | S001, Navbar | - |
| S003 | 設定ページ | /settings | プロフィール編集・チャット設定・パスワード変更 | User/Admin | Navbar | - |
| S004 | ユーザー管理ページ | /admin/users | ユーザー一覧・作成・削除 | Admin | Navbar | - |
| S005 | ダッシュボードページ | /admin/dashboard | 統計サマリー・トレンド・ランキング | Admin | S001, Navbar | - |
| S006 | 会話履歴ページ | /admin/conversations | 全ユーザーの会話履歴閲覧 | Admin | Navbar | - |

## 画面遷移図

```
                    ┌──────────┐
                    │  /login  │ (S001)
                    └────┬─────┘
                         │ ログイン成功
              ┌──────────┴──────────┐
              │                     │
         (user role)           (admin role)
              │                     │
              ▼                     ▼
        ┌──────────┐        ┌──────────────┐
        │  /chat   │ (S002) │ /admin/      │ (S005)
        └──────────┘        │ dashboard    │
                            └──────────────┘

    ── Navbar（認証済み共通） ──────────────────
    │                                          │
    │  [Chat]  [Settings]  [Admin▼]  [Logout]  │
    │                       ├─ Dashboard (S005) │
    │                       ├─ Users     (S004) │
    │                       └─ History   (S006) │
    ────────────────────────────────────────────
```

## コンポーネント構成

| 画面 | 主要コンポーネント |
|------|-------------------|
| S001 | LoginPage |
| S002 | ChatPage → ChatSidebar, ChatInput, MessageList, MessageItem, StreamingMessage, MarkdownRenderer, CodeBlock, ToolCallsGroup |
| S003 | SettingsPage → ProfileUpdateForm, ChatSettingsForm, PasswordChangeForm |
| S004 | UserManagementPage → UserList, UserCreateForm, InitialPasswordModal, Pagination |
| S005 | DashboardPage → StatCard, TrendChart, RankingTable, PeriodFilter |
| S006 | ConversationHistoryPage → ConversationList, ConversationFilters, ConversationDetailModal, Pagination |

## 共通レイアウト

認証済み画面（S002〜S006）は `AuthenticatedLayout` でラップされ、以下を含む:
- **Navbar**: ナビゲーションバー（デスクトップ）
- **MobileMenu**: モバイルメニュー
- **UserMenu**: ユーザーメニュー（ログアウト含む）
