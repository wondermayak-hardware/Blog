# ThunderStudy Daily Blog Bot

Every morning (8:00 IST) it picks the next of 5000 ideas, writes the post with OpenRouter,
and sends you the title, labels, description and the post file on Telegram.

## Setup (10 minutes)
1. Create a new GitHub repo and upload everything in this folder (keep `.github/workflows`).
2. Repo > Settings > Secrets and variables > Actions > New secret:
   - `OPENROUTER_API_KEY` (openrouter.ai/keys)
   - `TELEGRAM_BOT_TOKEN` (from @BotFather)
   - `TELEGRAM_CHAT_ID` (your numeric Telegram ID, see below)
3. Message your bot once (press Start) so it can message you.
4. Actions tab > "Daily blog" > Run workflow to test.

## Posting on Blogger
New post > paste the title > switch to **HTML view** > paste the .txt contents > add the Labels and
Search description from the Telegram message > Publish. No head/body tags needed: Blogger's theme
styles the post, and the bot adds a ready-made button box linking to your sites.

## Settings
- Free models are found automatically from OpenRouter every day (best free text models first),
  with `openrouter/free` as the last fallback. You never need to edit model names.
- Language: set env `LANGUAGE` (e.g. "Hinglish") in the workflow.
- A failed run does not use up an idea; it retries the next day.

## What is the Telegram Chat ID?
It is your personal Telegram number ID: it tells the bot where to send messages.
1. In Telegram, search **@userinfobot** and press Start. It replies with `Id: 123456789`. That number is your Chat ID.
2. Open your own bot and press **Start** once (otherwise the bot cannot message you).
3. Put the number in the `TELEGRAM_CHAT_ID` secret. For a group or channel the ID starts with `-100`.
