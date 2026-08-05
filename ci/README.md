# GitHub Actions workflows

These are the project's CI/CD workflows, ready to activate:

| File | What it does |
|---|---|
| `ci.yml` | On every PR/push: backend ruff lint + fast test suite, full end-to-end pipeline test (artifact upload on failure), frontend production build. |
| `docker.yml` | On pushes to `main`: builds the backend and frontend Docker images and pushes them to GHCR. |
| `generate.yml` | `workflow_dispatch`: long-running render runner — runs the standalone pipeline worker (`python -m app.workers.runner --standalone`) on GitHub-hosted runners with user-supplied params, live progress callbacks, and video/artifact upload. |

## Why they live here instead of `.github/workflows/`

The automated delivery account used to publish this repository is a GitHub App
without the **Workflows** permission, and GitHub hard-refuses any push that
creates or updates files under `.github/workflows/` for such tokens. The
workflows are therefore shipped here so nothing else was blocked.

## Activating (one minute)

Any account/token with the Workflows permission (e.g. your own GitHub login)
can activate them with a single commit:

```bash
git mv ci/github-workflows .github/workflows
git commit -m "Activate GitHub Actions workflows"
git push
```

…or via the GitHub web UI: **Actions → New workflow → set up a workflow
yourself**, paste each file's contents, and commit.

No edits are needed — the workflows are self-contained and reference only
repository-relative paths.
