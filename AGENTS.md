# Codex Skills Project

## プロジェクト概要

Codex 向け skill 資産を開発・管理するリポジトリ。
各 skill は `skills/<skill-name>/` 配下で管理する。

## ブランチ運用ルール

### 基本方針

- **1 skill = 1ブランチ系統** で管理する
- ブランチ名は `skill/<skill-name>` の形式とする
- 既存 skill の修正時は `main` 最新から派生させる

### ブランチ作成フロー

1. 新規 skill: `main` から `skill/<skill-name>` を作成
2. 修正系ブランチ: `skill/<skill-name>-fix-xxx` を作成

## PR作成ルール

### レビュープロセス

1. 実装後、PR作成前に AI レビューを実施する
2. 優先度「高」の指摘をすべて解消する
3. 必要なら再レビューする
4. 優先度「高」が 0 件であることを確認してから PR を作成する

### PR作成手順

- PR 作成には `gh pr create` を使用する
- PR タイトルは 70 文字以内で簡潔に記述する
- PR 本文には `Summary`、`Test plan`、`AI Review` を含める

```bash
gh pr create --title "Add <skill-name> skill" --body "$(cat <<'EOF'
## Summary
- <変更内容>

## Test plan
- [ ] <テスト項目>

## AI Review
- [x] Codex などによるレビュー実施済み
- [x] 優先度「高」の指摘事項は全て解消済み
EOF
)"
```

## ディレクトリ構成

```text
codex_plugin/
├── AGENTS.md
├── README.md
└── skills/
    └── <skill-name>/
        ├── SKILL.md
        ├── agents/
        ├── scripts/
        ├── references/
        └── assets/
```

## 開発ワークフロー

1. `main` から新ブランチを作成
2. skill を実装
3. AI レビューを実施
4. 高優先度指摘を修正
5. 必要に応じて再レビュー
6. `gh pr create` で PR を作成
7. レビュー後にマージ
