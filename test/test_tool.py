"""
Chạy test thủ công cho src/tools.py.

Cấu trúc:
    project/
    ├── src/
    │   └── tools.py
    └── test/
        └── test_tool.py

Lệnh chạy từ thư mục gốc dự án:
    python test/test_tool.py

Windows CMD:
    python test\test_tool.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.tools import (  # noqa: E402
    evaluate_candidate,
    execute_tool,
    get_available_slots,
    get_candidate_profile,
    get_job_requirements,
    reset_mock_state,
    schedule_interview,
)


def show(title: str, result: dict) -> None:
    """In kết quả test dễ đọc."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def assert_ok(result: dict) -> None:
    """Kiểm tra tool trả kết quả thành công."""
    assert result.get("ok") is True, result


def assert_error(
    result: dict,
    expected_code: str,
) -> None:
    """Kiểm tra tool trả đúng error_code."""
    assert result.get("ok") is False, result
    assert result.get("error_code") == expected_code, result


def main() -> None:
    """Chạy toàn bộ test thủ công."""
    reset_mock_state()

    # ------------------------------------------------------------------------
    # 1. HỒ SƠ ỨNG VIÊN
    # ------------------------------------------------------------------------

    result = get_candidate_profile("C001")
    assert_ok(result)
    assert result["candidate"]["candidate_id"] == "C001"
    show("1. Lấy ứng viên hợp lệ", result)

    result = get_candidate_profile("C999")
    assert_error(result, "CANDIDATE_NOT_FOUND")
    show("2. Ứng viên không tồn tại", result)

    # ------------------------------------------------------------------------
    # 2. JOB DESCRIPTION
    # ------------------------------------------------------------------------

    result = get_job_requirements("JOB001")
    assert_ok(result)
    assert result["job"]["job_id"] == "JOB001"
    show("3. Lấy JD hợp lệ", result)

    result = get_job_requirements("JOB999")
    assert_error(result, "JOB_NOT_FOUND")
    show("4. JD không tồn tại", result)

    result = get_job_requirements("JOB004")
    assert_error(result, "INCOMPLETE_JOB_DESCRIPTION")
    assert "required_skills" in result["details"]["missing_fields"]
    show("5. JD tồn tại nhưng chưa đầy đủ", result)

    # ------------------------------------------------------------------------
    # 3. ĐÁNH GIÁ ỨNG VIÊN
    # ------------------------------------------------------------------------

    result = evaluate_candidate("C001", "JOB001")
    assert_ok(result)
    assert result["recommendation"] == "human_review"
    assert result["score"] == 70.0
    show("6. Đánh giá C001 cho JOB001", result)

    result = evaluate_candidate("C004", "JOB001")
    assert_ok(result)
    assert result["score"] < 100
    assert result["recommendation"] == "human_review"
    show("7. Chống prompt injection trong CV", result)

    # ------------------------------------------------------------------------
    # 4. TÌM LỊCH
    # ------------------------------------------------------------------------

    result = get_available_slots(
        "INT001",
        "2026-08-03",
        "2026-08-07",
    )
    assert_ok(result)
    assert result["count"] == 3
    show("8. Tìm lịch trống", result)

    result = get_available_slots(
        "INT001",
        "2026/08/03",
        "2026-08-07",
    )
    assert_error(result, "INVALID_DATE_FORMAT")
    show("9. Ngày sai định dạng", result)

    result = get_available_slots(
        "INT001",
        "2026-08-08",
        "2026-08-03",
    )
    assert_error(result, "INVALID_DATE_RANGE")
    show("10. Khoảng ngày không hợp lệ", result)

    # ------------------------------------------------------------------------
    # 5. ĐẶT LỊCH VÀ GUARDRAILS
    # ------------------------------------------------------------------------

    result = schedule_interview(
        candidate_id="C001",
        job_id="JOB001",
        interviewer_id="INT001",
        slot_id="SLOT001",
        confirmed=False,
    )
    assert_error(result, "CONFIRMATION_REQUIRED")
    show("11. Chặn đặt lịch khi chưa xác nhận", result)

    result = schedule_interview(
        candidate_id="C001",
        job_id="JOB001",
        interviewer_id="INT001",
        slot_id="SLOT001",
        confirmed=True,
    )
    assert_ok(result)
    assert result["interview"]["slot_id"] == "SLOT001"
    show("12. Đặt lịch sau khi xác nhận", result)

    result = schedule_interview(
        candidate_id="C003",
        job_id="JOB003",
        interviewer_id="INT001",
        slot_id="SLOT001",
        confirmed=True,
    )
    assert_error(result, "SLOT_NOT_AVAILABLE")
    assert "alternative_slots" in result["details"]
    assert len(result["details"]["alternative_slots"]) >= 1
    show("13. Chặn đặt lại slot và gợi ý lịch khác", result)

    result = schedule_interview(
        candidate_id="C001",
        job_id="JOB001",
        interviewer_id="INT002",
        slot_id="SLOT005",
        confirmed=True,
    )
    assert_error(result, "SLOT_NOT_AVAILABLE")
    assert "alternative_slots" in result["details"]
    show("14. Phát hiện xung đột lịch HR", result)

    # ------------------------------------------------------------------------
    # 6. TOOL REGISTRY
    # ------------------------------------------------------------------------

    result = execute_tool(
        "delete_candidate",
        {"candidate_id": "C001"},
    )
    assert_error(result, "UNKNOWN_TOOL")
    show("15. Chặn tool không tồn tại", result)

    result = execute_tool(
        "get_candidate_profile",
        {},
    )
    assert_error(result, "INVALID_TOOL_ARGUMENTS")
    show("16. Chặn thiếu tham số tool", result)

    result = execute_tool(
        "get_candidate_profile",
        "C001",
    )
    assert_error(result, "INVALID_TOOL_INPUT")
    show("17. Chặn tool_input không phải dictionary", result)

    print("\n" + "=" * 80)
    print("TẤT CẢ 17 TEST THỦ CÔNG ĐÃ PASS.")
    print("=" * 80)


if __name__ == "__main__":
    main()
