# visualize.py
# Table display, CSV export, and Matplotlib timetable grid

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors


def build_dataframe(solution, variables_meta):
    """Convert solution dict into a tidy Pandas DataFrame."""
    rows = []
    for var, (timeslot, room) in solution.items():
        course = variables_meta[var]
        day, time = timeslot.split("-", 1)
        rows.append({
            "Session":  var,
            "Course":   course["name"],
            "Code":     course["id"],
            "Teacher":  course["teacher"].replace("_", " "),
            "Day":      day,
            "Time":     time,
            "Room":     room,
        })
    df = pd.DataFrame(rows)
    day_order = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    df["Day"] = pd.Categorical(df["Day"], categories=day_order, ordered=True)
    df = df.sort_values(["Day", "Time"]).reset_index(drop=True)
    return df


def print_table(df):
    """Pretty-print the timetable to console."""
    display_cols = ["Session", "Course", "Teacher", "Day", "Time", "Room"]
    print("\n" + "="*75)
    print("  GENERATED UNIVERSITY TIMETABLE")
    print("="*75)
    print(df[display_cols].to_string(index=False))
    print("="*75 + "\n")


def export_csv(df, path="timetable_output.csv"):
    df.to_csv(path, index=False)
    print(f"[+] Timetable exported to: {path}")


def visualize_grid(solution, variables_meta, time_slots, rooms, save_path="timetable.png"):
    """
    Draw a Room × Time grid where each assigned session is a colored block.
    Rows = time slots, Columns = rooms.
    """
    # Assign a distinct color to each course code
    course_ids = list({variables_meta[v]["id"] for v in variables_meta})
    palette = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
    color_map = {cid: palette[i % len(palette)] for i, cid in enumerate(course_ids)}

    n_slots = len(time_slots)
    n_rooms = len(rooms)

    fig, ax = plt.subplots(figsize=(max(8, n_rooms * 2.5), max(8, n_slots * 0.7)))
    ax.set_xlim(0, n_rooms)
    ax.set_ylim(0, n_slots)
    ax.invert_yaxis()   # top = first time slot

    # Draw grid lines
    for x in range(n_rooms + 1):
        ax.axvline(x, color="grey", linewidth=0.5)
    for y in range(n_slots + 1):
        ax.axhline(y, color="grey", linewidth=0.5)

    # Fill in scheduled sessions
    for var, (timeslot, room) in solution.items():
        course = variables_meta[var]
        r_idx = rooms.index(room)
        t_idx = time_slots.index(timeslot)

        color = color_map[course["id"]]
        rect = mpatches.FancyBboxPatch(
            (r_idx + 0.04, t_idx + 0.04), 0.92, 0.92,
            boxstyle="round,pad=0.04",
            facecolor=color, edgecolor="white", linewidth=1.2, alpha=0.88
        )
        ax.add_patch(rect)
        ax.text(r_idx + 0.5, t_idx + 0.38, course["id"],
                ha="center", va="center", fontsize=9, fontweight="bold", color="white")
        ax.text(r_idx + 0.5, t_idx + 0.70,
                course["teacher"].replace("_", " ").replace("Sir ", ""),
                ha="center", va="center", fontsize=7, color="white", alpha=0.9)

    # Axes labels
    ax.set_xticks([x + 0.5 for x in range(n_rooms)])
    ax.set_xticklabels(rooms, fontsize=10, fontweight="bold")
    ax.set_yticks([y + 0.5 for y in range(n_slots)])
    ax.set_yticklabels(time_slots, fontsize=8)
    ax.xaxis.tick_top()

    # Legend
    legend_patches = [
        mpatches.Patch(facecolor=color_map[cid], label=cid, alpha=0.88)
        for cid in course_ids
    ]
    ax.legend(handles=legend_patches, loc="lower right",
              fontsize=8, title="Courses", title_fontsize=9,
              framealpha=0.9, ncol=2)

    ax.set_title("University Timetable — CSP Backtracking + Forward Checking",
                 fontsize=13, fontweight="bold", pad=18)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    print(f"[+] Timetable grid saved to: {save_path}")
    plt.show()
