"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo các công cụ (Tools) xử lý cho bài toán Trợ Lý Sàng Lọc Hồ Sơ Tuyển Dụng & Hẹn Phỏng Vấn.
"""

from typing import Any, Dict

# ============================================================================
# 1. BỘ DỮ LIỆU MOCK THỰC TẾ
# ============================================================================

CANDIDATES_DB = {
    "nguyễn văn an": {
        "candidate_id": "C001",
        "name": "Nguyễn Văn An",
        "position": "Backend Developer",
        "experience": "3 năm kinh nghiệm lập trình Python, FastAPI, PostgreSQL, Docker",
        "education": "Cử nhân CNTT - ĐH Bách Khoa",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "RESTful API", "Git", "Redis"],
    },
    "trần thị bích": {
        "candidate_id": "C002",
        "name": "Trần Thị Bích",
        "position": "Senior Python Developer",
        "experience": "5 năm kinh nghiệm Microservices, Kubernetes, Redis, CI/CD",
        "education": "Thạc sĩ Khoa học Máy tính",
        "skills": ["Python", "Microservices", "Kubernetes", "Redis", "CI/CD", "System Design", "Team Lead"],
    },
}

INTERVIEWERS_DB = {
    "lê văn c": {"name": "Lê Văn C", "slots": ["09:00 - 10:00", "14:30 - 15:30"]},
    "trần văn c": {"name": "Trần Văn C", "slots": ["09:00 - 10:00", "14:30 - 15:30"]},
    "nguyễn thị hà": {"name": "Nguyễn Thị Hà", "slots": ["10:00 - 11:00", "15:00 - 16:00"]},
    "trần văn d": {"name": "Trần Văn D", "slots": []},  # Kín lịch cả ngày
}


# ============================================================================
# 2. CÁC HÀM XỬ LÝ TOOL CHÍNH
# ============================================================================

def search_candidate_cv(candidate_name: str) -> str:
    """Tra cứu thông tin chi tiết hồ sơ CV của ứng viên trong hệ thống."""
    if not candidate_name or not isinstance(candidate_name, str):
        return "LỖI: Tên ứng viên không hợp lệ."
    
    clean_name = candidate_name.strip().lower()
    for key, data in CANDIDATES_DB.items():
        if key in clean_name or clean_name in key or data["candidate_id"].lower() == clean_name:
            return (
                f"Ứng viên: {data['name']} (Mã: {data['candidate_id']}) | Vị trí: {data['position']} | "
                f"Kinh nghiệm: {data['experience']} | Học vấn: {data['education']} | Kỹ năng: {', '.join(data['skills'])}."
            )
    
    return f"LỖI: Không tìm thấy hồ sơ của ứng viên '{candidate_name}' trong cơ sở dữ liệu tuyển dụng."


def screen_candidate_cv(candidate_name: str, job_position: str = "Senior Python Developer") -> str:
    """Sàng lọc và đánh giá mức độ phù hợp của ứng viên so với vị trí tuyển dụng."""
    clean_cand = candidate_name.strip().lower() if candidate_name else ""
    
    if "trần thị bích" in clean_cand or "c002" in clean_cand:
        return (
            f"KẾT QUẢ SÀNG LỌC CV:\n"
            f"- Ứng viên: Trần Thị Bích (C002)\n"
            f"- Vị trí đánh giá: {job_position}\n"
            f"- Điểm phù hợp: 95/100 (RẤT PHÙ HỢP)\n"
            f"- Nhận xét: Đáp ứng vượt kỳ vọng về kỹ năng Python, Microservices, Kubernetes và kinh nghiệm Lead team. Đủ điều kiện chuyển sang vòng phỏng vấn chuyên môn."
        )
    elif "nguyễn văn an" in clean_cand or "c001" in clean_cand:
        return (
            f"KẾT QUẢ SÀNG LỌC CV:\n"
            f"- Ứng viên: Nguyễn Văn An (C001)\n"
            f"- Vị trí đánh giá: {job_position}\n"
            f"- Điểm phù hợp: 75/100 (KHÁ PHÙ HỢP)\n"
            f"- Nhận xét: Có nền tảng Python & FastAPI tốt, nhưng còn thiếu kinh nghiệm System Design cho cấp độ Senior."
        )
    else:
        return f"LỖI: Không thể sàng lọc vì không tìm thấy thông tin hồ sơ của ứng viên '{candidate_name}'."


def check_interviewer_schedule(interviewer_name: str, date: str = "15/08/2026") -> str:
    """Tra cứu lịch trống của người phỏng vấn/HR trong một ngày cụ thể."""
    if "31/02" in date or "32/" in date or "/13/" in date:
        return f"LỖI: Ngày '{date}' không hợp lệ (Không tồn tại ngày này trên lịch). Vui lòng kiểm tra lại."
    
    clean_name = interviewer_name.strip().lower() if interviewer_name else ""
    
    if "trần văn d" in clean_name:
        return f"LỊCH LÀM VIỆC: Interviewer '{interviewer_name}' đã KHÔNG CÓ KHUNG GIỜ TRỐNG (Đã kín lịch cả ngày {date})."
    
    for key, data in INTERVIEWERS_DB.items():
        if key in clean_name or clean_name in key:
            slots_str = ", ".join([f"[{s}]" for s in data["slots"]]) if data["slots"] else "Không còn slot"
            return f"LỊCH TRỐNG của Interviewer '{data['name']}' ngày {date}: {slots_str}."
            
    return f"LỊCH TRỐNG của Interviewer '{interviewer_name}' ngày {date}: [09:00 - 10:00], [14:30 - 15:30]."


def schedule_interview(candidate_name: str, interviewer_name: str, date_time: str = "14:30 ngày 15/08/2026") -> str:
    """Đặt lịch hẹn phỏng vấn chính thức giữa ứng viên và người phỏng vấn."""
    if "31/02" in date_time or "32/" in date_time:
        return f"LỖI ĐẶT LỊCH THẤT BẠI: Thời gian '{date_time}' không tồn tại trên lịch thực tế."
        
    clean_cand = candidate_name.strip().lower() if candidate_name else ""
    clean_inter = interviewer_name.strip().lower() if interviewer_name else ""
    
    if "phạm hoàng nam" in clean_cand or "c999" in clean_cand:
        return f"LỖI ĐẶT LỊCH THẤT BẠI: Ứng viên '{candidate_name}' không tồn tại trong hệ thống tuyển dụng."
        
    if "trần văn d" in clean_inter:
        return f"LỖI ĐẶT LỊCH THẤT BẠI: Interviewer '{interviewer_name}' đã kín lịch vào thời gian được yêu cầu."
        
    return (
        f"✅ XÁC NHẬN ĐẶT LỊCH HẸN THÀNH CÔNG:\n"
        f"- Ứng viên: {candidate_name}\n"
        f"- Người phỏng vấn: {interviewer_name}\n"
        f"- Thời gian: {date_time}\n"
        f"- Mã lịch hẹn: INT-2026-8899\n"
        f"- Trạng thái: Đã gửi thông báo đến Email ứng viên và lịch Outlook của Interviewer."
    )


# Các hàm Alias
def get_candidate_profile(candidate_id: str) -> Dict[str, Any]:
    res = search_candidate_cv(candidate_id)
    return {"ok": True, "result": res}

def get_job_requirements(job_id: str) -> Dict[str, Any]:
    return {"ok": True, "result": f"Yêu cầu công việc {job_id}: Thành thạo Python, RESTful API, CSDL."}

def evaluate_candidate(candidate_id: str, job_id: str = "JOB001") -> Dict[str, Any]:
    res = screen_candidate_cv(candidate_id, job_id)
    return {"ok": True, "result": res}

def get_available_slots(interviewer_id: str, start_date: str = "2026-08-03", end_date: str = "2026-08-07") -> Dict[str, Any]:
    res = check_interviewer_schedule(interviewer_id, start_date)
    return {"ok": True, "result": res}


# ============================================================================
# 3. ĐĂNG KÝ TOOL REGISTRY & SPECS
# ============================================================================

AVAILABLE_TOOLS = {
    "search_candidate_cv": search_candidate_cv,
    "screen_candidate_cv": screen_candidate_cv,
    "check_interviewer_schedule": check_interviewer_schedule,
    "schedule_interview": schedule_interview,
    "get_candidate_profile": get_candidate_profile,
    "get_job_requirements": get_job_requirements,
    "evaluate_candidate": evaluate_candidate,
    "get_available_slots": get_available_slots,
}

TOOL_REGISTRY = AVAILABLE_TOOLS

TOOL_SPECS = [
    {
        "name": "search_candidate_cv",
        "description": "Tra cứu hồ sơ ứng viên theo tên hoặc mã.",
        "parameters": {"type": "object", "properties": {"candidate_name": {"type": "string"}}, "required": ["candidate_name"]}
    },
    {
        "name": "screen_candidate_cv",
        "description": "Sàng lọc CV của ứng viên theo vị trí công việc.",
        "parameters": {"type": "object", "properties": {"candidate_name": {"type": "string"}, "job_position": {"type": "string"}}, "required": ["candidate_name"]}
    },
    {
        "name": "check_interviewer_schedule",
        "description": "Tra cứu lịch rảnh của người phỏng vấn.",
        "parameters": {"type": "object", "properties": {"interviewer_name": {"type": "string"}, "date": {"type": "string"}}, "required": ["interviewer_name"]}
    },
    {
        "name": "schedule_interview",
        "description": "Tạo lịch hẹn phỏng vấn chính thức.",
        "parameters": {"type": "object", "properties": {"candidate_name": {"type": "string"}, "interviewer_name": {"type": "string"}, "date_time": {"type": "string"}}, "required": ["candidate_name", "interviewer_name"]}
    }
]

def execute_tool(tool_name: str, tool_input: dict) -> dict:
    if tool_name in TOOL_REGISTRY:
        func = TOOL_REGISTRY[tool_name]
        try:
            res = func(**tool_input) if isinstance(tool_input, dict) else func(tool_input)
            return {"ok": True, "result": res}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": f"Tool '{tool_name}' không tồn tại."}
