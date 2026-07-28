"""
Offline Mock Provider.

Provider này không gọi API thật và không dùng kiến thức sinh tự do.
Nó chỉ trả câu trả lời đã khai báo trong MOCK_BASELINE_ANSWERS.
"""

from __future__ import annotations

from mock_data import MOCK_BASELINE_ANSWERS


def _normalize(value: str) -> str:
    return " ".join(str(value).strip().split())


class MockProvider:
    model_name = "Offline Full Mock Mode"

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
    ) -> str:
        normalized_prompt = _normalize(prompt)

        for question, answer in MOCK_BASELINE_ANSWERS.items():
            if _normalize(question) in normalized_prompt:
                return answer

        return (
            "[MOCK DATA NOT FOUND]: "
            "Chưa có phản hồi mock cho câu hỏi này."
        )


def get_llm_provider() -> MockProvider:
    return MockProvider()
