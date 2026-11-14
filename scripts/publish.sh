#!/usr/bin/env bash
# Commits the new post to main (Cloudflare Pages then rebuilds and deploys the site). Retries if main moved meanwhile.
set -u
git config user.name "blog-bot"; git config user.email "blog-bot@users.noreply.github.com"
git add content/posts
if git diff --cached --quiet; then echo "no new post to publish"; exit 0; fi
TITLE=$(python3 -c "import json;print(json.load(open('out/last.json'))['title'])" 2>/dev/null || echo "daily post")
git commit -q -m "post: ${TITLE}"
for i in 1 2 3 4 5 6; do
  git pull -q --rebase --autostash origin main || git rebase --abort 2>/dev/null
  if git push -q origin HEAD:main; then echo "published"; exit 0; fi
  echo "push rejected, retry $i"; sleep $((i * 3))
done
echo "could not publish"; exit 1
