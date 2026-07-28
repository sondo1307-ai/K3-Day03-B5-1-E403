"""
Prompts và guardrails.

Trong Full Mock Mode, prompt chỉ dùng để mô tả kiến trúc;
MockProvider không sinh kiến thức mới từ prompt.
"""

CHATBOT_BASELINE_PROMPT = """
Bạn là trợ lý tuyển dụng ở chế độ mock offline.
Chỉ trả nội dung đã có trong mock data.
"""

REACT_SYSTEM_PROMPT = """
Bạn là RecruitMate ở chế độ mock offline.
Action và Action Input được lấy từ MOCK_REACT_PLANS.
Không được tự tạo dữ liệu ngoài mock data.
"""

MAX_ITERATIONS = 5
TIMEOUT_SECONDS = 10
