# Branch Guard Config

Create `.branch-guard.json` in the git root when the default protected branches are not enough.

```json
{
  "protected_branches": ["main", "master", "production"]
}
```

If the file is absent, the skill treats `main` and `master` as protected.
