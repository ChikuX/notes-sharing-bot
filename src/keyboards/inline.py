from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ACADEMIC_STRUCTURE = {
    "BTECH": {
        "semesters": 8,
        "departments": ["ME", "CE", "CSE", "AIML", "ECE", "AGRICULTURE", "APPLIED SCIENCE"]
    },
    "BBA": { "semesters": 6, "departments": None },
    "BCA": { "semesters": 6, "departments": None },
    "MBA": { "semesters": 4, "departments": None },
    "MCA": { "semesters": 4, "departments": None },
    "BHMCT": { "semesters": 8, "departments": None },
    "BSERIT": { "semesters": 6, "departments": None },
    "BSEMLS": { "semesters": 6, "departments": None },
    "BSECCT": { "semesters": 6, "departments": None },
    "BSEOPT": { "semesters": 6, "departments": None },
    "BSEMT": { "semesters": 6, "departments": None },
    "DIPLOMA": {
        "semesters": 6,
        "departments": ["CE", "ME", "CSE"]
    }
}

def get_valid_departments(course_key: str, semester: int) -> list:
    """Return valid departments for a course and semester. Enforces BTECH sem 1/2 rule."""
    course_key = course_key.upper()
    if course_key == "BTECH":
        if semester in [1, 2]:
            return ["APPLIED SCIENCE"]
        else:
            return ["ME", "CE", "CSE", "AIML", "ECE", "AGRICULTURE"]
    
    struct = ACADEMIC_STRUCTURE.get(course_key)
    return struct.get("departments") if struct else None

def needs_department(course_key: str) -> bool:
    """Check if a course requires department selection."""
    struct = ACADEMIC_STRUCTURE.get(course_key.upper())
    return bool(struct and struct.get("departments"))

def get_semester_count(course_key: str) -> int:
    """Return number of semesters for a course."""
    struct = ACADEMIC_STRUCTURE.get(course_key.upper())
    return struct.get("semesters", 6) if struct else 6


# ─── Start Menu ───────────────────────────────────────────────

START_BUTTON = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📤 Upload Notes", callback_data="upload"),
    ],
    [
        InlineKeyboardButton(text="👤 Profile", callback_data="profile"),
        InlineKeyboardButton(text="🌐 Language", callback_data="language"),
    ],
    [
        InlineKeyboardButton(text="📚 Visit Library", url="https://college-resource-hub-one.vercel.app/"),
    ],
    [
        InlineKeyboardButton(text="❓ Help", callback_data="help"),
    ]
])


# ─── Upload Type Selection ────────────────────────────────────

def upload_type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 Notes", callback_data="type_notes"),
            InlineKeyboardButton(text="📝 PYQs", callback_data="type_pyqs"),
        ]
    ])


# ─── Language ─────────────────────────────────────────────────

def language_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="English", callback_data="lang_en"),
            InlineKeyboardButton(text="हिंदी", callback_data="lang_hi"),
            InlineKeyboardButton(text="ਪੰਜਾਬੀ", callback_data="lang_pu"),
        ]
    ])


# ─── Profile choice (upload flow) ────────────────────────────

def profile_choice_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Yes", callback_data="use_profile"),
            InlineKeyboardButton(text="❌ No", callback_data="change_profile"),
        ]
    ])


# ─── Confirm / Cancel ────────────────────────────────────────

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data="confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel"),
        ]
    ])


# ─── Profile confirm (confirm / re-enter) ────────────────────

def profile_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data="profile_confirm"),
            InlineKeyboardButton(text="🔄 Re-enter", callback_data="profile_reenter"),
        ]
    ])


# ─── Profile / Back (upload pre-check) ───────────────────────

def profile_or_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👤 Profile", callback_data="profile"),
            InlineKeyboardButton(text="🔙 Back", callback_data="back_home"),
        ]
    ])


def back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]
    ])


# ─── Profile View ──────────────────────────────────────────

def profile_view_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Edit Profile", callback_data="edit_profile")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]
    ])


# ─── Course selection ─────────────────────────────────────────

def course_kb():
    buttons = []
    row = []
    for key in ACADEMIC_STRUCTURE.keys():
        row.append(InlineKeyboardButton(text=key, callback_data=f"course_{key}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Department selection ─────────────────────────────────────

def department_kb(course_key: str, semester: int):
    buttons = []
    row = []

    valid_depts = get_valid_departments(course_key, semester) or []

    for dept in valid_depts:
        row.append(InlineKeyboardButton(text=dept, callback_data=f"dept_{dept}"))
        if len(row) == 2:  # using 2 per row for better fit
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Semester selection ───────────────────────────────────────

def semester_kb(course_key: str):
    count = get_semester_count(course_key)
    buttons = []
    row = []
    for i in range(1, count + 1):
        row.append(InlineKeyboardButton(text=f"Sem {i}", callback_data=f"sem_{i}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Admin approval ──────────────────────────────────────────

def approval_btn(note_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{note_id}"),
            InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{note_id}"),
        ]
    ])