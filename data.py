# data.py
# Default fallback data + CSV loader
# If courses.csv exists in the same folder, it will be loaded automatically.
# Otherwise, the hardcoded defaults below are used.

import os
import csv

# ── Default rooms ─────────────────────────────────────────────────────────────
rooms = ["CS-101", "CS-102", "CS-201", "CS-202", "LH-1", "LH-2"]

# ── Default time slots (Mon–Fri, 4 slots/day) ────────────────────────────────
time_slots = [
    "Mon-08:00", "Mon-10:00", "Mon-12:00", "Mon-14:00",
    "Tue-08:00", "Tue-10:00", "Tue-12:00", "Tue-14:00",
    "Wed-08:00", "Wed-10:00", "Wed-12:00", "Wed-14:00",
    "Thu-08:00", "Thu-10:00", "Thu-12:00", "Thu-14:00",
    "Fri-08:00", "Fri-10:00", "Fri-12:00", "Fri-14:00",
]

# ── Hardcoded fallback courses (used only if courses.csv is missing) ──────────
_default_courses = [
    {"id": "AI",   "name": "Artificial Intelligence",      "teacher": "Sir_Riaz",   "sessions_per_week": 2},
    {"id": "OS",   "name": "Operating Systems",            "teacher": "Sir_Hafiz",  "sessions_per_week": 2},
    {"id": "DB",   "name": "Database Systems",             "teacher": "Sir_Kamran", "sessions_per_week": 3},
    {"id": "SDA",  "name": "Software Design & Arch",       "teacher": "Sir_Ahmed",  "sessions_per_week": 2},
    {"id": "ML",   "name": "Machine Learning",             "teacher": "Sir_Riaz",   "sessions_per_week": 2},
    {"id": "PROB", "name": "Probability & Stats",          "teacher": "Sir_Naveed", "sessions_per_week": 2},
    {"id": "SE",   "name": "Software Engineering",         "teacher": "Sir_Tariq",  "sessions_per_week": 2},
    {"id": "CN",   "name": "Computer Networks",            "teacher": "Sir_Bilal",  "sessions_per_week": 2},
    {"id": "DS",   "name": "Data Structures",              "teacher": "Sir_Usman",  "sessions_per_week": 3},
    {"id": "LA",   "name": "Linear Algebra",               "teacher": "Sir_Naveed", "sessions_per_week": 2},
    {"id": "OOP",  "name": "Object Oriented Programming",  "teacher": "Sir_Kamran", "sessions_per_week": 2},
    {"id": "HCI",  "name": "Human Computer Interaction",   "teacher": "Sir_Tariq",  "sessions_per_week": 1},
]


def load_courses(csv_path=None):
    """Load courses from CSV if it exists, otherwise use hardcoded defaults."""
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "courses.csv")
    if not os.path.exists(csv_path):
        return _default_courses
    courses = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            teacher = row["teacher"].strip().replace(" ", "_")
            courses.append({
                "id":                row["id"].strip(),
                "name":              row["name"].strip(),
                "teacher":           teacher,
                "sessions_per_week": int(row["sessions_per_week"].strip()),
            })
    return courses


courses = load_courses()
