# Daily LeetCode bot

This repository generates, submits, and commits a Python solution for the public LeetCode Daily Challenge once per day. It fetches the challenge through LeetCode's public GraphQL endpoint, asks the OpenAI Responses API for a LeetCode-compatible `class Solution`, submits it, and saves the result under `solutions/` only after LeetCode accepts it.

Generated solutions are AI output and can be wrong. The workflow signs in using LeetCode session cookies stored as GitHub Actions secrets and submits the generated Python 3 answer. A rejected answer fails the workflow and is not saved.

## GitHub setup

1. Create a GitHub repository from this folder and push these files.
2. In **Settings → Secrets and variables → Actions**, add these repository secrets:
   - `OPENAI_API_KEY`: an OpenAI API key with API access enabled.
   - `LEETCODE_SESSION`: the `LEETCODE_SESSION` cookie from your signed-in LeetCode browser session.
   - `LEETCODE_CSRF_TOKEN`: the `csrftoken` cookie from the same session.
3. Optional: add an `OPENAI_MODEL` repository variable to override the default `gpt-5.6-luna`. For harder problems, `gpt-5.6-terra` is a useful quality/cost trade-off.
4. In **Settings → Actions → General**, allow workflows to have read and write permissions if your organization blocks the workflow's `contents: write` permission.
5. In **Actions**, select **Daily LeetCode solution**, then choose **Run workflow** to verify it. It subsequently runs at 00:20 UTC each day.

Never put passwords, cookies, or API keys in source files or chat. Session cookies provide account access; revoke the LeetCode session if a cookie is exposed and rotate the OpenAI key if needed.

## Run locally

Install `requirements.txt`, set `OPENAI_API_KEY`, then run to generate a solution without submitting it:

```bash
python leetcode_daily_bot.py
```

Use `python leetcode_daily_bot.py --force` to regenerate today's file. The bot skips an existing daily output by default, making workflow retries safe.

Set `AUTO_SUBMIT=true` plus `LEETCODE_SESSION` and `LEETCODE_CSRF_TOKEN` to submit locally. The GitHub workflow enables this automatically.

## Files

- `leetcode_daily_bot.py` — fetches the challenge, requests a solution, validates syntax, and writes it.
- `.github/workflows/daily-leetcode.yml` — scheduled/manual GitHub Actions workflow that commits changes.
- `solutions/` — generated Python solutions, named by date, LeetCode ID, and title slug.
