"""Fetch LeetCode's daily challenge and save an AI-generated Python solution."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path


LEETCODE_GRAPHQL_URL = "https://leetcode.com/graphql"
OUTPUT_DIR = Path("solutions")
DAILY_CHALLENGE_QUERY = """
query questionOfToday {
  activeDailyCodingChallengeQuestion {
    date link
    question { questionId questionFrontendId title titleSlug content difficulty topicTags { name slug } }
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
    question_id: str | None = None


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
        question_id=question["questionId"],
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


def submit_solution(challenge: DailyChallenge, code: str) -> None:
    """Submit a solution using session cookies stored in environment variables."""
    import requests

    leetcode_session = os.environ.get("LEETCODE_SESSION")
    csrf_token = os.environ.get("LEETCODE_CSRF_TOKEN")
    if not leetcode_session or not csrf_token:
        raise RuntimeError(
            "AUTO_SUBMIT requires LEETCODE_SESSION and LEETCODE_CSRF_TOKEN GitHub secrets."
        )

    session = requests.Session()
    session.cookies.set("LEETCODE_SESSION", leetcode_session, domain="leetcode.com", path="/")
    session.cookies.set("csrftoken", csrf_token, domain="leetcode.com", path="/")
    headers = {
        "Content-Type": "application/json",
        "Referer": challenge.url,
        "Origin": "https://leetcode.com",
        "X-CSRFToken": csrf_token,
        "User-Agent": "leetcode-daily-bot/1.0",
    }
    response = session.post(
        f"https://leetcode.com/problems/{challenge.slug}/submit/",
        json={
            "lang": "python3",
            "question_id": challenge.question_id,
            "typed_code": code,
        },
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    submission_id = response.json().get("submission_id")
    if not submission_id:
        raise RuntimeError(f"LeetCode did not create a submission: {response.text[:500]}")

    for _ in range(45):
        time.sleep(2)
        result = session.get(
            f"https://leetcode.com/submissions/detail/{submission_id}/check/",
            headers=headers,
            timeout=30,
        )
        result.raise_for_status()
        verdict = result.json()
        state = verdict.get("state")
        if state == "SUCCESS":
            if verdict.get("status_code") == 10:
                return
            raise RuntimeError(f"LeetCode verdict: {verdict.get('status_msg', state)}")
        if state not in ("PENDING", "STARTED"):
            raise RuntimeError(f"Unexpected LeetCode judge status: {verdict}")
    raise RuntimeError("Timed out waiting for LeetCode's judge.")


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
    code = generate_solution(challenge)
    if os.environ.get("AUTO_SUBMIT", "false").lower() == "true":
        submit_solution(challenge, code)
    write_solution(challenge, code, target)
    print(f"Saved: {target}")


if __name__ == "__main__":
    main()
