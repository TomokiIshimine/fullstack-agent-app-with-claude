---
argument-hint: 開発したい機能の説明を入力してください
description: 新規機能を要件定義からPR作成まで一気通貫で開発する。
---
ultrathink

# 新規機能開発ワークフロー

ユーザーの要望を起点に、以下の8フェーズを順に実行して新規機能を完成させる。

## ユーザーの要望
 `$ARGUMENTS`

## 準備

1. 今日の日付（YYYY-MM-DD）と `$ARGUMENTS` から適切な機能名を決定する
2. 作業ディレクトリ `tasks/YYYY-MM-DD-機能名/` を作成する
3. `git checkout -b feat/機能名` で feature ブランチを作成する

## ワークフロー全体像

```
Phase 1: 要件定義 → ユーザー確認
Phase 2: 設計 → ユーザー確認
Phase 3: E2Eテストケース設計 → ユーザー確認
┌─────────────────────────────────────────┐
│ Phase 4〜6 ループ（E2E成功まで）          │
│ Phase 4: 実装                           │
│ Phase 5: コードレビュー → 問題あれば4へ   │
│ Phase 6: E2Eテスト実行 → 失敗なら4へ     │
└─────────────────────────────────────────┘
Phase 7: ドキュメント更新
Phase 8: PR作成
```

---

## Phase 1: 要件定義

**エージェント:** `requirements-analyst`

Task ツールで `requirements-analyst` を起動し、以下を指示する:

> ユーザーの要望: `$ARGUMENTS`
>
> この要望をもとにヒアリングを行い、要件を定義してください。
>
> 出力先パス: `tasks/YYYY-MM-DD-機能名/Requirement.md`
>
> 要件定義書には以下を含めること:
> - 機能概要
> - ユースケース / ユーザーストーリー
> - 機能要件一覧
> - 非機能要件（あれば）
> - 前提条件・制約

成果物の保存を確認したら、**ユーザーに要件定義書の内容を提示し、承認を求める。**

承認されたら Phase 2 へ。修正指示があれば `requirements-analyst` を resume して対応する。

---

## Phase 2: 設計

**エージェント:** `system-designer`

Task ツールで `system-designer` を起動し、Phase 1 の要件定義書を渡して技術設計を行う:

> 要件定義書 `tasks/YYYY-MM-DD-機能名/Requirement.md` を読み込み、技術設計を行ってください。
>
> 出力先パス: `tasks/YYYY-MM-DD-機能名/Design.md`
>
> 設計書には以下を含めること:
> - アーキテクチャ設計（該当レイヤーの変更方針）
> - DB設計（テーブル変更がある場合）
> - API設計（エンドポイント、リクエスト/レスポンス）
> - フロントエンド設計（コンポーネント構成、画面遷移）
> - 実装計画（ファイル単位の変更一覧と順序）

成果物の保存を確認したら、**ユーザーに設計書の内容を提示し、承認を求める。**

承認されたら Phase 3 へ。修正指示があれば `system-designer` を resume して対応する。

---

## Phase 3: E2Eテストケース設計

**エージェント:** `e2e-test-creator`

Task ツールで `e2e-test-creator` を起動:

> 以下のドキュメントを読み込み、E2Eテストシナリオを設計してください。
>
> 要件定義書パス: `tasks/YYYY-MM-DD-機能名/Requirement.md`
> 設計書パス: `tasks/YYYY-MM-DD-機能名/Design.md`
> 出力先パス: `tasks/YYYY-MM-DD-機能名/test-cases/test-scenarios.md`

成果物の保存を確認したら、**ユーザーにテストケースの内容を提示し、承認を求める。**

承認されたら Phase 4 へ。修正指示があれば `e2e-test-creator` を resume して対応する。

---

## Phase 4: 実装

**エージェント:** `infra-ops` → `backend-implementer` + `frontend-implementer`

設計書 `tasks/YYYY-MM-DD-機能名/Design.md` の実装計画に従い、段階的に実装する。

### Step 4-1: インフラ変更（条件付き）

設計書に DB スキーマ変更・Docker 設定変更・マイグレーションなどインフラ変更が含まれる場合のみ、`infra-ops` を起動:

> 設計書 `tasks/YYYY-MM-DD-機能名/Design.md` に基づき、インフラ変更を実施してください。
> （DB マイグレーション、Docker 設定変更など）

### Step 4-2: バックエンド + フロントエンド実装（並列）

`backend-implementer` と `frontend-implementer` を **並列で** Task ツールから起動する:

**backend-implementer:**
> 設計書 `tasks/YYYY-MM-DD-機能名/Design.md` の実装計画に従い、バックエンド実装を行ってください。
> backend/CLAUDE.md のパターンに従うこと。テストも実装すること。

**frontend-implementer:**
> 設計書 `tasks/YYYY-MM-DD-機能名/Design.md` の実装計画に従い、フロントエンド実装を行ってください。
> frontend/CLAUDE.md のパターンに従うこと。テストも実装すること。

両方の完了を待ってから Phase 5 へ進む。

---

## Phase 5: コードレビュー

**エージェント:** `code-reviewer` ×複数並列

### Step 5-1: 変更スコープの分析

`git diff` で変更ファイルを確認し、適切なレビュースコープに分割する。
例:
- `backend/app/routes/` — ルート層
- `backend/app/services/` — サービス層
- `backend/app/repositories/` — リポジトリ層
- `frontend/src/pages/` — ページ
- `frontend/src/components/` — コンポーネント
- `frontend/src/hooks/` + `frontend/src/lib/api/` — フック・API
- テストファイル

### Step 5-2: 並列レビュー実行

各スコープごとに `code-reviewer` を **並列で** Task ツールから起動する。
各起動時に以下のパスを明示的に渡す:
- 設計書パス: `tasks/YYYY-MM-DD-機能名/Design.md`
- レビュー結果保存先: `tasks/YYYY-MM-DD-機能名/review-results/スコープ名.md`

### Step 5-3: レビュー結果の判定

全レビュー結果を集約し:
- **Must Fix（重大問題）がある場合:** 問題を修正して Phase 4 の該当部分を再実行し、再度 Phase 5 へ
- **Must Fix がない場合:** Phase 6 へ進む

---

## Phase 6: E2Eテスト実行

**エージェント:** `e2e-test-prep` → `e2e-test-runner`

### Step 6-0: 環境準備

Task ツールで `e2e-test-prep` を起動し、E2Eテスト実行に必要な環境準備（サービス起動・ヘルスチェック・DBマイグレーション・テストアカウント作成・フロントエンド疎通確認）を行う。準備が失敗した場合はユーザーに報告して指示を仰ぐ。

### Step 6-1: テスト実行

`tasks/YYYY-MM-DD-機能名/test-cases/test-scenarios.md` の「e2e-test-runner への実行指示」セクションに従い、各シナリオごとに `e2e-test-runner` を **個別に** Task ツールから起動する。
その際、保存先ディレクトリとして `tasks/YYYY-MM-DD-機能名/test-results/` を明示的に指定すること。

### テスト結果の判定

- **失敗したテストがある場合:** 失敗原因を分析し、Phase 4 に戻って修正 → Phase 5 → Phase 6 を再実行
- **全テスト成功:** ユーザーに実装結果・テスト結果のサマリーを提示し、**承認を求める**

承認されたら Phase 7 へ。

---

## Phase 7: ドキュメント更新

**エージェント:** `doc-updater`

Task ツールで `doc-updater` を起動:

> 今回の実装による変更内容をもとに、影響のあるドキュメントを特定して更新してください。

---

## Phase 8: PR作成

**エージェント:** `pull-request-creator`

Task ツールで `pull-request-creator` を起動:

> 現在のブランチの変更内容をもとに PR を作成してください。
> lint / format / test を全チェックしてから PR を作成し、CI の結果を監視してください。

PR の URL をユーザーに報告してワークフロー完了。

---

## ループ制御ルール

- Phase 4〜6 のループは **最大3回** まで。3回目でも E2E が通らない場合はユーザーに状況を報告し、判断を仰ぐ。
- 各 Phase でエラーが発生した場合は、エラー内容をユーザーに報告して指示を仰ぐ。
- ユーザー確認ゲートでは、必ず成果物のサマリーを提示してから承認を求める。
