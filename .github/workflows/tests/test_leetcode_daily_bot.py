import unittest

from leetcode_daily_bot import DailyChallenge, solution_path, strip_code_fence


class BotHelpersTest(unittest.TestCase):
    def test_code_fence_is_removed(self):
        self.assertEqual(strip_code_fence("```python\nclass Solution: pass\n```"), "class Solution: pass\n")

    def test_solution_path_is_stable_and_safe(self):
        challenge = DailyChallenge(
            date="2026-08-06", url="https://leetcode.com/problems/example", frontend_id="1",
            title="Example", slug="Example Problem!", content_html="<p>Example</p>",
            difficulty="Easy", topics=[],
        )
        self.assertEqual(str(solution_path(challenge)).replace("\\", "/"), "solutions/2026-08-06_1_example_problem.py")


if __name__ == "__main__":
    unittest.main()
