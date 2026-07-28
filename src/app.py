"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Developer / Integrator)
Đề tài 9: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn.

File chính ghép nối tất cả các thành phần của nhóm:
    - config/test_cases.json (Role 1)
    - src/tools.py           (Role 2)
    - src/prompts.py         (Role 3)
    - src/providers.py       (Multi-Provider LLM Adapter)
"""

import json
import os
import sys
import re
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
from tools import TOOL_SPECS, TOOL_REGISTRY, AVAILABLE_TOOLS, execute_tool
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


def parse_action(text: str):
    """Trích xuất tên tool và tham số từ dạng Action: tool_name[arg1, arg2]"""
    match = re.search(r"Action:\s*(\w+)\[(.*?)\]", text, re.IGNORECASE)
    if not match:
        return None, []
    tool_name = match.group(1).strip()
    raw_args = match.group(2).strip()
    if not raw_args:
        args = []
    else:
        args = [a.strip(" '\"") for a in raw_args.split(",")]
    return tool_name, args


# ============================================================================
# MỐC 2: BASELINE CHATBOT (Chatbot gốc - KHÔNG có công cụ)
# ============================================================================

def run_baseline_chatbot(user_query: str, provider) -> str:
    """
    Chạy Chatbot gốc (Baseline): chỉ có LLM + System Prompt, KHÔNG được gọi Tool.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print("🚫 Công cụ khả dụng: KHÔNG CÓ (baseline chỉ dùng kiến thức sẵn có của LLM)")

    try:
        response = provider.generate(
            user_query,
            system_prompt=CHATBOT_BASELINE_PROMPT,
        )
    except Exception as error:
        response = f"[APP ERROR]: Không gọi được LLM Provider - {error}"

    if not response or not str(response).strip():
        response = "[APP ERROR]: Provider trả về câu trả lời rỗng."

    print(f"🤖 Chatbot trả lời:\n{response}")
    return response


# ============================================================================
# MỐC 3: REACT AGENT (Vòng lặp Thought -> Action -> Observation + Guardrails)
# ============================================================================

def run_react_agent(user_query: str, provider):
    """
    Chạy vòng lặp ReAct Agent có Guardrails MAX_ITERATIONS.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    history = f"User Query: {user_query}"
    step = 0
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        response = provider.generate(history, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"{response}")
        
        if "Final Answer:" in response:
            break
            
        tool_name, args = parse_action(response)
        if tool_name and tool_name in AVAILABLE_TOOLS:
            tool_func = AVAILABLE_TOOLS[tool_name]
            try:
                obs = tool_func(*args)
            except Exception as e:
                obs = f"LỖI THỰC THI TOOL: {str(e)}"
            print(f"👁️ Observation: {obs}")
            history += f"\n{response}\nObservation: {obs}"
        else:
            if "Action:" in response and not tool_name:
                print(f"👁️ Observation: LỖI: Định dạng Action không hợp lệ hoặc tool không tồn tại.")
                history += f"\n{response}\nObservation: LỖI: Tool không hợp lệ."
            else:
                break
                
    if step >= MAX_ITERATIONS and "Final Answer:" not in response:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


# ============================================================================
# ĐIỂM CHẠY CHÍNH
# ============================================================================

if __name__ == "__main__":
    print(LINE)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("📌 Đề tài 9: Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn")
    print(LINE)

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} Test Cases từ config/test_cases.json (Role 1)")
    print(f"🛠️ Đã nạp {len(TOOL_SPECS)} Tool Specs từ src/tools.py (Role 2)")

    # Cho phép chạy 1 test case cụ thể: python src/app.py 5
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        selected_id = int(sys.argv[1])
        tests = [case for case in tests if case.get("id") == selected_id]

    print(f"\n{LINE}")
    print("📍 DEMO: CHẠY SO SÁNH CHATBOT BASELINE VS REACT AGENT")
    print(LINE)

    for case in tests:
        print(f"\n{LINE}")
        print(f"🧪 TEST CASE #{case.get('id')} | {case.get('category')}")
        print(f"❓ Câu hỏi: {case.get('question')}")
        print(f"📌 Kỳ vọng (Role 1): {case.get('expected_behavior')}")
        print(LINE)

        if "Đơn giản" in case.get("category", ""):
            print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
            run_baseline_chatbot(case.get("question", ""), provider)
        else:
            print("--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
            run_react_agent(case.get("question", ""), provider)

    print(f"\n{LINE}")
    print("👀 QUAN SÁT CHO ROLE 5 (docs/trace_eval.md):")
    print("   - Câu 🟢 Đơn giản: Chatbot trả lời tốt bằng kiến thức chung.")
    print("   - Câu 🟡 Multi-step: ReAct Agent gọi Tool sàng lọc CV/lịch thực tế.")
    print("   - Câu 🔴 Edge Case: ReAct Agent kích hoạt phanh Guardrail ngắt lặp an toàn.")
    print(LINE)
