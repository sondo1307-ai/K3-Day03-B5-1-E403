"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.0-flash"
        self._mock = MockProvider()
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return self._mock.generate(prompt, system_prompt)
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return self._mock.generate(prompt, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.0-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()
        if "nguyễn văn an" in text and ("kinh nghiệm" in text or "tra cứu" in text) and "observation" not in text:
            return "Thought: Cần tra cứu thông tin CV của ứng viên Nguyễn Văn An trong cơ sở dữ liệu tuyển dụng.\nAction: search_candidate_cv['Nguyễn Văn An']"
        elif "nguyễn văn an" in text and "observation" in text:
            return "Thought: Tôi đã có đủ thông tin từ Observation để kết luận.\nFinal Answer: Ứng viên Nguyễn Văn An có 3 năm kinh nghiệm làm việc với Python, FastAPI, PostgreSQL, Docker. Học vấn: Cử nhân CNTT - ĐH Bách Khoa."
        elif "trần thị bích" in text and "observation" not in text and "check_interviewer_schedule" not in text:
            return "Thought: Tôi cần sàng lọc CV ứng viên Trần Thị Bích so với vị trí Senior Python Developer.\nAction: screen_candidate_cv['Trần Thị Bích', 'Senior Python Developer']"
        elif "trần thị bích" in text and "screen_candidate_cv" in text and "check_interviewer_schedule" not in text:
            return "Thought: Ứng viên đạt 95/100 điểm. Tôi cần tiếp tục kiểm tra lịch trống của Interviewer Lê Văn C.\nAction: check_interviewer_schedule['Lê Văn C', '15/08/2026']"
        elif "trần thị bích" in text and "check_interviewer_schedule" in text and "schedule_interview" not in text:
            return "Thought: Interviewer Lê Văn C có lịch trống. Tôi sẽ tiến hành đặt lịch phỏng vấn chính thức.\nAction: schedule_interview['Trần Thị Bích', 'Lê Văn C', '14:30 ngày 15/08/2026']"
        elif "trần thị bích" in text and "schedule_interview" in text:
            return "Thought: Tôi đã có đủ thông tin từ Observation để kết luận.\nFinal Answer: Ứng viên Trần Thị Bích đạt 95/100 điểm phù hợp. Đã xếp lịch phỏng vấn thành công với Interviewer Lê Văn C vào 14:30 ngày 15/08/2026 (Mã lịch: INT-2026-8899)."
        elif "phạm hoàng nam" in text or "31/02" in text:
            if "observation" not in text:
                return "Thought: Tôi cần kiểm tra lịch trống của Interviewer cho ngày 31/02/2026.\nAction: check_interviewer_schedule['Trần Văn D', '31/02/2026']"
            else:
                return "Thought: Công cụ báo lỗi ngày 31/02/2026 không hợp lệ trên lịch. Tôi sẽ dừng lặp và thông báo lỗi lịch sự cho người dùng.\nFinal Answer: Rất tiếc, ngày 31/02/2026 không tồn tại trên lịch thực tế. Vui lòng cung cấp ngày làm việc hợp lệ để tiếp tục đặt lịch hẹn phỏng vấn."
        elif "tiêu chí" in text or "phỏng vấn" in text:
            return "Dưới đây là 3 tiêu chí quan trọng khi đánh giá CV Senior Python Developer:\n1. Kiến thức chuyên sâu về Python, OOP, AsyncIO\n2. Kinh nghiệm thiết kế hệ thống Microservices & CSDL\n3. Kỹ năng tối ưu hiệu năng và CI/CD."
        elif "backend developer" in text or "câu hỏi phỏng vấn" in text:
            return "Dưới đây là 3 câu hỏi phỏng vấn kỹ thuật Backend Developer (Python/FastAPI):\n1. Phân biệt async/await và threading trong FastAPI?\n2. Đã dùng các ORM nào (SQLAlchemy, Tortoise ORM)?\n3. Cách tối ưu truy vấn SQL với PostgreSQL?"
        
        return "Thought: Đã tiếp nhận yêu cầu.\nFinal Answer: Trợ lý tuyển dụng AI RecruitMate đã hoàn tất phản hồi."


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()
