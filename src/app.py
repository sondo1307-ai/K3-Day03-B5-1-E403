"""
RecruitMate Full Mock App.

Cách chạy:
    python src/app.py baseline
    python src/app.py react
    python src/app.py all
    python src/app.py react 4
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


from mock_data import MOCK_BASELINE_ANSWERS, MOCK_REACT_PLANS
from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider
from tools import (
    TOOL_REGISTRY,
    TOOL_SPECS,
    execute_tool,
    reset_mock_state,
)


LINE = "=" * 78


def load_test_cases() -> list[dict[str, Any]]:
    path = os.path.join(PROJECT_ROOT, "config", "test_cases.json")
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def run_baseline_chatbot(
    user_query: str,
    provider: Any,
) -> str:
    print(f"\n💬 [FULL MOCK BASELINE] {user_query}")
    print("🚫 Tool: không sử dụng")

    answer = provider.generate(
        user_query,
        system_prompt=CHATBOT_BASELINE_PROMPT,
    )

    print(f"🤖 Final Answer:\n{answer}")
    return answer


def run_baseline_on_test_cases(
    tests: list[dict[str, Any]],
    provider: Any,
) -> list[dict[str, Any]]:
    logs = []

    for case in tests:
        print(f"\n{LINE}")
        print(f"🧪 TC#{case['id']} | {case['category']}")
        print(LINE)

        answer = run_baseline_chatbot(case["question"], provider)

        logs.append({
            "id": case["id"],
            "question": case["question"],
            "answer": answer,
        })

    return logs


def _build_final_answer(
    case_id: int,
    trace: list[dict[str, Any]],
) -> str:
    if case_id == 3 and trace:
        observation = trace[-1]["observation"]
        if observation.get("ok"):
            summary = observation["summary"]
            skills = ", ".join(summary["skills"])
            return (
                f"{summary['name']} có "
                f"{summary['years_experience']} năm kinh nghiệm. "
                f"Các kỹ năng chính gồm: {skills}."
            )

    if case_id == 4 and trace:
        last = trace[-1]["observation"]

        if last.get("ok") and "interview" in last:
            interview = last["interview"]
            screening = last["screening_summary"]

            return (
                f"Trần Thị Bích đạt {screening['score']} điểm, "
                f"mức phù hợp {screening['fit_level']}. "
                f"Lịch phỏng vấn đã được tạo với "
                f"{interview['interviewer_name']} tại "
                f"{interview['start_time']}–{interview['end_time']} "
                f"({interview['slot_id']}). "
                "Kết quả sàng lọc vẫn cần HR xem xét."
            )

    if case_id == 5 and trace:
        observation = trace[-1]["observation"]

        if not observation.get("ok"):
            return (
                "Không thể đặt lịch phỏng vấn. "
                f"Lý do: {observation.get('error')}. "
                "Hệ thống không thực hiện thay đổi nào."
            )

    return "[MOCK FINAL ANSWER NOT FOUND]"


def run_mock_react_agent(
    case: dict[str, Any],
) -> dict[str, Any]:
    case_id = int(case["id"])
    question = case["question"]

    print(f"\n🤖 [FULL MOCK REACT] {question}")
    print(
        "🛠️ Tools:",
        ", ".join(sorted(TOOL_REGISTRY)),
    )

    # TC1 và TC2: trả dữ liệu mock trực tiếp, không gọi tool.
    if case_id in (1, 2):
        answer = MOCK_BASELINE_ANSWERS.get(
            question,
            "[MOCK DATA NOT FOUND]",
        )
        print("Thought: Câu hỏi có câu trả lời mock trực tiếp.")
        print(f"Final Answer:\n{answer}")

        return {
            "id": case_id,
            "ok": True,
            "trace": [],
            "final_answer": answer,
        }

    plan = MOCK_REACT_PLANS.get(case_id)
    if not plan:
        return {
            "id": case_id,
            "ok": False,
            "trace": [],
            "final_answer": "[MOCK PLAN NOT FOUND]",
        }

    trace: list[dict[str, Any]] = []

    for iteration, step in enumerate(plan, start=1):
        if iteration > MAX_ITERATIONS:
            observation = {
                "ok": False,
                "error_code": "MAX_ITERATIONS_REACHED",
                "error": "Đã đạt giới hạn số vòng lặp.",
            }
            print(
                "Observation:",
                json.dumps(observation, ensure_ascii=False),
            )
            break

        thought = step["thought"]
        action = step["action"]
        action_input = step["action_input"]

        print(f"\nIteration {iteration}")
        print(f"Thought: {thought}")
        print(f"Action: {action}")
        print(
            "Action Input:",
            json.dumps(action_input, ensure_ascii=False),
        )

        observation = execute_tool(action, action_input)

        print(
            "Observation:",
            json.dumps(
                observation,
                ensure_ascii=False,
                indent=2,
            ),
        )

        trace.append({
            "iteration": iteration,
            "thought": thought,
            "action": action,
            "action_input": action_input,
            "observation": observation,
        })

        # Guardrail: gặp lỗi thì dừng.
        if not observation.get("ok"):
            break

    final_answer = _build_final_answer(case_id, trace)
    print(f"\nFinal Answer:\n{final_answer}")

    return {
        "id": case_id,
        "ok": True,
        "trace": trace,
        "final_answer": final_answer,
    }


def run_react_on_test_cases(
    tests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reset_mock_state()
    logs = []

    for case in tests:
        print(f"\n{LINE}")
        print(f"🧪 TC#{case['id']} | {case['category']}")
        print(LINE)

        logs.append(run_mock_react_agent(case))

    return logs


def select_tests(
    tests: list[dict[str, Any]],
    selected_id: int | None,
) -> list[dict[str, Any]]:
    if selected_id is None:
        return tests

    selected = [
        case for case in tests
        if int(case.get("id", -1)) == selected_id
    ]

    if not selected:
        raise ValueError(
            f"Không tìm thấy Test Case id={selected_id}."
        )

    return selected


def main() -> None:
    print(LINE)
    print("🏫 VINUNI LAB 3 — RECRUITMATE FULL MOCK")
    print("📌 Toàn bộ câu trả lời, dữ liệu và Action đều là mock")
    print(LINE)

    provider = get_llm_provider()
    tests = load_test_cases()

    mode = "all"
    selected_id: int | None = None

    if len(sys.argv) >= 2:
        mode = sys.argv[1].lower()

    if len(sys.argv) >= 3 and sys.argv[2].isdigit():
        selected_id = int(sys.argv[2])

    tests = select_tests(tests, selected_id)

    print(
        f"🔌 Provider: {provider.__class__.__name__} "
        f"({provider.model_name})"
    )
    print(f"✅ Test cases: {len(tests)}")
    print(f"🛠️ Tool Specs: {len(TOOL_SPECS)}")

    if mode not in {"baseline", "react", "all"}:
        print("❌ Mode hợp lệ: baseline, react, all")
        sys.exit(1)

    if mode in {"baseline", "all"}:
        print(f"\n{LINE}")
        print("📍 BASELINE FULL MOCK")
        print(LINE)
        run_baseline_on_test_cases(tests, provider)

    if mode in {"react", "all"}:
        print(f"\n{LINE}")
        print("📍 REACT FULL MOCK")
        print(LINE)
        run_react_on_test_cases(tests)


if __name__ == "__main__":
    main()
