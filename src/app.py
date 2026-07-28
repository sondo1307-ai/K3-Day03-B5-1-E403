"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Developer / Integrator)
Đề tài 9: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn.

File chính ghép nối tất cả các thành phần của nhóm:
    - config/test_cases.json (Role 1)
    - src/tools.py           (Role 2)
    - src/prompts.py         (Role 3)
    - src/providers.py       (Multi-Provider LLM Adapter)

Trạng thái:
    ✅ MỐC 2: run_baseline_chatbot() đã nối hoàn chỉnh.
    ⏳ MỐC 3: run_react_agent() sẽ lắp vòng lặp ReAct.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import TOOL_SPECS, TOOL_REGISTRY, execute_tool
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

LINE = "=" * 70


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")

    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================================
# MỐC 2: BASELINE CHATBOT (Chatbot gốc - KHÔNG có công cụ)
# ============================================================================

def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Chạy Chatbot gốc (Baseline): chỉ có LLM + System Prompt, KHÔNG được gọi Tool.

    Mục đích của Mốc 2 là để cả nhóm thấy rõ hạn chế của Chatbot thuần:
    nó không tra được hồ sơ CV thật, không biết lịch trống của interviewer,
    nên hoặc là từ chối, hoặc là bịa thông tin (ảo giác / hallucination).

    Args:
        user_query: Câu hỏi của người dùng (HR hoặc ứng viên).
        provider:   LLM Provider lấy từ get_llm_provider().

    Returns:
        Chuỗi câu trả lời của Chatbot (để Role 5 dán vào docs/trace_eval.md).
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print("🚫 Công cụ khả dụng: KHÔNG CÓ (baseline chỉ dùng kiến thức sẵn có của LLM)")

    try:
        response = provider.generate(
            user_query,
            system_prompt=CHATBOT_BASELINE_PROMPT,
        )
    except Exception as error:
        # Guardrail: lỗi mạng / lỗi API không được làm sập cả bài demo
        response = f"[APP ERROR]: Không gọi được LLM Provider - {error}"

    if not response or not str(response).strip():
        response = "[APP ERROR]: Provider trả về câu trả lời rỗng."

    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


def run_baseline_on_test_cases(tests: list, provider) -> list:
    """
    Chạy toàn bộ bộ Test Cases của Role 1 qua Chatbot Baseline.

    In ra dạng bảng nhật ký để Role 5 quan sát: câu nào Chatbot trả lời được,
    câu nào Chatbot buộc phải bịa hoặc báo "không có quyền truy cập dữ liệu".
    """
    logs = []

    for case in tests:
        print(f"\n{LINE}")
        print(f"🧪 TEST CASE #{case.get('id')} | {case.get('category')}")
        print(LINE)

        answer = run_baseline_chatbot(case.get("question", ""), provider)

        print(f"\n📌 Kỳ vọng (Role 1): {case.get('expected_behavior')}")

        logs.append({
            "id": case.get("id"),
            "category": case.get("category"),
            "question": case.get("question"),
            "baseline_answer": answer,
        })

    return logs


# ============================================================================
# MỐC 3: REACT AGENT (sẽ lắp vòng lặp Thought -> Action -> Observation)
# ============================================================================

def run_react_agent(user_query: str, provider):
    """
    ⏳ CHƯA LÀM - thuộc phạm vi MỐC 3.

    Ở Mốc 3, hàm này sẽ dựng vòng lặp ReAct đầy đủ:
        1. Gửi REACT_SYSTEM_PROMPT + TOOL_SPECS cho LLM.
        2. Parse dòng "Action: ten_tool[tham_so]" mà LLM sinh ra.
        3. Gọi execute_tool() của Role 2 để lấy Observation.
        4. Lặp lại tối đa MAX_ITERATIONS lần (phanh an toàn Guardrail).
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    print(f"🛠️ Đã sẵn sàng {len(TOOL_SPECS)} tool từ Role 2: "
          f"{', '.join(sorted(TOOL_REGISTRY.keys()))}")
    print(f"🛡️ Guardrail MAX_ITERATIONS = {MAX_ITERATIONS} (từ prompts.py của Role 3)")
    print("⏳ Vòng lặp ReAct sẽ được lắp ở MỐC 3.")


# ============================================================================
# ĐIỂM CHẠY CHÍNH
# ============================================================================

if __name__ == "__main__":
    print(LINE)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("📌 Đề tài 9: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn")
    print(LINE)

    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} Test Cases từ config/test_cases.json (Role 1)")
    print(f"🛠️ Đã nạp {len(TOOL_SPECS)} Tool Specs từ src/tools.py (Role 2)")

    # Cho phép chạy 1 test case cụ thể:  python src/app.py 3
    selected_id = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        selected_id = int(sys.argv[1])
        tests = [case for case in tests if case.get("id") == selected_id]

        if not tests:
            print(f"❌ Không tìm thấy Test Case có id = {selected_id}")
            sys.exit(1)

    print(f"\n{LINE}")
    print("📍 MỐC 2 - DEMO: CHẠY BỘ TEST CASES TRÊN CHATBOT BASELINE")
    print(LINE)

    run_baseline_on_test_cases(tests, provider)

    print(f"\n{LINE}")
    print("👀 QUAN SÁT CHO ROLE 5 (docs/trace_eval.md):")
    print("   - Câu 🟢 Đơn giản: Chatbot trả lời tốt bằng kiến thức chung.")
    print("   - Câu 🟡 Multi-step: Chatbot KHÔNG tra được CV/lịch thật")
    print("     => hoặc từ chối, hoặc bịa dữ liệu (ảo giác).")
    print("   - Câu 🔴 Edge Case: Chatbot không có phanh Guardrail của Tool.")
    print(LINE)
