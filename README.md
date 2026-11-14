# ThunderStudy Blog: website + daily bot in one repo

Hosted on **Cloudflare Pages** at blog.thunderstudy.info. A **GitHub Actions** bot writes one post every morning, saves it
in this repo, and Cloudflare rebuilds and deploys the site by itself. The sitemap, RSS feed, search index, category pages
and pagination are regenerated on every deploy, so you never touch them.

```
 08:00 IST  GitHub Actions  ->  OpenRouter writes the post  ->  commit to main  ->  Cloudflare builds + deploys  ->  Telegram sends you the link
```

## Setup (one time, about 15 minutes)

**1. GitHub**
- Create a repo and upload everything in this folder to the `main` branch (keep the `.github` folder).
- Settings > Secrets and variables > Actions > New repository secret, add:
  - `OPENROUTER_API_KEY` (openrouter.ai/keys)
  - `TELEGRAM_BOT_TOKEN` (from @BotFather)
  - `TELEGRAM_CHAT_ID` (your numeric ID: open @userinfobot in Telegram and press Start; then press Start on your own bot once)
- Settings > Actions > General > Workflow permissions: choose **Read and write permissions** and save.

**2. Cloudflare Pages**
- Cloudflare dashboard > Workers & Pages > Create > Pages > Connect to Git > pick this repo.
- Framework preset: None. Build command: `python build.py`. Build output directory: `_site`. Production branch: `main`.
- The `.python-version` file in this repo selects Python 3.12. If a build ever fails with a syntax error, add the build variable `PYTHON_VERSION` = `3.12`.
- Deploy. You get a `*.pages.dev` address to check the site.

**3. Domain**
- Pages project > Custom domains > Set up a domain > `blog.thunderstudy.info`. If thunderstudy.info uses Cloudflare DNS it is added for you; otherwise create a CNAME `blog` pointing to your `*.pages.dev` address.

**4. Search engines**
- Google Search Console: add `https://blog.thunderstudy.info/`, submit `https://blog.thunderstudy.info/sitemap.xml`. Do the same in Bing Webmaster Tools.

**5. Test the bot**
- GitHub > Actions > Daily blog > Run workflow. In 3 to 5 minutes you should get the Telegram message and a new file in `content/posts/`.

## How the daily bot works
- `bot/ideas.json` holds 5000 ideas. The bot picks the next idea that has no post yet. Progress is the posts themselves (each bot post has `idea: N` in its front matter), so there is no separate state that can get out of sync.
- It skips any idea whose title already exists as a post. Delete a post and the bot will write that idea again later.
- To write a specific idea, run the workflow manually and fill in `idea_id`.
- Free models are discovered automatically from OpenRouter every day, with `openrouter/free` as the last fallback.
- A second AI pass checks the answers and lists doubtful ones in the Telegram message. Free models can miss errors, so skim the posts. To fix one, edit the file in `content/posts/` on GitHub; Cloudflare redeploys.
- The workflow builds the site before publishing, so a broken post can never break the live site. If anything fails you get a Telegram message and the idea is not used up.

## Adding or editing posts by hand
Create `content/posts/<slug>.html`:
```
---
title: How to Prepare Space and ISRO for CUET 2027 in 7 Days
description: One or two sentences, 120-155 characters, used as the meta description.
date: 2026-11-14
category: GK
labels: CUET 2027, GK, Study Plan
---
<p>Quick Answer: one direct 30-50 word answer.</p>
<p>Short intro.</p>
<h2>Section title</h2>
<p>Plain HTML only: p, h2, h3, ol, ul, b.</p>
```
`build.py` turns it into colour-coded blocks (Quick Answer card, plan, tips, mistakes, question cards, answer key, FAQ accordion) and
generates BlogPosting, BreadcrumbList and FAQPage schema.

## What is in the repo
- `build.py`, `postfmt.py`, `styler.py`, `cssutil.py`: the site generator (no dependencies, Python 3.12).
- `design/`: header, footer, dock, sidebar, loader, tokens and scripts cut from design_ai.html.
- `assets/`: blog CSS and JS, favicon, `og-default.jpg` (your mascot share image).
- `content/posts/`: all posts. `bot/`: the daily bot and the 5000 ideas. `scripts/publish.sh`: commits and pushes with retries.
- `.github/workflows/daily-blog.yml`: the schedule.

## Troubleshooting
- **No Telegram message:** Actions > Daily blog > open the last run and read the red step. Check the three secrets and that you pressed Start on your bot.
- **"could not publish":** Workflow permissions must be Read and write (step 1).
- **Post written but not on the site:** Cloudflare Pages > Deployments shows the build log.
- **Limits:** Cloudflare Pages free plan allows 20,000 files per site. 5000 posts build to about 5,800 files in about 16 seconds (tested).
