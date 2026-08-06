"""Fetch LeetCode's daily challenge and save an AI-generated Python solution."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path


LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
OUTPUT_DIR = Path("solutions")
DAILY_CHALLENGE_QUERY = """
query questionOfToday {
  activeDailyCodingChallengeQuestion {
    date link
    question { questionFrontendId title titleSlug content difficulty topicTags { name slug } }
  }
}
"""


@dataclass(frozen=True)
class DailyChallenge:
    date: str
    url: str
    frontend_id: str
    title: str
    slug: str
    content_html: str
    difficulty: str
    topics: list[str]


def fetch_daily_challenge() -> DailyChallenge:
    """Return LeetCode's public current Daily Challenge."""
    import requests
    response = requests.post(
        LEETCODE_GRAPHQL_URL,
        json={"query": DAILY_CHALLENGE_QUERY, "variables": {}},
        headers={"Content-Type": "application/json", "User-Agent": "leetcode-daily-bot/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(f"LeetCode GraphQL error: {payload['errors']}")
    daily = payload.get("data", {}).get("activeDailyCodingChallengeQuestion")
    question = (daily or {}).get("question")
    if not daily or not question:
        raise RuntimeError("LeetCode did not return an active daily challenge.")
    return DailyChallenge(
        date=daily["date"],
        url="https://leetcode.com" + daily["link"],
        frontend_id=question["questionFrontendId"],
        title=question["title"],
        slug=question["titleSlug"],
        content_html=question["content"],
        difficulty=question["difficulty"],
        topics=[tag["name"] for tag in question.get("topicTags", [])],
    )


def solution_path(challenge: DailyChallenge) -> Path:
    safe_slug = re.sub(r"[^a-z0-9_]+", "_", challenge.slug.lower()).strip("_")
    return OUTPUT_DIR / f"{challenge.date}_{challenge.frontend_id}_{safe_slug}.py"


def strip_code_fence(text: str) -> str:
    match = re.fullmatch(r"\s*```(?:python)?\s*(.*?)\s*```\s*", text, re.DOTALL | re.IGNORECASE)
    return (match.group(1) if match else text).strip() + "\n"


def generate_solution(challenge: DailyChallenge) -> str:
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required. Add it as a GitHub Actions secret.")
    prompt = f"""Solve this LeetCode problem in Python 3.

Title: {challenge.title}
LeetCode ID: {challenge.frontend_id}
Difficulty: {challenge.difficulty}
Problem statement (HTML):
{challenge.content_html}

Return only complete Python source. It must define the class and method signature expected by
LeetCode, be efficient for the stated constraints, and contain no Markdown fences, prose, test
runner, or input/output handling."""
    response = OpenAI(api_key=api_key).responses.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-5.6-luna"),
        reasoning={"effort": os.environ.get("OPENAI_REASONING_EFFORT", "medium")},
        input=prompt,
    )
    code = strip_code_fence(response.output_text)
    if "class Solution" not in code:
        raise RuntimeError("Model response did not contain `class Solution`.")
    compile(code, "generated_solution.py", "exec")
    return code


def write_solution(challenge: DailyChallenge, code: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"date": challenge.date, "leetcode_id": challenge.frontend_id,
                "title": challenge.title, "difficulty": challenge.difficulty,
                "topics": challenge.topics, "source": challenge.url}
    target.write_text('"""' + json.dumps(metadata, indent=2) + '\n"""\n\n' + code, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="replace an existing solution for today")
    args = parser.parse_args()
    challenge = fetch_daily_challenge()
    target = solution_path(challenge)
    if target.exists() and not args.force:
        print(f"Already generated: {target}")
        return
    write_solution(challenge, generate_solution(challenge), target)
    print(f"Saved: {target}")


if __name__ == "__main__":
    main()
