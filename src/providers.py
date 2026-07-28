"""Multi-provider LLM adapter for RecruitMate.

Provider failures are raised to the application. A real provider must never
silently fall back to mock output because that makes evaluation traces
misleading.
"""

from __future__ import annotations

import os
from typing import Any

import requests
from dotenv import load_dotenv


load_dotenv()


class ProviderError(RuntimeError):
    """Base error raised by an LLM provider."""


class ProviderConfigurationError(ProviderError):
    """The selected provider is missing required configuration."""


class ProviderQuotaError(ProviderError):
    """The selected provider has exhausted its request quota."""


class BaseLLMProvider:
    model_name = "unknown"
    provider_name = "unknown"
    is_mock = False

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


def _missing_key(value: str | None, placeholder: str) -> bool:
    return not value or value.strip() == placeholder


def _raise_provider_error(provider: str, error: Exception) -> None:
    message = str(error)
    if "RESOURCE_EXHAUSTED" in message or "429" in message:
        raise ProviderQuotaError(
            f"{provider} đã hết quota hoặc đang bị giới hạn tần suất."
        ) from error
    raise ProviderError(f"{provider} gặp lỗi: {message}") from error


class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = (
            model
            or os.getenv("LLM_MODEL")
            or "gemini-3.5-flash"
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if _missing_key(self.api_key, "your_gemini_api_key_here"):
            raise ProviderConfigurationError(
                "Chưa cấu hình GEMINI_API_KEY."
            )

        try:
            from google import genai

            client = genai.Client(api_key=self.api_key)
            contents = (
                f"{system_prompt}\n\n{prompt}"
                if system_prompt
                else prompt
            )
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
            )
            return response.text or ""
        except ProviderError:
            raise
        except Exception as error:
            _raise_provider_error("Gemini", error)


class OpenAIProvider(BaseLLMProvider):
    provider_name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = (
            model
            or os.getenv("LLM_MODEL")
            or "gpt-4o-mini"
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if _missing_key(self.api_key, "your_openai_api_key_here"):
            raise ProviderConfigurationError(
                "Chưa cấu hình OPENAI_API_KEY."
            )

        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)
            messages: list[dict[str, str]] = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt,
                })
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            return response.choices[0].message.content or ""
        except ProviderError:
            raise
        except Exception as error:
            _raise_provider_error("OpenAI", error)


class AnthropicProvider(BaseLLMProvider):
    provider_name = "anthropic"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = (
            model
            or os.getenv("LLM_MODEL")
            or "claude-3-haiku-20240307"
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if _missing_key(
            self.api_key,
            "your_anthropic_api_key_here",
        ):
            raise ProviderConfigurationError(
                "Chưa cấu hình ANTHROPIC_API_KEY."
            )

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs: dict[str, Any] = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except ProviderError:
            raise
        except Exception as error:
            _raise_provider_error("Anthropic", error)


class OpenRouterProvider(BaseLLMProvider):
    provider_name = "openrouter"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = (
            model
            or os.getenv("LLM_MODEL")
            or "google/gemini-3.5-flash"
        )

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if _missing_key(
            self.api_key,
            "your_openrouter_api_key_here",
        ):
            raise ProviderConfigurationError(
                "Chưa cấu hình OPENROUTER_API_KEY."
            )

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
            })
        messages.append({"role": "user", "content": prompt})

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model_name,
                    "messages": messages,
                },
                timeout=30,
            )
            if response.status_code == 429:
                raise ProviderQuotaError(
                    "OpenRouter đã hết quota hoặc đang bị giới hạn."
                )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except ProviderError:
            raise
        except Exception as error:
            _raise_provider_error("OpenRouter", error)


class MockProvider(BaseLLMProvider):
    """Deterministic provider used only when LLM_PROVIDER=mock."""

    provider_name = "mock"
    model_name = "Offline deterministic mock"
    is_mock = True

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()
        is_react = "action input" in system_prompt.lower()

        if not is_react:
            if "câu hỏi phỏng vấn" in text or "backend developer" in text:
                return (
                    "Ba câu hỏi phỏng vấn kỹ thuật:\n"
                    "1. Khi nào nên dùng async/await trong FastAPI?\n"
                    "2. Bạn thiết kế validation và authentication như thế nào?\n"
                    "3. Bạn chẩn đoán và tối ưu một API chậm ra sao?"
                )
            if "tiêu chí" in text and "senior python" in text:
                return (
                    "Ba tiêu chí quan trọng gồm:\n"
                    "1. Kinh nghiệm Python backend và dự án thực tế.\n"
                    "2. Năng lực thiết kế hệ thống và cơ sở dữ liệu.\n"
                    "3. Khả năng review code, xử lý vấn đề và dẫn dắt."
                )
            return (
                "Tôi không có quyền truy cập CV, lịch phỏng vấn hoặc "
                "hệ thống đặt lịch thực tế nên không thể xác nhận yêu "
                "cầu này."
            )

        if "nguyễn văn an" in text:
            if '"tool": "search_candidate_cv"' in text:
                return (
                    "Thought: Đã có dữ liệu CV để trả lời.\n"
                    "Final Answer: Nguyễn Văn An có 3 năm kinh nghiệm; "
                    "kỹ năng chính gồm Python, FastAPI, PostgreSQL, "
                    "Docker, RESTful API, Git và Redis."
                )
            return (
                "Thought: Cần tra cứu CV Nguyễn Văn An.\n"
                "Action: search_candidate_cv\n"
                'Action Input: {"candidate_name": "Nguyễn Văn An"}'
            )

        if "trần thị bích" in text:
            if '"tool": "schedule_interview"' in text:
                return (
                    "Thought: Đã có đủ kết quả sàng lọc và đặt lịch.\n"
                    "Final Answer: Trần Thị Bích phù hợp với vị trí. "
                    "Lịch demo đã được tạo tại SLOT001 với Lê Văn C; "
                    "quyết định tuyển dụng vẫn cần HR xem xét."
                )
            if '"tool": "check_interviewer_schedule"' in text:
                return (
                    "Thought: Có slot trống và người dùng đã yêu cầu "
                    "đặt lịch.\n"
                    "Action: schedule_interview\n"
                    "Action Input: "
                    '{"candidate_name": "Trần Thị Bích", '
                    '"job_title": "Senior Python Developer", '
                    '"interviewer_name": "Lê Văn C", '
                    '"slot_id": "SLOT001", "confirmed": true}'
                )
            if '"tool": "screen_candidate_cv"' in text:
                return (
                    "Thought: Ứng viên phù hợp; cần kiểm tra lịch.\n"
                    "Action: check_interviewer_schedule\n"
                    'Action Input: {"interviewer_name": "Lê Văn C"}'
                )
            return (
                "Thought: Cần sàng lọc hồ sơ trước.\n"
                "Action: screen_candidate_cv\n"
                "Action Input: "
                '{"candidate_name": "Trần Thị Bích", '
                '"job_title": "Senior Python Developer"}'
            )

        if "phạm hoàng nam" in text or "31/02/2026" in text:
            if '"error_code": "invalid_date"' in text:
                return (
                    "Thought: Ngày không hợp lệ nên phải dừng an toàn.\n"
                    "Final Answer: Không thể đặt lịch vì 31/02/2026 "
                    "không tồn tại. Hệ thống không thực hiện thay đổi."
                )
            return (
                "Thought: Cần kiểm tra ngày và lịch trước.\n"
                "Action: check_interviewer_schedule\n"
                "Action Input: "
                '{"interviewer_name": "Trần Văn D", '
                '"start_date": "31/02/2026", '
                '"end_date": "31/02/2026"}'
            )

        if "câu hỏi phỏng vấn" in text or "backend developer" in text:
            return (
                "Thought: Câu hỏi chỉ cần kiến thức chung.\n"
                "Final Answer: Có thể hỏi về async/await, dependency "
                "injection và tối ưu truy vấn trong FastAPI."
            )

        return (
            "Thought: Câu hỏi chỉ cần kiến thức chung.\n"
            "Final Answer: Hãy đánh giá kinh nghiệm Python, năng lực "
            "thiết kế hệ thống và khả năng dẫn dắt kỹ thuật."
        )


def get_llm_provider(
    provider_name: str | None = None,
) -> BaseLLMProvider:
    name = (
        provider_name
        or os.getenv("LLM_PROVIDER")
        or "mock"
    ).lower().strip()

    providers: dict[str, type[BaseLLMProvider]] = {
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "openrouter": OpenRouterProvider,
        "mock": MockProvider,
    }
    provider_class = providers.get(name)
    if provider_class is None:
        raise ProviderConfigurationError(
            f"LLM_PROVIDER '{name}' không hợp lệ."
        )
    return provider_class()
