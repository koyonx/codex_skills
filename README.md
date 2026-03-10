# Codex Skills Collection

このリポジトリは Codex 用の skill 集です。
Claude 向け plugin 構成はやめて、Codex が実際に読める `SKILL.md` ベースに再編しています。

## 収録 skill

- `auto-commit-suggestion`
- `branch-guard`
- `context-loader`
- `cost-tracker`
- `diff-snapshot`
- `prompt-template`
- `todo-tracker`

`session-history` は Codex 側で同等の自動 hook 前提を置けないため削除しています。

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
├── references/     # 必要な skill のみ
└── assets/         # 必要な skill のみ
```

## メモ

- `agents/openai.yaml` は手動生成しています
- `skill-creator` の `generate_openai_yaml.py` はこの環境で `PyYAML` 不足のため未使用です
