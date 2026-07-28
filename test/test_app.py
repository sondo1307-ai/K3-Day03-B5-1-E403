from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from src.app import (
    ActionParseError,
    parse_action,
    run_baseline_chatbot,
    run_react_agent,
)
from src.providers import (
    BaseLLMProvider,
    MockProvider,
    ProviderQuotaError,
)
from src.tools import reset_mock_state


class QuotaProvider(BaseLLMProvider):
    provider_name = "quota-test"
    model_name = "quota-test"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise ProviderQuotaError("quota exhausted")


class AppTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_mock_state()

    def quiet(self, function, *args):
        with redirect_stdout(io.StringIO()):
            return function(*args)

    def test_parse_action_json(self) -> None:
        action, tool_input = parse_action(
            "Thought: lookup\n"
            "Action: search_candidate_cv\n"
            'Action Input: {"candidate_name": "Nguyễn Văn An"}'
        )
        self.assertEqual(action, "search_candidate_cv")
        self.assertEqual(
            tool_input,
            {"candidate_name": "Nguyễn Văn An"},
        )

    def test_parse_action_rejects_legacy_format(self) -> None:
        with self.assertRaises(ActionParseError):
            parse_action(
                "Action: search_candidate_cv['Nguyễn Văn An']"
            )

    def test_baseline_uses_one_llm_call_and_no_tools(self) -> None:
        result = self.quiet(
            run_baseline_chatbot,
            "Gợi ý 3 câu hỏi phỏng vấn Backend Developer.",
            MockProvider(),
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["llm_calls"], 1)
        self.assertEqual(result["tool_calls"], 0)
        self.assertIn("async/await", result["answer"])
        self.assertNotIn("tiêu chí quan trọng", result["answer"])

    def test_provider_error_is_not_replaced_by_mock(self) -> None:
        result = self.quiet(
            run_baseline_chatbot,
            "Hello",
            QuotaProvider(),
        )
        self.assertEqual(result["status"], "provider_error")
        self.assertEqual(result["answer"], "")

    def test_tc3_react_uses_one_tool_and_final_answer(self) -> None:
        result = self.quiet(
            run_react_agent,
            (
                "Hãy tra cứu hồ sơ của ứng viên Nguyễn Văn An "
                "và cho biết kinh nghiệm cùng kỹ năng chính."
            ),
            MockProvider(),
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tool_calls"], 1)
        self.assertEqual(result["llm_calls"], 2)
        self.assertEqual(
            result["trace"][0]["tool"],
            "search_candidate_cv",
        )

    def test_tc4_has_three_tools_then_final_answer(self) -> None:
        result = self.quiet(
            run_react_agent,
            (
                "Đánh giá Trần Thị Bích cho Senior Python Developer, "
                "kiểm tra lịch Lê Văn C và đặt lịch phỏng vấn."
            ),
            MockProvider(),
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tool_calls"], 3)
        self.assertEqual(result["llm_calls"], 4)
        self.assertFalse(result["guardrail_triggered"])
        self.assertEqual(
            [item["tool"] for item in result["trace"]],
            [
                "screen_candidate_cv",
                "check_interviewer_schedule",
                "schedule_interview",
            ],
        )
        schedule_result = result["trace"][-1]["observation"]
        self.assertTrue(schedule_result["ok"])
        self.assertIn(
            "chưa gửi email",
            schedule_result["note"],
        )

    def test_tc5_stops_safely_on_invalid_date(self) -> None:
        result = self.quiet(
            run_react_agent,
            (
                "Đặt lịch cho Phạm Hoàng Nam ngày 31/02/2026 "
                "với Trần Văn D."
            ),
            MockProvider(),
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["tool_calls"], 1)
        observation = result["trace"][0]["observation"]
        self.assertFalse(observation["ok"])
        self.assertTrue(result["guardrail_triggered"])
        self.assertEqual(
            observation["error_code"],
            "INVALID_DATE",
        )
        self.assertIn(
            "không thực hiện thay đổi",
            result["final_answer"],
        )


if __name__ == "__main__":
    unittest.main()
