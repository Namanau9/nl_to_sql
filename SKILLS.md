# Skills

This document lists reusable skills / runbooks used by the development agent for this project.

## Skill: frontend-design

Invoked when building or refining the React analytics chat interface. The skill provides guidance on
component structure, styling conventions, and the chat → SQL → results → explanation UI flow.

**Invoke:**

```text
skill: frontend-design
```

## Engineering Runbooks

### Branch → feature → test → commit → push

Every medium feature is developed on its own branch:

```text
main → feature/<name> → implement → test → commit → push
```

### Validate before commit

```bash
git status
git diff
```

### Never commit secrets

- Keep real credentials only in `.env` (git-ignored).
- `.env.example` may contain placeholders only.
- Scan diffs for API keys, passwords, and tokens before each commit.
