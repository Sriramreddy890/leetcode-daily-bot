# Daily LeetCode bot

This repository generates and commits a Python solution for the public LeetCode Daily Challenge once per day. It fetches the challenge through LeetCode's public GraphQL endpoint, asks the OpenAI Responses API for a LeetCode-compatible `class Solution`, and saves the result under `solutions/`.

Generated solutions are AI output: review and test them before relying on them. The workflow does **not** sign in to LeetCode and does not submit answers to the platform.

## GitHub setup

1. Create a GitHub repository from this folder and push these files.
2. In **Settings → Secrets and variables → Actions**, add the `OPENAI_API_KEY` secret.
3. Optional: add an `OPENAI_MODEL` repository variable to override the default `gpt-5.6-luna`. For harder problems, `gpt-5.6-terra` is a useful quality/cost trade-off.
4. In **Settings → Actions → General**, allow workflows to have read and write permissions if your organization blocks the workflow's `contents: write` permission.
5. In **Actions**, select **Daily LeetCode solution**, then choose **Run workflow** to verify it. It subsequently runs at 03:00 UTC each day.

## Run locally

Install `requirements.txt`, set `OPENAI_API_KEY`, then run:

```bash
python leetcode_daily_bot.py
```

Use `python leetcode_daily_bot.py --force` to regenerate today's file. The bot skips an existing daily output by default, making workflow retries safe.

## Files

- `leetcode_daily_bot.py` — fetches the challenge, requests a solution, validates syntax, and writes it.
- `.github/workflows/daily-leetcode.yml` — scheduled/manual GitHub Actions workflow that commits changes.
- `solutions/` — generated Python solutions, named by date, LeetCode ID, and title slug.
