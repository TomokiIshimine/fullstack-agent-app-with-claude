---
argument-hint: スコープを指定（backend / frontend / 特定パス）。省略時は全体をレビュー
description: コードベース全体をレビューし、発見した問題点を GitHub Issue として作成する。
allowed-tools: Read(**), Task(code-reviewer), Task(issue-manager)
---
ultrathink

# コードベースレビュー → Issue 作成ワークフロー

コードベース全体（または指定スコープ）をレビューし、発見したリファクタリングポイント・問題点を GitHub Issue として自動登録する。

## ユーザーの指定スコープ
`$ARGUMENTS`

---

## Phase 1: スコープ決定

`$ARGUMENTS` に基づきレビュー対象を決定する:

- **`backend`**: スコープ #1〜#6 のみ実行
- **`frontend`**: スコープ #7〜#10 のみ実行
- **特定パス**（例: `backend/app/routes/`）: そのパスのみを単一スコープとして実行
- **空 / 未指定**: 全 10 スコープを実行

---

## Phase 2: 並列レビュー実行

**エージェント:** `code-reviewer` × 最大10並列

Phase 1 で決定したスコープに基づき、`code-reviewer` を **並列で** Task ツールから起動する。

### レビュースコープ一覧

| # | スコープ名 | 対象パス |
|---|-----------|---------|
| 1 | backend-routes | `backend/app/routes/` |
| 2 | backend-services | `backend/app/services/` |
| 3 | backend-repositories | `backend/app/repositories/` |
| 4 | backend-models-schemas | `backend/app/models/`, `backend/app/schemas/` |
| 5 | backend-providers-tools | `backend/app/providers/`, `backend/app/tools/`, `backend/app/utils/` |
| 6 | backend-tests | `backend/tests/` |
| 7 | frontend-pages-components | `frontend/src/pages/`, `frontend/src/components/` |
| 8 | frontend-hooks | `frontend/src/hooks/` |
| 9 | frontend-lib-contexts | `frontend/src/lib/`, `frontend/src/contexts/` |
| 10 | frontend-types-utils | `frontend/src/types/`, `frontend/src/utils/` |

### 各 code-reviewer への指示

各スコープごとに以下のプロンプトで起動する:

> **レビュースコープ**: {対象パス}
>
> このスコープのコードを全て読み込み、6つの観点（アーキテクチャ準拠・設計書整合性・ドキュメント整合性・要件準拠・冗長性排除・テスト品質）でレビューしてください。
>
> **ファイルへの保存は不要です。** レビュー結果はそのままレスポンスとして返してください。
>
> 注意: 今回は既存コードベース全体のレビューです。git diff ではなく、スコープ内の全ファイルを対象にしてください。

全ての `code-reviewer` の完了を待つ。

---

## Phase 3: 結果集約 → サマリー提示 → ユーザー確認

### Step 3-1: Issue 候補の抽出と Priority マッピング

全スコープのレビュー結果から Issue 候補を抽出し、以下のルールで Priority を割り当てる:

| レビュー分類 | 該当する観点 | Issue priority |
|-------------|-------------|---------------|
| 🔴 Must Fix（全て） | 全観点 | `priority: high` |
| 🟡 Should Fix（アーキテクチャ・要件系） | アーキテクチャ準拠、設計書整合性、ドキュメント整合性、要件準拠 | `priority: medium` |
| 🟡 Should Fix（冗長性・テスト・ドキュメント系） | 冗長性排除、テスト品質 | `priority: low` |

### Step 3-2: サマリー提示とユーザー確認

以下のフォーマットでサマリーをユーザーに直接提示する:

```
## コードベースレビュー サマリー

| Priority | 件数 |
|----------|------|
| 🔴 high | X件 |
| 🟡 medium | X件 |
| 🟢 low | X件 |
| **合計** | **X件** |

## Issue 候補一覧

| # | Priority | タイトル | スコープ | 観点 |
|---|----------|---------|---------|------|
| 1 | high | fix(routes): 認証チェックの欠落 | backend-routes | アーキテクチャ準拠 |
| 2 | medium | refactor(services): 重複ロジックの統合 | backend-services | 冗長性排除 |
| ... | ... | ... | ... | ... |
```

そして AskUserQuestion で以下を確認する:

> レビュー結果から **X件** の Issue 候補が見つかりました。どの Issue を作成しますか？

選択肢:
1. 全件 Issue 作成
2. high + medium のみ作成
3. high のみ作成
4. （Other で個別番号指定を受け付ける）

**ユーザーの承認がなければ Phase 4 に進まないこと。**

---

## Phase 4: Issue 作成

**エージェント:** `issue-manager` × 逐次実行

### 重要: 逐次実行ルール

**`issue-manager` は必ず1つずつ起動すること。複数の `issue-manager` を同時に起動してはならない。** `issue-manager` は `gh issue list --search` で重複チェックを行うため、1つの Issue 作成が完了してから次を起動する。

### 各 Issue の作成方法

ユーザーが承認した各 Issue 候補について、Task ツールで `issue-manager` を **1つだけ** 起動する。プロンプトには以下を含める:

> 以下の Issue を作成してください。重複チェックも実施してください。
>
> **タイトル**: `{type}({scope}): {説明}`
> **Priority**: `{priority}`
> **本文**:
> ## 概要
> {レビューで発見した問題の概要}
>
> ## 詳細
> - **ファイル**: `{ファイルパス}` (L{行番号})
> - **観点**: {レビュー観点}
> - **問題**: {具体的な説明}
> - **推奨対応**: {修正方法}

### 進捗報告

5件ごとに進捗をユーザーに報告する:

> Issue 作成進捗: X / Y 件完了

---

## Phase 5: 完了レポート

全 Issue 作成完了後、作成された全 Issue の番号・URL・タイトルを一覧でユーザーに提示して完了とする:

```
## 作成された Issue 一覧（X件）

| # | Issue | Priority | タイトル |
|---|-------|----------|---------|
| 1 | #123 | high | fix(routes): 認証チェックの欠落 |
| 2 | #124 | medium | refactor(services): 重複ロジックの統合 |
| ... | ... | ... | ... |
```

---

## エラーハンドリング

- `code-reviewer` が1つでも失敗した場合: 失敗したスコープをユーザーに報告し、残りの結果で続行するか確認する
- `issue-manager` が失敗した場合: 失敗した Issue をスキップし、次の Issue に進む。最終レポートで失敗分を報告する
- `gh` コマンドの認証エラー: ユーザーに `gh auth login` の実行を促してワークフローを停止する
