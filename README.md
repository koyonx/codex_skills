# Codex Skills Collection

このリポジトリは Codex 用の skill 集です。
Claude 向け plugin 構成はやめて、Codex が実際に読める `SKILL.md` ベースに再編しています。

## 収録 skill

| Skill | 概要 |
|---|---|
| `api-doc-sync` | APIルート変更検出・ドキュメント同期チェック |
| `auto-commit-suggestion` | コミット準備状況のチェック・提案 |
| `branch-guard` | 保護ブランチへの直接変更防止 |
| `change-impact-analyzer` | インポートグラフによる変更影響分析 |
| `code-convention-learner` | コーディング規約の学習・注入 |
| `context-loader` | プロジェクト固有コンテキストの自動読込 |
| `cost-tracker` | Codex トークン使用量の集計 |
| `cross-repo-linker` | クロスリポジトリ依存関係の追跡・管理 |
| `dead-code-detector` | 削除/リネーム後のデッドコード参照検出 |
| `dependency-watchdog` | 依存パッケージの脆弱性監視・セキュリティ監査 |
| `diff-snapshot` | 差分スナップショットの保存・復元 |
| `env-sync` | `.env` と `.env.example` の同期チェック |
| `error-memory` | エラーパターンと解決策の記録・再利用 |
| `framework-vuln-scanner` | フレームワーク/ランタイムの EOL・脆弱性チェック |
| `git-conflict-resolver` | マージコンフリクト検出・解決支援 |
| `migration-tracker` | DB マイグレーション状態の追跡・警告 |
| `prompt-template` | 再利用可能なプロンプトテンプレート管理 |
| `secret-scanner` | API キー・トークン・パスワードの漏洩スキャン |
| `session-history` | セッション履歴の保存・閲覧 |
| `smart-context-injector` | プロンプトへの関連コンテキスト自動注入 |
| `test-auto-runner` | 変更ファイルに対応するテストの自動実行 |
| `todo-tracker` | TODO/FIXME マーカーのスキャン・集計 |
| `workflow-replay` | ワークフロー操作の記録・再生 |

## 使い方

各 skill は `skills/<skill-name>/` にあります。
Codex で使うときは、必要な skill ディレクトリを `~/.codex/skills/` 配下に置くか、symlink してください。

```bash
ln -s /path/to/codex_plugin/skills/prompt-template ~/.codex/skills/prompt-template
```

その後、Codex で skill 名を明示するか、内容に合う依頼をすると `SKILL.md` が使われます。

## 構成

各 skill は以下の形に揃えています。

```text
skills/<skill-name>/
├── SKILL.md
├── agents/openai.yaml
├── scripts/
├── references/
└── assets/
```

## 開発ルール

詳細は [AGENTS.md](AGENTS.md) を参照。

- 1 skill = 1 ブランチ (`skill/<skill-name>`)
- PR 作成前に AI レビューを実施し、優先度「高」の指摘を全て解消する
