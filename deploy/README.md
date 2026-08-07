# Deploying

## Vercel (easiest — nothing to configure)

Import this repo at [vercel.com/new](https://vercel.com/new) and click Deploy.
No environment variables are required. `vercel.json` in the repo root handles the rest.

Or from your machine:

```bash
npx vercel --prod
```

---

## GitHub Pages

The workflow lives here as `github-pages.yml` rather than in `.github/workflows/`,
because the automation that created this repo isn't permitted to publish workflow files.

Activate it in two commands:

```bash
mkdir -p .github/workflows
cp deploy/github-pages.yml .github/workflows/deploy.yml
git add .github/workflows/deploy.yml
git commit -m "ci: enable GitHub Pages deployment"
git push
```

Then in your repository: **Settings → Pages → Source → GitHub Actions**.

Every push to `main` now publishes to `https://<your-user>.github.io/<repo>/`.
The workflow sets `BASE_PATH` to your repo name automatically, so asset paths resolve correctly.

### Building the static bundle manually

```bash
BASE_PATH=/yt npm run build:static   # writes ./out
```

Set `BASE_PATH` to `/<repo-name>` for a project site.
Omit it entirely for a custom domain or a `<user>.github.io` repo.

---

## Any other static host

`./out` is a plain folder of static files — deploy it to Netlify, Cloudflare Pages,
S3, Surge or anything else. There is no backend to run.
