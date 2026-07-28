"""
Test thủ công Role 2 — bám đúng test case Role 1.

Cấu trúc:
    project/
    ├── src/
    │   └── tools.py
    ├── config/
    │   └── test_cases.json
    └── test/
        └── test_tool.py

Chạy từ thư mục gốc:
    python test/test_tool.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.tools import (  # noqa: E402
    TOOL_REGISTRY,
    check_interviewer_schedule,
    execute_tool,
    get_job_requirements,
    reset_mock_state,
    schedule_interview,
    screen_candidate_cv,
    search_candidate_cv,
)


def show(title: str, result: dict) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def assert_ok(result: dict) -> None:
    assert result.get("ok") is True, result


def assert_error(
    result: dict,
    expected_code: str,
) -> None:
    assert result.get("ok") is False, result
    assert result.get("error_code") == expected_code, result


def main() -> None:
    reset_mock_state()

    # ------------------------------------------------------------------------
    # TEST CASE 1 VÀ 2
    # Chỉ cần LLM nên không gọi tool.
    # Role 2 chỉ xác nhận không cần tool mới.
    # ------------------------------------------------------------------------

    expected_tools = {
        "search_candidate_cv",
        "screen_candidate_cv",
        "check_interviewer_schedule",
        "schedule_interview",
    }

    assert expected_tools.issubset(TOOL_REGISTRY)

    print("\nTC1 và TC2: Chatbot path, không cần gọi tool.")

    # ------------------------------------------------------------------------
    # TEST CASE 3
    # Tra cứu Nguyễn Văn An.
    # ------------------------------------------------------------------------

    result = search_candidate_cv("Nguyễn Văn An")
    assert_ok(result)
    assert result["candidate"]["name"] == "Nguyễn Văn An"
    assert result["summary"]["years_experience"] == 3.0
    assert "Python" in result["summary"]["skills"]
    show("TC3. Tra cứu CV Nguyễn Văn An", result)

    # Kiểm tra tìm tên không dấu vẫn hoạt động.
    result = search_candidate_cv("Nguyen Van An")
    assert_ok(result)
    assert result["candidate"]["candidate_id"] == "C001"
    show("TC3B. Tra cứu tên không dấu", result)

    # ------------------------------------------------------------------------
    # TEST CASE 4
    # Đánh giá Trần Thị Bích, kiểm tra lịch Lê Văn C và đặt lịch.
    # ------------------------------------------------------------------------

    result = get_job_requirements("Senior Python Developer")
    assert_ok(result)
    assert result["job"]["job_id"] == "JOB001"
    show("TC4A. Lấy JD Senior Python Developer", result)

    result = screen_candidate_cv(
        "Trần Thị Bích",
        "Senior Python Developer",
    )
    assert_ok(result)
    assert result["score"] == 100.0
    assert result["fit_level"] == "strong_match"
    assert result["recommendation"] == "human_review"
    show("TC4B. Sàng lọc Trần Thị Bích", result)

    result = check_interviewer_schedule(
        "Lê Văn C",
        "2026-08-10",
        "2026-08-12",
    )
    assert_ok(result)
    assert result["count"] == 3
    assert result["slots"][0]["slot_id"] == "SLOT001"
    show("TC4C. Kiểm tra lịch Lê Văn C", result)

    # Guardrail: chưa confirmed thì không đặt.
    result = schedule_interview(
        candidate_name="Trần Thị Bích",
        job_title="Senior Python Developer",
        interviewer_name="Lê Văn C",
        slot_id="SLOT001",
        confirmed=False,
    )
    assert_error(result, "CONFIRMATION_REQUIRED")
    show("TC4D. Chặn đặt lịch khi chưa xác nhận", result)

    # Yêu cầu Role 1 đã ghi rõ "đặt lịch", nên confirmed=True.
    result = schedule_interview(
        candidate_name="Trần Thị Bích",
        job_title="Senior Python Developer",
        interviewer_name="Lê Văn C",
        slot_id="SLOT001",
        confirmed=True,
    )
    assert_ok(result)
    assert result["interview"]["status"] == "scheduled"
    assert result["interview"]["slot_id"] == "SLOT001"
    show("TC4E. Đặt lịch thành công", result)

    # Không được đặt lại slot vừa dùng.
    result = schedule_interview(
        candidate_name="Nguyễn Văn An",
        job_title="Senior Python Developer",
        interviewer_name="Lê Văn C",
        slot_id="SLOT001",
        confirmed=True,
    )
    assert_error(result, "SLOT_NOT_AVAILABLE")
    assert "alternative_slots" in result["details"]
    show("TC4F. Phát hiện xung đột lịch", result)

    # ------------------------------------------------------------------------
    # TEST CASE 5
    # Ứng viên không tồn tại và ngày 31/02/2026 không hợp lệ.
    # ------------------------------------------------------------------------

    result = search_candidate_cv("Phạm Hoàng Nam")
    assert_error(result, "CANDIDATE_NOT_FOUND")
    show("TC5A. Ứng viên không tồn tại", result)

    result = check_interviewer_schedule(
        "Trần Văn D",
        "31/02/2026",
        "31/02/2026",
    )
    assert_error(result, "INVALID_DATE")
    show("TC5B. Ngày 31/02/2026 không hợp lệ", result)

    result = schedule_interview(
        candidate_name="Phạm Hoàng Nam",
        job_title="Senior Python Developer",
        interviewer_name="Trần Văn D",
        slot_id="SLOT005",
        confirmed=True,
    )
    assert_error(result, "CANDIDATE_NOT_FOUND")
    show("TC5C. Không đặt lịch cho ứng viên không tồn tại", result)

    # ------------------------------------------------------------------------
    # TEST TOOL REGISTRY
    # ------------------------------------------------------------------------

    result = execute_tool(
        "search_candidate_cv",
        {
            "candidate_name": "Nguyễn Văn An",
        },
    )
    assert_ok(result)
    show("Registry 1. Gọi tool hợp lệ", result)

    result = execute_tool(
        "delete_candidate",
        {
            "candidate_name": "Nguyễn Văn An",
        },
    )
    assert_error(result, "UNKNOWN_TOOL")
    show("Registry 2. Chặn tool không tồn tại", result)

    result = execute_tool(
        "search_candidate_cv",
        {},
    )
    assert_error(result, "INVALID_TOOL_ARGUMENTS")
    show("Registry 3. Chặn thiếu tham số", result)

    print("\n" + "=" * 80)
    print("TẤT CẢ TEST ROLE 2 THEO TEST CASE ROLE 1 ĐÃ PASS.")
    print("=" * 80)


if __name__ == "__main__":
    main()
