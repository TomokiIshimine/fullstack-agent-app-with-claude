---
argument-hint: 件数やフィルタ（例: 3, 5 backend, priority:medium）。省略時は priority:high から3件
description: 最も重要度の高い Issue を N 件選んで順次自動解決し、それぞれ別の PR を作成する。
---
ultrathink

# Issue 自動解決ワークフロー

GitHub Issue を優先度順に取得し、1件ずつブランチを切って修正・テスト・PR作成まで自動で実行する。
ユーザー確認ゲートなし — 全て自律的に処理する。

## 引数
`$ARGUMENTS`

---

## Phase 0: 引数解析と Issue 取得

### Step 0-1: 引数解析

`$ARGUMENTS` を解析して以下のパラメータを決定する:

| パラメータ | デフォルト | 例 |
|-----------|-----------|-----|
| 件数 | 3 | `5` → 5件 |
| スコープ | なし | `backend` → backend スコープのみ |
| Priority | high | `priority:medium` → medium |

解析ルール:
- 数字のみ → 件数（例: `5`）
- `backend` / `frontend` → スコープフィルタ
- `priority:high` / `priority:medium` → Priority フィルタ
- 組み合わせ可（例: `5 backend priority:medium`）
- 空 / 未指定 → 件数3, priority:high, スコープなし

### Step 0-2: Issue 取得

Bash ツールで以下を実行:

```bash
gh issue list --label "priority: {priority}" --state open --json number,title,body,labels --limit {件数}
```

スコープフィルタがある場合、取得した Issue をタイトルの `({scope})` 部分でフィルタリングする:
- `backend` → タイトルに `(routes)`, `(services)`, `(repositories)`, `(models)`, `(schemas)`, `(providers)`, `(tools)`, `(utils)`, `(tests)` を含むもの
- `frontend` → タイトルに `(pages)`, `(components)`, `(hooks)`, `(lib)`, `(contexts)`, `(types)` を含むもの

取得した Issue の一覧をユーザーに表示する:

```
## 処理対象 Issue（{N}件）

| # | Issue | Priority | タイトル |
|---|-------|----------|---------|
| 1 | #XX | high | fix(routes): ... |
| ... | ... | ... | ... |

これらを順次解決し、それぞれ PR を作成します。
```

Issue が 0 件の場合はメッセージを表示して終了する。

---

## Issue ループ（1件ずつ逐次処理）

以下の Phase 1〜4 を Issue ごとに繰り返す。
**Issue 間の並列処理は行わない** — ファイル競合を防ぎ、main を最新に保つため。

各 Issue の処理開始時に進捗を表示する:

```
---
## Issue {i}/{N}: #{issue_number} {issue_title}
---
```

---

### Phase 1: ブランチ作成と準備

1. `git checkout main && git pull origin main` で main を最新にする
2. Issue タイトルからブランチ名を生成する:
   - `fix(routes): 認証チェックの欠落` → `fix/issue-{number}-routes-auth-check`
   - パターン: `{type}/issue-{number}-{scope}-{短い説明（kebab-case）}`
3. `git checkout -b {ブランチ名}` でブランチを作成する

---

### Phase 2: 軽量設計

**エージェント:** `system-designer`

Task ツールで `system-designer` を起動する:

> 以下の GitHub Issue の修正方針を設計してください。
>
> **Issue #{number}**: {title}
>
> **Issue 本文:**
> {body}
>
> 以下を簡潔に整理してください（ファイルに保存不要、レスポンスとして返すこと）:
> 1. **影響ファイル一覧**: 変更が必要なファイルパスのリスト
> 2. **変更方針**: 各ファイルで何をどう変更するか（1-2行）
> 3. **テスト方針**: 既存テストの修正 or 新規テスト追加の要否
> 4. **リスク**: 他機能への影響の有無
>
> CLAUDE.md と既存コードを読んでプロジェクトのパターンに従うこと。

設計結果を保持し、Phase 3 で使用する。

---

### Phase 3: 実装とテスト

Issue タイトルの `({scope})` からスコープを自動判定する:

**バックエンドスコープ**: `routes`, `services`, `repositories`, `models`, `schemas`, `providers`, `tools`, `utils`, `tests`（backend/tests に関連する Issue）
**フロントエンドスコープ**: `pages`, `components`, `hooks`, `lib`, `contexts`, `types`

#### Step 3-1: 実装

スコープに応じたエージェントを Task ツールで起動する:

**バックエンドの場合 → `backend-implementer`:**
> 以下の GitHub Issue を修正してください。
>
> **Issue #{number}**: {title}
>
> **Issue 本文:**
> {body}
>
> **設計方針:**
> {Phase 2 の設計結果}
>
> backend/CLAUDE.md のパターンに厳密に従うこと。
> 必要に応じてテストも追加・修正すること。

**フロントエンドの場合 → `frontend-implementer`:**
> 以下の GitHub Issue を修正してください。
>
> **Issue #{number}**: {title}
>
> **Issue 本文:**
> {body}
>
> **設計方針:**
> {Phase 2 の設計結果}
>
> frontend/CLAUDE.md のパターンに厳密に従うこと。
> 必要に応じてテストも追加・修正すること。

**スコープ不明の場合:** Issue 本文のファイルパスから判定する。両方に跨る場合は `backend-implementer` → `frontend-implementer` の順に逐次実行する。

#### Step 3-2: テスト実行

Bash ツールでスコープに応じたテストを実行する:

- バックエンド: `make test-backend`
- フロントエンド: `make test-frontend`
- 両方: `make test`

**テストが失敗した場合:**
失敗内容を分析し、該当スコープのエージェントを再起動して修正する。修正後に再テスト。
テスト修正ループは **最大2回** まで。2回目でも失敗する場合は、失敗内容を記録してこの Issue をスキップし、次の Issue に進む。

#### Step 3-3: フォーマット

`make format` を実行してコードを整形する。

---

### Phase 4: コードレビューと PR 作成

#### Step 4-1: コードレビュー

`git diff main` で変更ファイルを確認し、変更があるディレクトリに基づいて `code-reviewer` を **並列で** Task ツールから起動する。

各 `code-reviewer` への指示:

> 以下のスコープの変更をレビューしてください。
>
> **スコープ**: {対象パス}
> **Issue**: #{number} {title}
>
> ファイルへの保存は不要です。レビュー結果はそのままレスポンスとして返してください。
> Must Fix（重大問題）があれば明確に示してください。

#### Step 4-2: レビュー結果の判定と修正

- **Must Fix がある場合:** 問題を修正し、再度テストを実行する。修正ループは **最大2回** まで。
- **Must Fix がない場合:** Step 4-3 へ。

#### Step 4-3: コミットと PR 作成

1. 変更をステージングしてコミットする:
   - コミットメッセージ: `{type}({scope}): {Issue タイトルの説明部分} (#issue_number)`
   - 例: `fix(routes): add missing auth check (#42)`
2. Task ツールで `pull-request-creator` を起動する:

> 現在のブランチの変更内容をもとに PR を作成してください。
> PR タイトルには Issue 番号を含めてください。
> PR 本文に `Closes #{issue_number}` を含めてください。
> lint / format / test を全チェックしてから PR を作成し、CI の結果を監視してください。

PR の URL を記録する。

#### Step 4-4: main に戻る

`git checkout main` で main ブランチに戻り、次の Issue の処理に進む。

---

## Phase 5: 完了レポート

全 Issue の処理完了後、結果をユーザーに提示する:

```
## Issue 自動解決レポート

### 成功（X件）

| # | Issue | PR | タイトル |
|---|-------|----|---------|
| 1 | #42 | #50 | fix(routes): add missing auth check |
| ... | ... | ... | ... |

### スキップ（Y件）

| # | Issue | 理由 |
|---|-------|------|
| 1 | #43 | テスト修正ループ超過: {失敗内容の要約} |
| ... | ... | ... |
```

---

## エラーハンドリング

- **`gh` コマンドの認証エラー**: ユーザーに `gh auth login` の実行を促してワークフローを停止する
- **ブランチ作成失敗**（既存ブランチ名の衝突など）: ブランチ名にタイムスタンプを付与してリトライする
- **エージェント起動失敗**: エラー内容を記録し、その Issue をスキップして次に進む
- **テスト修正ループ超過**: 変更を破棄（`git reset --hard && git checkout main`）し、スキップリストに追加する
- **全 Issue スキップ**: 全件失敗した場合はその旨をレポートに明記する
