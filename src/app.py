"""RecruitMate: fair baseline versus ReAct agent comparison."""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

from dotenv import load_dotenv


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


try:
    from .prompts import (
        CHATBOT_BASELINE_PROMPT,
        MAX_ITERATIONS,
        MAX_TOOL_CALLS,
        REACT_SYSTEM_PROMPT,
    )
    from .providers import (
        BaseLLMProvider,
        ProviderError,
        get_llm_provider,
    )
    from .tools import (
        TOOL_REGISTRY,
        TOOL_SPECS,
        execute_tool,
        reset_mock_state,
    )
except ImportError:
    # Cho phép chạy trực tiếp: python src/app.py
    from prompts import (
        CHATBOT_BASELINE_PROMPT,
        MAX_ITERATIONS,
        MAX_TOOL_CALLS,
        REACT_SYSTEM_PROMPT,
    )
    from providers import (
        BaseLLMProvider,
        ProviderError,
        get_llm_provider,
    )
    from tools import (
        TOOL_REGISTRY,
        TOOL_SPECS,
        execute_tool,
        reset_mock_state,
    )


load_dotenv()
LINE = "=" * 78


class ActionParseError(ValueError):
    """The model did not follow the Action protocol."""


def load_test_cases() -> list[dict[str, Any]]:
    path = os.path.join(PROJECT_ROOT, "config", "test_cases.json")
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_action(text: str) -> tuple[str, dict[str, Any]]:
    """Parse ``Action`` and JSON ``Action Input`` from a model response."""
    action_match = re.search(
        r"(?im)^\s*Action:\s*([A-Za-z_]\w*)\s*$",
        text,
    )
    input_match = re.search(
        r"(?im)^\s*Action Input:\s*(\{.*\})\s*$",
        text,
    )
    if not action_match or not input_match:
        raise ActionParseError(
            "Thiếu Action hoặc Action Input dạng JSON object."
        )
    try:
        tool_input = json.loads(input_match.group(1))
    except json.JSONDecodeError as error:
        raise ActionParseError(
            f"Action Input không phải JSON hợp lệ: {error.msg}."
        ) from error
    if not isinstance(tool_input, dict):
        raise ActionParseError(
            "Action Input phải là một JSON object."
        )
    return action_match.group(1), tool_input


def _provider_metadata(provider: BaseLLMProvider) -> dict[str, Any]:
    return {
        "provider": provider.provider_name,
        "model": provider.model_name,
        "is_mock": provider.is_mock,
    }


def run_baseline_chatbot(
    user_query: str,
    provider: BaseLLMProvider,
) -> dict[str, Any]:
    """Run exactly one LLM call and zero tool calls."""
    print(f"\n💬 [CHATBOT BASELINE] {user_query}")
    print("🚫 Tool calls: 0")
    result = {
        **_provider_metadata(provider),
        "status": "success",
        "answer": "",
        "llm_calls": 1,
        "tool_calls": 0,
    }
    try:
        answer = provider.generate(
            user_query,
            system_prompt=CHATBOT_BASELINE_PROMPT,
        )
        if not answer.strip():
            raise ProviderError("Provider trả về nội dung rỗng.")
    except ProviderError as error:
        result.update({
            "status": "provider_error",
            "error": str(error),
            "answer": "",
        })
        print(f"❌ EXECUTION ERROR: {error}")
        return result

    result["answer"] = answer
    print(f"🤖 Final Answer:\n{answer}")
    return result


def _react_system_prompt() -> str:
    return REACT_SYSTEM_PROMPT.format(
        tool_specs=json.dumps(
            TOOL_SPECS,
            ensure_ascii=False,
            indent=2,
        )
    )


def run_react_agent(
    user_query: str,
    provider: BaseLLMProvider,
) -> dict[str, Any]:
    """Run LLM → Action → Tool → Observation until Final Answer."""
    print(f"\n🤖 [REACT AGENT] {user_query}")
    history = f"User Query: {user_query}"
    trace: list[dict[str, Any]] = []
    seen_actions: set[str] = set()
    llm_calls = 0
    tool_calls = 0
    result: dict[str, Any] = {
        **_provider_metadata(provider),
        "status": "guardrail",
        "final_answer": "",
        "llm_calls": 0,
        "tool_calls": 0,
        "iterations": 0,
        "guardrail_triggered": False,
        "trace": trace,
    }

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(
            f"\n--- 🔄 ReAct {iteration}/{MAX_ITERATIONS} "
            f"(tools {tool_calls}/{MAX_TOOL_CALLS}) ---"
        )
        try:
            response = provider.generate(
                history,
                system_prompt=_react_system_prompt(),
            )
            llm_calls += 1
        except ProviderError as error:
            result.update({
                "status": "provider_error",
                "error": str(error),
                "llm_calls": llm_calls + 1,
                "tool_calls": tool_calls,
                "iterations": iteration,
            })
            print(f"❌ EXECUTION ERROR: {error}")
            return result

        print(response)
        if "Final Answer:" in response:
            final_answer = response.split(
                "Final Answer:",
                1,
            )[1].strip()
            result.update({
                "status": "success",
                "final_answer": final_answer,
                "llm_calls": llm_calls,
                "tool_calls": tool_calls,
                "iterations": iteration,
            })
            return result

        try:
            tool_name, tool_input = parse_action(response)
        except ActionParseError as error:
            result.update({
                "status": "parse_error",
                "error": str(error),
                "llm_calls": llm_calls,
                "tool_calls": tool_calls,
                "iterations": iteration,
                "guardrail_triggered": True,
            })
            print(f"🛡️ PARSER GUARDRAIL: {error}")
            return result

        if tool_calls >= MAX_TOOL_CALLS:
            result.update({
                "status": "guardrail",
                "error": "Đã đạt MAX_TOOL_CALLS.",
                "llm_calls": llm_calls,
                "tool_calls": tool_calls,
                "iterations": iteration,
                "guardrail_triggered": True,
            })
            print("🛡️ GUARDRAIL: Đã đạt giới hạn tool calls.")
            return result

        signature = json.dumps(
            [tool_name, tool_input],
            ensure_ascii=False,
            sort_keys=True,
        )
        if signature in seen_actions:
            result.update({
                "status": "guardrail",
                "error": "Agent lặp lại cùng một Action.",
                "llm_calls": llm_calls,
                "tool_calls": tool_calls,
                "iterations": iteration,
                "guardrail_triggered": True,
            })
            print("🛡️ LOOP GUARDRAIL: Action bị lặp.")
            return result
        seen_actions.add(signature)

        observation = execute_tool(tool_name, tool_input)
        tool_calls += 1
        if observation.get("ok") is False:
            result["guardrail_triggered"] = True
        trace_item = {
            "iteration": iteration,
            "thought_action": response,
            "tool": tool_name,
            "tool_input": tool_input,
            "observation": observation,
        }
        trace.append(trace_item)
        print(
            "👁️ Observation:\n"
            + json.dumps(
                observation,
                ensure_ascii=False,
                indent=2,
            )
        )
        history += (
            f"\n\n{response}\nObservation: "
            + json.dumps(
                {
                    "tool": tool_name,
                    "result": observation,
                },
                ensure_ascii=False,
            )
        )

    result.update({
        "status": "guardrail",
        "error": "Đã đạt MAX_ITERATIONS mà chưa có Final Answer.",
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
        "iterations": MAX_ITERATIONS,
        "guardrail_triggered": True,
    })
    print("🛡️ GUARDRAIL: Hết vòng lặp mà chưa có Final Answer.")
    return result


def _parse_cli(
    arguments: list[str],
) -> tuple[str, int | None]:
    mode = "all"
    selected_id: int | None = None
    for argument in arguments:
        normalized = argument.lower()
        if normalized in {"baseline", "react", "all"}:
            mode = normalized
        elif argument.isdigit():
            selected_id = int(argument)
        else:
            raise ValueError(
                "Cú pháp: python src/app.py [baseline|react|all] [id]"
            )
    return mode, selected_id


def main() -> int:
    try:
        mode, selected_id = _parse_cli(sys.argv[1:])
        provider = get_llm_provider()
    except (ValueError, ProviderError) as error:
        print(f"❌ CONFIG ERROR: {error}")
        return 2

    tests = load_test_cases()
    if selected_id is not None:
        tests = [
            case for case in tests
            if int(case["id"]) == selected_id
        ]
        if not tests:
            print(f"❌ Không tìm thấy test #{selected_id}.")
            return 2

    print(LINE)
    print("🏫 VINUNI LAB 3 — CHATBOT VS REACT AGENT")
    print("📌 Chủ đề 9: Sàng lọc hồ sơ và hẹn phỏng vấn")
    print(LINE)
    print(
        f"🔌 Provider thực tế: {provider.provider_name} "
        f"({provider.model_name})"
    )
    print(f"🧪 Mode: {mode}; Test cases: {len(tests)}")
    print(f"🛠️ Tools: {', '.join(sorted(TOOL_REGISTRY))}")
    if provider.is_mock:
        print("⚠️ OFFLINE MOCK — không dùng để chấm năng lực LLM.")

    reset_mock_state()
    summary: list[dict[str, Any]] = []
    provider_failed = False
    for case in tests:
        print(f"\n{LINE}")
        print(f"TEST #{case['id']} | {case['category']}")
        print(f"❓ {case['question']}")
        print(f"📌 Expected: {case['expected_behavior']}")
        print(LINE)

        case_result: dict[str, Any] = {"id": case["id"]}
        if mode in {"baseline", "all"}:
            baseline = run_baseline_chatbot(
                case["question"],
                provider,
            )
            case_result["baseline"] = baseline
            if baseline["status"] == "provider_error":
                summary.append(case_result)
                provider_failed = True
                print("⛔ Dừng suite vì provider không khả dụng.")
                break

        if mode in {"react", "all"}:
            agent = run_react_agent(
                case["question"],
                provider,
            )
            case_result["agent"] = agent
            if agent["status"] == "provider_error":
                summary.append(case_result)
                provider_failed = True
                print("⛔ Dừng suite vì provider không khả dụng.")
                break
        summary.append(case_result)

    print(f"\n{LINE}")
    print("📊 RUN SUMMARY")
    for item in summary:
        labels = []
        if "baseline" in item:
            labels.append(
                "baseline=" + item["baseline"]["status"]
            )
        if "agent" in item:
            agent = item["agent"]
            labels.append(
                "agent="
                f"{agent['status']}"
                f"/llm:{agent['llm_calls']}"
                f"/tools:{agent['tool_calls']}"
                f"/guardrail:{agent['guardrail_triggered']}"
            )
        print(f"- TC#{item['id']}: {', '.join(labels)}")
    print(LINE)
    return 1 if provider_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
