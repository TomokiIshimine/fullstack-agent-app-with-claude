# 管理者ダッシュボード 要件定義書

## 1. 概要

### 1.1 目的
管理者がシステム全体のユーザー利用状況をリアルタイムで把握し、サービス運用の意思決定を支援するためのダッシュボードを提供する。

### 1.2 対象ユーザー
- role: "admin" を持つ管理者ユーザー

### 1.3 既存機能との関係
| 既存機能 | 本ダッシュボード |
|---------|---------------|
| ユーザー管理ページ | 統計情報を追加表示 |
| 会話履歴ページ | 利用傾向の分析を追加 |
| （新規） | 概要ダッシュボード |

---

## 2. 機能要件

### 2.1 ダッシュボード概要ページ（メイン画面）

#### 2.1.1 サマリーカード
リアルタイムで以下の主要KPIを表示:

| メトリクス | 説明 | データソース |
|-----------|------|------------|
| 総ユーザー数 | 登録ユーザーの総数 | User.count() |
| アクティブユーザー数 | 過去7日間に会話があったユーザー数 | Conversation.user_id (distinct) |
| 総会話数 | システム全体の会話数 | Conversation.count() |
| 今日の会話数 | 本日作成された会話数 | Conversation.created_at |
| 総メッセージ数 | 全メッセージ数 | Message.count() |
| 総トークン消費量 | input_tokens + output_tokens の合計 | Message.input_tokens, output_tokens |
| 推定総コスト | cost_usd の合計 | Message.cost_usd |

#### 2.1.2 利用傾向グラフ
- **日別会話数推移**（過去30日間の折れ線グラフ）
- **日別メッセージ数推移**（過去30日間の折れ線グラフ）
- **日別トークン消費量推移**（過去30日間の棒グラフ）

#### 2.1.3 ユーザーアクティビティランキング
- 会話数 TOP10 ユーザー
- メッセージ数 TOP10 ユーザー
- トークン消費量 TOP10 ユーザー

---

### 2.2 ユーザー統計ページ

#### 2.2.1 ユーザー概要
| メトリクス | 説明 |
|-----------|------|
| ロール別ユーザー数 | admin / user の内訳（円グラフ） |
| 新規登録推移 | 日別・週別・月別の登録数（折れ線グラフ） |
| ユーザー別利用状況 | 各ユーザーの会話数・メッセージ数・最終アクティブ日（テーブル） |

#### 2.2.2 ユーザー詳細統計
特定ユーザーを選択した際の詳細表示:
- 登録日
- 総会話数
- 総メッセージ数
- 総トークン消費量
- 推定コスト
- 会話頻度（日別推移）

---

### 2.3 AI利用統計ページ

#### 2.3.1 トークン・コスト分析
| メトリクス | 説明 |
|-----------|------|
| 総入力トークン数 | 全期間の input_tokens 合計 |
| 総出力トークン数 | 全期間の output_tokens 合計 |
| 総コスト | cost_usd の合計 |
| 平均コスト/会話 | 会話あたりの平均コスト |
| 平均コスト/ユーザー | ユーザーあたりの平均コスト |
| コスト推移 | 日別・週別・月別のコスト推移グラフ |

#### 2.3.2 パフォーマンス分析
| メトリクス | 説明 |
|-----------|------|
| 平均レスポンス時間 | response_time_ms の平均 |
| レスポンス時間分布 | ヒストグラム（0-1s, 1-3s, 3-5s, 5s+） |
| レスポンス時間推移 | 日別の平均レスポンス時間 |

#### 2.3.3 モデル利用状況
| メトリクス | 説明 |
|-----------|------|
| モデル別利用回数 | 使用されたモデルの内訳（円グラフ） |
| モデル別トークン消費量 | モデルごとのトークン使用量 |
| モデル別コスト | モデルごとのコスト |

---

### 2.4 ツール利用統計ページ

#### 2.4.1 ツールコール分析
| メトリクス | 説明 | データソース |
|-----------|------|------------|
| ツール別利用回数 | 各ツールの呼び出し回数（棒グラフ） | ToolCall.tool_name |
| ツール成功率 | 成功/エラーの割合 | ToolCall.status |
| ツール別エラー数 | エラーが発生したツールのランキング | ToolCall.error |
| ツール実行時間 | started_at から completed_at の差分 | ToolCall |

---

### 2.5 期間フィルター（共通機能）

全ページで以下の期間フィルターを適用可能:
- 今日
- 過去7日間
- 過去30日間
- 過去90日間
- カスタム期間（開始日〜終了日）

---

## 3. 非機能要件

### 3.1 パフォーマンス
| 項目 | 要件 |
|-----|------|
| ダッシュボード読み込み時間 | 3秒以内 |
| グラフ描画時間 | 1秒以内 |
| データ更新頻度 | ページリロード時（リアルタイム更新は将来対応） |

### 3.2 セキュリティ
| 項目 | 要件 |
|-----|------|
| 認証 | JWT認証必須 |
| 認可 | admin ロールのみアクセス可能 |
| ログ | 管理者操作のアクセスログ記録 |

### 3.3 レスポンシブ対応
- デスクトップ（1280px以上）: フル機能
- タブレット（768px-1279px）: 2カラムレイアウト
- モバイル（767px以下）: 1カラムレイアウト（グラフは横スクロール）

---

## 4. 画面構成

```
/admin/dashboard          # メインダッシュボード（概要）
/admin/dashboard/users    # ユーザー統計
/admin/dashboard/ai       # AI利用統計（トークン・コスト・パフォーマンス）
/admin/dashboard/tools    # ツール利用統計
```

### 4.1 ナビゲーション構成
```
管理者メニュー
├── ダッシュボード（新規）
│   ├── 概要
│   ├── ユーザー統計
│   ├── AI利用統計
│   └── ツール利用統計
├── ユーザー管理（既存）
└── 会話履歴（既存）
```

---

## 5. API設計

### 5.1 新規エンドポイント

#### サマリー統計
```
GET /api/admin/dashboard/summary
Response:
{
  "total_users": number,
  "active_users": number,        // 過去7日間
  "total_conversations": number,
  "today_conversations": number,
  "total_messages": number,
  "total_tokens": {
    "input": number,
    "output": number
  },
  "total_cost_usd": number
}
```

#### 利用傾向（時系列データ）
```
GET /api/admin/dashboard/trends?period=30d&metric=conversations
Query Parameters:
  - period: 7d | 30d | 90d | custom
  - start_date: YYYY-MM-DD (custom時)
  - end_date: YYYY-MM-DD (custom時)
  - metric: conversations | messages | tokens | cost

Response:
{
  "period": "30d",
  "metric": "conversations",
  "data": [
    { "date": "2025-01-01", "value": 42 },
    { "date": "2025-01-02", "value": 38 },
    ...
  ]
}
```

#### ユーザーランキング
```
GET /api/admin/dashboard/rankings?metric=conversations&limit=10
Query Parameters:
  - metric: conversations | messages | tokens | cost
  - limit: number (default: 10, max: 50)
  - period: 7d | 30d | 90d | all (default: all)

Response:
{
  "metric": "conversations",
  "rankings": [
    { "user_id": 1, "email": "user@example.com", "name": "User Name", "value": 150 },
    ...
  ]
}
```

#### ユーザー統計
```
GET /api/admin/dashboard/users/stats
Response:
{
  "by_role": {
    "admin": number,
    "user": number
  },
  "registration_trend": [
    { "date": "2025-01", "count": 15 },
    ...
  ]
}
```

#### AI利用統計
```
GET /api/admin/dashboard/ai/stats?period=30d
Response:
{
  "tokens": {
    "total_input": number,
    "total_output": number,
    "average_per_message": number
  },
  "cost": {
    "total_usd": number,
    "average_per_conversation": number,
    "average_per_user": number
  },
  "performance": {
    "average_response_time_ms": number,
    "response_time_distribution": {
      "0-1s": number,
      "1-3s": number,
      "3-5s": number,
      "5s+": number
    }
  },
  "models": [
    { "model": "claude-sonnet-4-5-20250929", "count": 1000, "tokens": 50000, "cost_usd": 25.00 },
    ...
  ]
}
```

#### ツール利用統計
```
GET /api/admin/dashboard/tools/stats?period=30d
Response:
{
  "tools": [
    {
      "tool_name": "web_search",
      "call_count": 500,
      "success_count": 480,
      "error_count": 20,
      "success_rate": 0.96,
      "average_duration_ms": 1500
    },
    ...
  ]
}
```

---

## 6. 技術設計

### 6.1 バックエンド

#### 新規コンポーネント
```
backend/app/
├── routes/
│   └── admin_dashboard_routes.py    # ダッシュボードAPI
├── services/
│   └── admin_dashboard_service.py   # 統計集計ロジック
├── repositories/
│   └── dashboard_repository.py      # 統計クエリ
└── schemas/
    └── admin_dashboard_schemas.py   # レスポンススキーマ
```

#### クエリ最適化
- 集計クエリには適切なインデックスを活用
- 重い集計はキャッシュ検討（Redis利用可能）
- ページネーションで大量データを分割

### 6.2 フロントエンド

#### 新規コンポーネント
```
frontend/src/
├── pages/admin/dashboard/
│   ├── DashboardOverviewPage.tsx    # 概要
│   ├── UserStatsPage.tsx            # ユーザー統計
│   ├── AIStatsPage.tsx              # AI利用統計
│   └── ToolStatsPage.tsx            # ツール統計
├── components/admin/dashboard/
│   ├── StatCard.tsx                 # KPIカード
│   ├── TrendChart.tsx               # 推移グラフ
│   ├── RankingTable.tsx             # ランキングテーブル
│   ├── PieChart.tsx                 # 円グラフ
│   ├── BarChart.tsx                 # 棒グラフ
│   └── PeriodFilter.tsx             # 期間フィルター
├── hooks/
│   └── useAdminDashboard.ts         # ダッシュボードデータ取得
└── lib/api/
    └── adminDashboard.ts            # APIクライアント
```

#### グラフライブラリ
推奨: **Recharts**
- React専用で統合が容易
- 軽量で高パフォーマンス
- 豊富なカスタマイズオプション

---

## 7. 実装優先度

### Phase 1: MVP（最小限の実用機能）
1. ダッシュボード概要ページ
   - サマリーカード（主要KPI）
   - 日別会話数推移グラフ
2. 基本的な期間フィルター（7日/30日/90日）

### Phase 2: 分析機能強化
3. ユーザー統計ページ
4. AI利用統計ページ（トークン・コスト）
5. ユーザーランキング機能

### Phase 3: 詳細分析
6. パフォーマンス分析（レスポンス時間）
7. ツール利用統計ページ
8. カスタム期間フィルター
9. データエクスポート機能（CSV）

---

## 8. 受け入れ基準

### 8.1 機能要件
- [ ] 管理者のみがダッシュボードにアクセスできる
- [ ] 主要KPIがサマリーカードで表示される
- [ ] 過去30日間の利用傾向がグラフで表示される
- [ ] 期間フィルターで表示期間を変更できる
- [ ] ユーザー別の利用状況が確認できる
- [ ] トークン消費量・コストが確認できる

### 8.2 非機能要件
- [ ] ダッシュボード読み込みが3秒以内
- [ ] レスポンシブデザインでモバイルでも閲覧可能
- [ ] アクセスログが記録される

### 8.3 テスト要件
- [ ] バックエンドAPIのユニットテスト
- [ ] フロントエンドコンポーネントのテスト
- [ ] E2Eテスト（管理者ログイン → ダッシュボード表示）

---

## 9. 将来の拡張案（スコープ外）

- リアルタイム更新（WebSocket）
- アラート機能（異常な利用パターンの検知）
- レポート自動生成・メール送信
- ユーザー行動分析（セッション追跡）
- A/Bテスト用のメトリクス
