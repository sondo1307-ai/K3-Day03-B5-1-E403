"""
Kiểm thử thủ công Role 2 — Mốc 2.

Chạy từ thư mục gốc dự án:
    python test/test_tool.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.tools import (  # noqa: E402
    TOOL_REGISTRY,
    TOOL_SPECS,
    check_interviewer_schedule,
    execute_tool,
    get_job_requirements,
    reset_mock_state,
    schedule_interview,
    screen_candidate_cv,
    search_candidate_cv,
)


PASSED = 0


def show(title: str, result: dict) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def pass_test(name: str) -> None:
    global PASSED
    PASSED += 1
    print(f"✅ {PASSED:02d}. {name}")


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

    # 1. Đúng 5 Tool Specs.
    assert len(TOOL_SPECS) == 5
    pass_test("Có đúng 5 Tool Specs")

    # 2. Tên tool khớp Role 1.
    expected_names = {
        "search_candidate_cv",
        "get_job_requirements",
        "screen_candidate_cv",
        "check_interviewer_schedule",
        "schedule_interview",
    }
    actual_names = {spec["name"] for spec in TOOL_SPECS}
    assert actual_names == expected_names
    assert set(TOOL_REGISTRY) == expected_names
    pass_test("Tên tool khớp test case Role 1")

    # 3. TC3: tra cứu Nguyễn Văn An.
    result = search_candidate_cv("Nguyễn Văn An")
    assert_ok(result)
    assert result["candidate"]["name"] == "Nguyễn Văn An"
    assert result["summary"]["years_experience"] == 3.0
    assert "Python" in result["summary"]["skills"]
    pass_test("TC3 tra cứu CV Nguyễn Văn An")
    show("TC3", result)

    # 4. Tìm tên không dấu.
    result = search_candidate_cv("Nguyen Van An")
    assert_ok(result)
    assert result["candidate"]["candidate_id"] == "C001"
    pass_test("Tìm ứng viên bằng tên không dấu")

    # 5. JD đúng.
    result = get_job_requirements("Senior Python Developer")
    assert_ok(result)
    assert result["job"]["job_id"] == "JOB001"
    pass_test("Tra cứu JD Senior Python Developer")

    # 6. JD chưa đầy đủ.
    result = get_job_requirements("Undefined Position")
    assert_error(result, "INCOMPLETE_JOB_DESCRIPTION")
    pass_test("Phát hiện JD chưa đầy đủ")

    # 7. TC4: sàng lọc Trần Thị Bích.
    result = screen_candidate_cv(
        "Trần Thị Bích",
        "Senior Python Developer",
    )
    assert_ok(result)
    assert result["score"] == 100.0
    assert result["fit_level"] == "strong_match"
    assert result["recommendation"] == "human_review"
    pass_test("TC4 sàng lọc Trần Thị Bích")
    show("TC4 - Screening", result)

    # 8. Prompt injection trong CV không làm điểm thành 100.
    result = screen_candidate_cv(
        "Ứng Viên Prompt Injection",
        "Senior Python Developer",
    )
    assert_ok(result)
    assert result["score"] < 100
    assert result["recommendation"] == "human_review"
    pass_test("Không làm theo prompt injection trong CV")

    # 9. TC4: kiểm tra lịch không cần ngày.
    result = check_interviewer_schedule("Lê Văn C")
    assert_ok(result)
    assert result["count"] == 3
    assert result["slots"][0]["slot_id"] == "SLOT001"
    pass_test("Kiểm tra lịch Lê Văn C khi câu hỏi không cho ngày")
    show("TC4 - Available slots", result)

    # 10. Kiểm tra lịch có khoảng ngày.
    result = check_interviewer_schedule(
        "Lê Văn C",
        "2026-08-10",
        "2026-08-10",
    )
    assert_ok(result)
    assert result["count"] == 2
    pass_test("Lọc lịch theo khoảng ngày")

    # 11. TC5: ngày không hợp lệ.
    result = check_interviewer_schedule(
        "Trần Văn D",
        "31/02/2026",
        "31/02/2026",
    )
    assert_error(result, "INVALID_DATE")
    pass_test("TC5 phát hiện ngày 31/02/2026 không hợp lệ")

    # 12. Chưa xác nhận thì không đặt lịch.
    result = schedule_interview(
        candidate_name="Trần Thị Bích",
        job_title="Senior Python Developer",
        interviewer_name="Lê Văn C",
        slot_id="SLOT001",
        confirmed=False,
    )
    assert_error(result, "CONFIRMATION_REQUIRED")
    pass_test("Chặn đặt lịch khi chưa xác nhận")

    # 13. Đặt lịch thành công.
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
    pass_test("Đặt lịch thành công")
    show("TC4 - Scheduled interview", result)

    # 14. Không được đặt lại slot đã bận.
    result = schedule_interview(
        candidate_name="Nguyễn Văn An",
        job_title="Senior Python Developer",
        interviewer_name="Lê Văn C",
        slot_id="SLOT001",
        confirmed=True,
    )
    assert_error(result, "SLOT_NOT_AVAILABLE")
    assert result["details"]["alternative_slots"]
    pass_test("Phát hiện xung đột và trả slot thay thế")

    # 15. TC5: ứng viên không tồn tại.
    result = schedule_interview(
        candidate_name="Phạm Hoàng Nam",
        job_title="Senior Python Developer",
        interviewer_name="Trần Văn D",
        slot_id="SLOT005",
        confirmed=True,
    )
    assert_error(result, "CANDIDATE_NOT_FOUND")
    pass_test("TC5 không đặt lịch cho ứng viên không tồn tại")

    # 16. Tool không tồn tại.
    result = execute_tool(
        "delete_candidate",
        {
            "candidate_name": "Nguyễn Văn An",
        },
    )
    assert_error(result, "UNKNOWN_TOOL")
    pass_test("Chặn tool không tồn tại")

    # 17. Thiếu tham số.
    result = execute_tool(
        "search_candidate_cv",
        {},
    )
    assert_error(result, "INVALID_TOOL_ARGUMENTS")
    pass_test("Bắt lỗi thiếu tham số tool")

    print("\n" + "=" * 78)
    print(f"TẤT CẢ {PASSED} TEST ROLE 2 ĐÃ PASS.")
    print("=" * 78)


if __name__ == "__main__":
    main()
